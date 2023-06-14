import os
from dcrx_kv.context.manager import context, ContextType
from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from fastapi.responses import Response
from typing import Literal, Annotated
from .models import (
    Blob,
    BlobMetadataNotFoundException,
    JobMetadata
)
from .context import StorageServiceContext


storage_router = APIRouter()


@storage_router.put(
    '/store/put/{namespace}/{key}',
    responses={
        400: {
            "model": JobMetadata
        }
    }
)
async def upload_blob(
    namespace: str,
    key: str,
    blob: Annotated[UploadFile, File()],
    persist: Literal["aws", "azure", "gcs", "disk"]="disk",
    encoding: str='utf-8',
    mime_type: str=Header(default="application/octet-stream")
) -> JobMetadata:
    storage_service_context: StorageServiceContext = context.get(ContextType.STORAGE_SERVICE)

    new_blob = Blob(
        key=key,
        namespace=namespace,
        filename=blob.filename,
        path=os.path.join(
            namespace,
            key
        ),
        content_type=mime_type,
        operation_type="upload",
        backup_type=persist,
        encoding=encoding
    )

    result = await storage_service_context.queue.upload(
        new_blob,
        blob
    )

    if result.error:
        raise HTTPException(
            400,
            detail=result.dict()
        )
    
    return result


@storage_router.get(
    '/store/get/{namespace}/{key}',
    responses={
        404: {
            "model": BlobMetadataNotFoundException
        }
    }
)
async def download_blob(
    namespace: str,
    key: str
) -> Response:
    storage_service_context: StorageServiceContext = context.get(ContextType.STORAGE_SERVICE)

    blob = await storage_service_context.queue.get_blob_metadata(
        namespace,
        key,
        operation_type="upload"
    )

    if isinstance(blob, BlobMetadataNotFoundException):
        raise HTTPException(404, detail={
            "namespace": namespace,
            'key': key,
            "message": blob.message
        })
    
    result = await storage_service_context.queue.download(blob)

    return Response(
        content=result.data,
        headers={
            'Content-Disposition': f'attachment; filename="{result.filename}"'
        },
        media_type=result.content_type
    )

@storage_router.get(
    '/store/metadata/get/{namespace}/{key}',
    responses={
        404: {
            "model": BlobMetadataNotFoundException
        }
    }
)
async def get_metadata(
    namespace: str,
    key: str    
) -> JobMetadata:

    storage_service_context: StorageServiceContext = context.get(ContextType.STORAGE_SERVICE)

    metadata = await storage_service_context.queue.get_job_metadata(
        namespace,
        key
    )

    if isinstance(metadata, BlobMetadataNotFoundException):
        raise HTTPException(404, detail={
            "namespace": namespace,
            'key': key,
            "message": metadata.message
        })

    return metadata