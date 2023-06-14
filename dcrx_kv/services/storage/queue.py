import asyncio
import functools
import os
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dcrx_kv.database.models import DatabaseTransactionResult
from dcrx_kv.env import Env
from dcrx_kv.env.time_parser import TimeParser
from fs.errors import (
    ResourceNotFound, 
    ResourceReadOnly
)
from fs.memoryfs import MemoryFS
from fastapi import UploadFile
from typing import (
    Dict, 
    Union, 
    List
)
from .models import (
    Blob,
    BlobMetadataNotFoundException,
    JobMetadata,
    ServerLimitException
)

from .connection import StorageConnection
from .job import Job


class JobQueue:

    def __init__(
        self,
        env: Env,
        connection: StorageConnection
    ) -> None:
        self.pool_size = env.DCRX_KV_STORAGE_WORKERS

        self._filesystem = MemoryFS()

        self._connection = connection
        self._jobs: Dict[uuid.UUID, Job] = {}
        self._job_metadata: Dict[str, JobMetadata] = {}
        self._active: Dict[uuid.UUID, asyncio.Task] = {}

        self.max_jobs = env.DCRX_KV_STORAGE_POOL_SIZE
        self.max_pending_jobs = env.DCRX_KV_STORAGE_MAX_PENDING
        self.max_job_workers = env.DCRX_KV_STORAGE_WORKERS

        self.active_jobs_count = 0
        self.pending_jobs_count = 0
        self.running_jobs = asyncio.Queue(maxsize=self.max_jobs)
        self.pending_jobs = asyncio.Queue(maxsize=self.max_pending_jobs)

        self.completed: List[asyncio.Task] = []

        self._executor = ThreadPoolExecutor(max_workers=env.DCRX_KV_STORAGE_WORKERS)

        self._cleanup_task: Union[asyncio.Task, None] = None
        self._job_max_age = TimeParser(env.DCRX_KV_STORAGE_BLOB_MAX_AGE).time
        self._job_prune_interval = TimeParser(env.DCRX_KV_STORAGE_PRUNE_INTERVAL).time
        self._run_cleanup = True

        self.loop = asyncio.get_event_loop()

    async def start(self):
        self._cleanup_task = asyncio.create_task(
            self._monitor_jobs()
        )

    async def _monitor_jobs(self):
        while self._run_cleanup:

            await self.loop.run_in_executor(
                self._executor,
                functools.partial(
                    subprocess.run,
                    [
                        "docker",
                        "system",
                        "prune",
                        "-f"
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            )

            queue_jobs = dict(self._jobs)

            pruneable_statuses = ['DONE', 'CANCELLED', 'FAILED']
            
            for job_id, job in queue_jobs.items():
                
                job_elapsed = time.monotonic() - job.job_start_time
                job_is_pruneable = job.metadata.status in pruneable_statuses

                if job.metadata.status in pruneable_statuses:
                    self.completed.append(
                        asyncio.create_task(
                            job.close()
                        )
                    )

                if job_is_pruneable and job_elapsed > self._job_max_age:

                    blob_exists = await self.loop.run_in_executor(
                        self._executor,
                        self._filesystem.exists,
                        job.path
                    )

                    if blob_exists:
                        try:
                            await self.loop.run_in_executor(
                                self._executor,
                                self._filesystem.remove,
                                job.path
                            )

                        except (ResourceReadOnly, ResourceNotFound,):
                            pass

                    del self._jobs[job_id]
            
            for _ in range(self.active_jobs_count):
                job: Job = await self.running_jobs.get()
                job_is_pruneable = job.metadata.status in pruneable_statuses

                if job_is_pruneable is False:
                    await self.running_jobs.put(job)

                elif self.pending_jobs_count > 0:
                    await self.running_jobs.put(
                        await self.pending_jobs.get()
                    )

                    self.active_jobs_count = self.running_jobs.qsize()
                    self.pending_jobs_count = self.pending_jobs.qsize()

            for _ in range(self.pending_jobs_count):
                job: Job = await self.pending_jobs.get()
                job_is_pruneable = job.metadata.status in pruneable_statuses

                if job_is_pruneable is False:
                    await self.pending_jobs.put(job)

            self.pending_jobs_count = self.pending_jobs.qsize()


            self.active_jobs_count = self.running_jobs.qsize()
            
            completed_tasks = list(self.completed)
            for completed_task in completed_tasks:
                if completed_task.done():
                    self.completed.remove(completed_task)
            
            await asyncio.sleep(self._job_prune_interval)

    async def upload(
        self, 
        blob: Blob,
        data: UploadFile
    ) -> JobMetadata:
        
        job = Job(
            blob,
            self._connection,
            workers=self.max_job_workers
        )

        result = await job.create()
        if result.error:
            return result

        if self.active_jobs_count >= self.max_jobs and self.pending_jobs_count < self.max_pending_jobs:
            job.waiter = asyncio.Future()
            await self.pending_jobs.put(job)
            self.pending_jobs_count = self.pending_jobs.qsize()

        elif self.active_jobs_count >= self.max_jobs:
            return ServerLimitException(
                message='Pending jobs quota reached. Please try again later.',
                limit=self.max_pending_jobs,
                current=self.pending_jobs_count
            )
        
        else:
            await self.running_jobs.put(job)
            self.active_jobs_count = self.running_jobs.qsize()

        upload_data = await data.read()
        
        self._active[job.metadata.id] = asyncio.create_task(
            job.run(
                self._filesystem,
                data=upload_data
            )
    
        )

        self._jobs[job.metadata.id] = job
        self._job_metadata[job.path] = job.metadata

        return job.metadata
    
    async def download(
        self,
        blob: Blob
    ):
        
        job = Job(
            blob,
            self._connection,
            workers=self.max_job_workers
        )

        return await job.run(self._filesystem)
    
    async def get_job_metadata(
        self,
        namespace: str,
        key: str
    ) -> Union[JobMetadata, BlobMetadataNotFoundException]:
        path_key = os.path.join(namespace, key)
        metadata = self._job_metadata.get(path_key)
        if metadata is None:

            metadata_set = await self._connection.select(
                filters={
                    'path': path_key
                }
            )

            if metadata_set.data is None or len(metadata_set.data) < 1:
                return BlobMetadataNotFoundException(
                    namespace=namespace,
                    key=key,
                    message=f'Blob - {path_key} - not found.'
                )
            
            metadata = metadata_set.data.pop()

        return JobMetadata(
            id=metadata.id,
            key=metadata.key,
            namespace=metadata.namespace,
            filename=metadata.filename,
            path=metadata.path,
            content_type=metadata.content_type,
            operation_type=metadata.operation_type,
            encoding=metadata.encoding,
            context=metadata.content_type,
            status=metadata.status,
            error=metadata.error
        )
        

    async def get_blob_metadata(
        self, 
        namespace: str,
        key: str,
        operation_type: str="list"
    ) -> Union[Blob, BlobMetadataNotFoundException]:
        
        metadata = await self.get_job_metadata(
            namespace,
            key
        )

        return Blob(
            key=key,
            namespace=namespace,
            filename=metadata.filename,
            path=metadata.path,
            content_type=metadata.content_type,
            operation_type=operation_type,
            encoding=metadata.encoding,
            backup_type=metadata.backup_type
        )
    
    async def cancel(self, job_id: uuid.UUID) -> Union[Job, BlobMetadataNotFoundException]:

        active_task = self._active.get(job_id)
        if active_task and active_task.done() is False:
            active_task.cancel()

        cancellable_states = [
            'CREATINNG',
            'CREATED', 
            'WRITING',
            'READING'
        ]

        cancelled_job = self._jobs.get(job_id)

        if cancelled_job is None:
            return BlobMetadataNotFoundException(
                job_id=job_id,
                message=f'Job - {job_id} - not found or is not active.'
            )

        job_is_cancellable = cancelled_job.metadata.status in cancellable_states

        if job_is_cancellable is False:
            return BlobMetadataNotFoundException(
                job_id=job_id,
                message=f'Job - {job_id} - not found or is not active.'
            )
        
        await cancelled_job.cancel()
        
        self._jobs[job_id] = cancelled_job

        return cancelled_job
    
    async def close(self):

        await self.loop.run_in_executor(
            self._executor,
            self._filesystem.close
        )

        self._run_cleanup = False
        await self._cleanup_task

        cancel_jobs: List[Job] = []
        for _ in range(self.pending_jobs_count):
            job: Job = await self.pending_jobs.get()
            if job.shutdown is False:
                cancel_jobs.append(job)

            await asyncio.gather(*[
                asyncio.create_task(
                    job.close()
                ) for job in cancel_jobs
            ])

        cancel_jobs: List[Job] = []
        for _ in range(self.active_jobs_count):
            job: Job = await self.running_jobs.get()
            if job.shutdown is False:
                cancel_jobs.append(job)
            
            await asyncio.gather(*[
                asyncio.create_task(
                    job.close()
                ) for job in cancel_jobs
            ])
        
        for job_task in self._active.values():
            if not job_task.done():
                job_task.cancel()

        self._executor.shutdown()