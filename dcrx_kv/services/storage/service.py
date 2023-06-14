import os
from dcrx_kv.context.manager import context, ContextType
from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from fastapi.responses import Response
from typing import Literal, Annotated
from .models import (
    Blob,
    PathNotFoundException,
    JobMetadata,
    ServerLimitException
)
from .context import StorageServiceContext


storage_router = APIRouter()


@storage_router.put(
    '/store/put/{namespace}/{key}',
    status_code=202,
    responses={
        400: {
            "model": JobMetadata
        },
        429: {
            "model": ServerLimitException
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

    if isinstance(result, ServerLimitException):
        raise HTTPException(
            429,
            detail=result.dict()
        )

    elif result.error:
        raise HTTPException(
            400,
            detail=result.dict()
        )
    
    return result


@storage_router.get(
    '/store/get/{namespace}/{key}',
    responses={
        404: {
            "model": PathNotFoundException
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
        operation_type="download"
    )

    if isinstance(blob, PathNotFoundException):
        raise HTTPException(404, detail={
            "namespace": namespace,
            'key': key,
            "message": blob.message
        })
    
    result = await storage_service_context.queue.download(blob)

    if isinstance(result, PathNotFoundException):
        raise HTTPException(
            404,
            detail={
                "namespace": namespace,
                'key': key,
                "message": result.message          
            }
        )

    return Response(
        content=result.data,
        headers={
            'Content-Disposition': f'attachment; filename="{result.filename}"'
        },
        media_type=result.content_type
    )


@storage_router.delete(
    '/store/delete/{namespace}/{key}',
    responses={
        404: {
            "model": PathNotFoundException
        },
        429: {
            "model": ServerLimitException
        }
    }
)
async def delete_blob(
    namespace: str,
    key: str
) -> JobMetadata:
    storage_service_context: StorageServiceContext = context.get(ContextType.STORAGE_SERVICE)

    blob = await storage_service_context.queue.get_blob_metadata(
        namespace,
        key,
        operation_type="delete"
    )

    if isinstance(blob, PathNotFoundException):
        raise HTTPException(
            404, 
            detail=blob.dict()
        )
    
    result = await storage_service_context.queue.delete(blob)

    if isinstance(result, PathNotFoundException):
        raise HTTPException(
            404,
            detail=result.dict()
        )
    
    elif result.error:
        raise HTTPException(
            404,
            detail=result.dict()
        )
    
    
    return result


@storage_router.get(
    '/store/metadata/get/{namespace}/{key}',
    responses={
        404: {
            "model": PathNotFoundException
        }
    }
)
async def get_metadata(
    namespace: str,
    key: str    
) -> JobMetadata:

    storage_service_context: StorageServiceContext = context.get(ContextType.STORAGE_SERVICE)

    result = await storage_service_context.queue.get_job_metadata(
        namespace,
        key
    )

    if isinstance(result, PathNotFoundException):
        raise HTTPException(404, detail={
            "namespace": namespace,
            'key': key,
            "message": result.message
        })

    return result
