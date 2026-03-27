from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from src.core.dependencies import (
    get_authorization_header,
    get_current_user,
    get_request_id,
)
from src.schemas.ingest import IngestionRequest, IngestionResponse
from src.workers.ingestion_worker import get_ingestion_worker
from src.workers.job_service import job_service

router = APIRouter()


class CancelResponse(BaseModel):
    jobId: str
    status: str
    message: str


@router.post("/", response_model=IngestionResponse)
async def ingest(
    req: IngestionRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
    authorization: Optional[str] = Depends(get_authorization_header),
    request_id: Optional[str] = Depends(get_request_id),
):
    job_id = job_service.create_job()
    background_tasks.add_task(
        get_ingestion_worker().run,
        job_id,
        req.fileId,
        req.projectId,
        req.options,
        user_id,
        authorization,
        request_id,
    )
    return IngestionResponse(jobId=job_id, status="queued")


@router.get("/status/{job_id}")
async def status(job_id: str):
    job_status = job_service.get_status(job_id)
    if job_status.get("status") == "unknown":
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job_status


@router.post("/cancel/{job_id}", response_model=CancelResponse)
async def cancel(job_id: str):
    job_status = job_service.get_status(job_id)
    if job_status.get("status") == "unknown":
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    current_status = job_status.get("status")
    if current_status in ["completed", "failed", "cancelled"]:
        return CancelResponse(
            jobId=job_id,
            status=current_status,
            message=f"Job already {current_status}",
        )

    job_service.set_status(job_id, "cancelled")
    return CancelResponse(
        jobId=job_id,
        status="cancelled",
        message="Job cancellation requested",
    )
