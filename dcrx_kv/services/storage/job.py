import asyncio
import functools
import os
import psutil
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from fastapi import UploadFile
from fs.memoryfs import MemoryFS
from fs.errors import (
    ResourceReadOnly,
    ResourceLocked,
    ResourceError,
    ResourceNotFound
)
from typing import Union, Optional
from .connection import StorageConnection
from .models import (
    Blob,
    JobMetadata,
    PathNotFoundException
)
from .status import JobStatus


class Job:

    def __init__(
        self,
        blob: Blob,
        connection: StorageConnection,
        workers: int=psutil.cpu_count()
    ) -> None:
        self.loop = asyncio.get_event_loop()

        self.waiter: Union[asyncio.Future, None] = None
        self._executor = ThreadPoolExecutor(
            max_workers=workers
        )
        self._connection = connection
        self.job_start_time = time.monotonic()
        
        self.filesystem: Union[MemoryFS, None] = None

        job_id = uuid.uuid4()
        self.metadata = JobMetadata(
            id=job_id,
            key=blob.key,
            namespace=blob.namespace,
            content_type=blob.content_type,
            filename=blob.filename,
            path=blob.path,
            operation_type=blob.operation_type,
            backup_type=blob.backup_type,
            encoding=blob.encoding,
            context=f'Job {str(job_id)} creating',
            status=JobStatus.CREATING.value
        )

        self.shutdown = False

    @property
    def path(self):
        return os.path.join( 
            self.metadata.namespace,
            self.metadata.key
        )
    
    async def run(self, 
        filesystem: MemoryFS,
        data: Optional[UploadFile]=None
    ) -> Union[Blob, PathNotFoundException]:
        
        self.filesystem = filesystem

        path_exists = await self.loop.run_in_executor(
            self._executor,
            functools.partial(      
                self.filesystem.exists,
                self.path
            )
        )

        if self.metadata.operation_type != "upload" and path_exists is False:
            return PathNotFoundException(
                namespace=self.metadata.namespace,
                key=self.metadata.key,
                message=f'Blob - {self.metadata.path} - not found.'
            )

        
        if self.metadata.operation_type == 'upload':
            result = await self.upload(data)

        elif self.metadata.operation_type == "delete":
            result = await self.delete()
            
        else:
            result = await self.download()
        
        await self.close()

        return result
    
    async def create(self) -> JobMetadata:

        try:

            result = await self._connection.create([
                self.metadata
            ])

            if result.error:
                result = await self._connection.update([
                    self.metadata
                ], filters={
                    'path': self.metadata.path
                })

            return self.metadata

        except Exception as create_error:
            return JobMetadata(
                id=self.metadata.id,
                key=self.metadata.key,
                namespace=self.metadata.namespace,
                filename=self.metadata.filename,
                path=self.metadata.path,
                content_type=self.metadata.content_type,
                operation_type=self.metadata.operation_type,
                backup_type=self.metadata.backup_type,
                encoding=self.metadata.encoding,
                error=str(create_error),
                context=f'Job {str(self.metadata.id)} failed to create',
                status=JobStatus.FAILED.value
            )
            
    async def download(self) -> Blob:

        self.metadata = JobMetadata(
            id=self.metadata.id,
            key=self.metadata.key,
            namespace=self.metadata.namespace,
            filename=self.metadata.filename,
            path=self.metadata.path,
            content_type=self.metadata.content_type,
            operation_type=self.metadata.operation_type,
            backup_type=self.metadata.backup_type,
            encoding=self.metadata.encoding,
            context=f'Job {str(self.metadata.id)} starting read',
            status=JobStatus.READING.value
        )

        await self._connection.update([
            self.metadata
        ], filters={
            'path': self.metadata.path
        })

        result: Union[bytes, None] = None

        try:
            
            result = await self.loop.run_in_executor(
                self._executor,
                functools.partial(
                    self.filesystem.readbytes,
                    self.path
                )
            )

            self.metadata = JobMetadata(
                id=self.metadata.id,
                key=self.metadata.key,
                namespace=self.metadata.namespace,
                filename=self.metadata.filename,
                path=self.metadata.path,
                content_type=self.metadata.content_type,
                operation_type=self.metadata.operation_type,
                backup_type=self.metadata.backup_type,
                encoding=self.metadata.encoding,
                context=f'Job {str(self.metadata.id)} read complete',
                status=JobStatus.DONE.value
            )

            await self._connection.update([
                self.metadata
            ], filters={
                'path': self.metadata.path
            })

        except (
            ResourceReadOnly,
            ResourceLocked,
            ResourceError,
            ResourceNotFound
        ) as download_error:
            self.metadata = JobMetadata(
                id=self.metadata.id,
                key=self.metadata.key,
                namespace=self.metadata.namespace,
                filename=self.metadata.filename,
                path=self.metadata.path,
                content_type=self.metadata.content_type,
                operation_type=self.metadata.operation_type,
                backup_type=self.metadata.backup_type,
                encoding=self.metadata.encoding,
                error=str(download_error),
                context=f'Job {str(self.metadata.id)} download failed',
                status=JobStatus.FAILED.value
            )

            await self._connection.update([
                self.metadata
            ], filters={
                 'path': self.metadata.path
            })

            return Blob(
                key=self.metadata.key,
                namespace=self.metadata.namespace,
                filename=self.metadata.filename,
                path=self.metadata.path,
                content_type=self.metadata.content_type,
                operation_type=self.metadata.operation_type,
                data=result,
                error=self.metadata.error,
                backup_type=self.metadata.backup_type,
                encoding=self.metadata.encoding
            )
        
        await self._connection.update([
            self.metadata
        ], filters={
             'path': self.metadata.path
        })

        return Blob(
            key=self.metadata.key,
            namespace=self.metadata.namespace,
            filename=self.metadata.filename,
            path=self.metadata.path,
            content_type=self.metadata.content_type,
            operation_type=self.metadata.operation_type,
            data=result,
            backup_type=self.metadata.backup_type,
            encoding=self.metadata.encoding
        )

    async def upload(
        self, 
        data: bytes
    ) -> Blob:
        
        self.metadata = JobMetadata(
            id=self.metadata.id,
            key=self.metadata.key,
            namespace=self.metadata.namespace,
            filename=self.metadata.filename,
            path=self.metadata.path,
            content_type=self.metadata.content_type,
            operation_type=self.metadata.operation_type,
            backup_type=self.metadata.backup_type,
            encoding=self.metadata.encoding,
            context=f'Job {str(self.metadata.id)} starting upload',
            status=JobStatus.READING.value
        )

        await self._connection.update([
            self.metadata
        ], filters={
             'path': self.metadata.path
        })

        try:

            namespace_exists = await self.loop.run_in_executor(
                self._executor,
                functools.partial(
                    self.filesystem.exists,
                    self.metadata.namespace
                )
            )

            if namespace_exists is False:
                await self.loop.run_in_executor(
                    self._executor,
                    functools.partial(
                        self.filesystem.makedirs,
                        self.metadata.namespace
                    )
                )

            await self.loop.run_in_executor(
                self._executor,
                functools.partial(
                    self.filesystem.writebytes,
                    self.path,
                    data
                )
            )

            self.metadata = JobMetadata(
                id=self.metadata.id,
                key=self.metadata.key,
                namespace=self.metadata.namespace,
                filename=self.metadata.filename,
                path=self.metadata.path,
                content_type=self.metadata.content_type,
                operation_type=self.metadata.operation_type,
                backup_type=self.metadata.backup_type,
                encoding=self.metadata.encoding,
                context=f'Job {str(self.metadata.id)} upload complete',
                status=JobStatus.DONE.value
            )

            await self._connection.update([
                self.metadata
            ], filters={
                 'path': self.metadata.path
            })

        except (
            ResourceReadOnly,
            ResourceLocked,
            ResourceError,
            ResourceNotFound
        ) as upload_error:
            self.metadata = JobMetadata(
                id=self.metadata.id,
                key=self.metadata.key,
                namespace=self.metadata.namespace,
                filename=self.metadata.filename,
                path=self.metadata.path,
                content_type=self.metadata.content_type,
                operation_type=self.metadata.operation_type,
                backup_type=self.metadata.backup_type,
                encoding=self.metadata.encoding,
                error=str(upload_error),
                context=f'Job {str(self.metadata.id)} upload failed',
                status=JobStatus.FAILED.value,
            )

            await self._connection.update([
                self.metadata
            ], filters={
                 'path': self.metadata.path
            })

            return Blob(
                key=self.metadata.key,
                namespace=self.metadata.namespace,
                filename=self.metadata.filename,
                path=self.metadata.path,
                content_type=self.metadata.content_type,
                operation_type=self.metadata.operation_type,
                error=self.metadata.error,
                backup_type=self.metadata.backup_type,
                encoding=self.metadata.encoding,
            )
        
        await self._connection.update([
            self.metadata
        ], filters={
             'path': self.metadata.path
        })

        return Blob(
            key=self.metadata.key,
            namespace=self.metadata.namespace,
            filename=self.metadata.filename,
            path=self.metadata.path,
            content_type=self.metadata.content_type,
            operation_type=self.metadata.operation_type,
            encoding=self.metadata.encoding,
            backup_type=self.metadata.backup_type,
        )
    
    async def delete(self) -> Blob:
        
        self.metadata = JobMetadata(
            id=self.metadata.id,
            key=self.metadata.key,
            namespace=self.metadata.namespace,
            filename=self.metadata.filename,
            path=self.metadata.path,
            content_type=self.metadata.content_type,
            operation_type=self.metadata.operation_type,
            backup_type=self.metadata.backup_type,
            encoding=self.metadata.encoding,
            context=f'Job {str(self.metadata.id)} starting deletion',
            status=JobStatus.DELETING.value
        )

        await self._connection.update([
            self.metadata
        ], filters={
             'path': self.metadata.path
        })

        try:

            await self.loop.run_in_executor(
                self._executor,
                functools.partial(
                    self.filesystem.remove,
                    self.path
                )
            )

            self.metadata = JobMetadata(
                id=self.metadata.id,
                key=self.metadata.key,
                namespace=self.metadata.namespace,
                filename=self.metadata.filename,
                path=self.metadata.path,
                content_type=self.metadata.content_type,
                operation_type=self.metadata.operation_type,
                backup_type=self.metadata.backup_type,
                encoding=self.metadata.encoding,
                context=f'Job {str(self.metadata.id)} deletion complete',
                status=JobStatus.DONE.value
            )

            await self._connection.update([
                self.metadata
            ], filters={
                 'path': self.metadata.path
            })

        except (
            ResourceReadOnly,
            ResourceLocked,
            ResourceError,
            ResourceNotFound
        ) as download_error:
            self.metadata = JobMetadata(
                id=self.metadata.id,
                key=self.metadata.key,
                filename=self.metadata.filename,
                path=self.metadata.path,
                content_type=self.metadata.content_type,
                namespace=self.metadata.namespace,
                operation_type=self.metadata.operation_type,
                backup_type=self.metadata.backup_type,
                encoding=self.metadata.encoding,
                error=str(download_error),
                context=f'Job {str(self.metadata.id)} deletion failed',
                status=JobStatus.FAILED.value,
            )

            await self._connection.update([
                self.metadata
            ], filters={
                 'path': self.metadata.path
            })

            return Blob(
                key=self.metadata.key,
                namespace=self.metadata.namespace,
                filename=self.metadata.filename,
                path=self.metadata.path,
                content_type=self.metadata.content_type,
                operation_type=self.metadata.operation_type,
                error=self.metadata.error,
                backup_type=self.metadata.backup_type,
                encoding=self.metadata.encoding,
            )
        
        await self._connection.update([
            self.metadata
        ], filters={
             'path': self.metadata.path
        })

        return Blob(
            key=self.metadata.key,
            namespace=self.metadata.namespace,
            filename=self.metadata.filename,
            path=self.metadata.path,
            content_type=self.metadata.content_type,
            operation_type=self.metadata.operation_type,
            encoding=self.metadata.encoding,
            backup_type=self.metadata.backup_type,
        )
    
    async def cancel(self):
        self.metadata = JobMetadata(
            id=self.metadata.id,
            key=self.metadata.key,
            namespace=self.metadata.namespace,
            filename=self.metadata.filename,
            path=self.metadata.path,
            content_type=self.metadata.content_type,
            operation_type=self.metadata.operation_type,
            backup_type=self.metadata.backup_type,
            encoding=self.metadata.encoding,
            context=f'Job {str(self.metadata.id)} cancelled',
            status=JobStatus.CANCELLED.value,
        )

        await self._connection.update([
            self.metadata
        ], filters={
             'path': self.metadata.path
        })
    
    async def close(self):
        self._executor.shutdown(cancel_futures=True)
        
        