import uuid
from datetime import datetime, timezone
from typing import Optional


class JobService:
    def __init__(self):
        self.jobs = {}

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "status": "queued",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "error": None,
        }
        return job_id

    def set_status(self, job_id: str, status: str):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            self.jobs[job_id]["updatedAt"] = datetime.now(timezone.utc).isoformat()
        else:
            self.jobs[job_id] = {"status": status}

    def set_result(self, job_id: str, result: dict):
        if job_id in self.jobs:
            self.jobs[job_id]["result"] = result

    def set_error(self, job_id: str, error: str):
        if job_id in self.jobs:
            self.jobs[job_id]["error"] = error

    def get_status(self, job_id: str) -> dict:
        return self.jobs.get(job_id, {"status": "unknown"})

    def get_job(self, job_id: str) -> Optional[dict]:
        return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        if job_id in self.jobs:
            current = self.jobs[job_id]["status"]
            if current in ["queued", "processing"]:
                self.jobs[job_id]["status"] = "cancelled"
                self.jobs[job_id]["updatedAt"] = datetime.now(timezone.utc).isoformat()
                return True
        return False


job_service = JobService()
