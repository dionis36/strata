import os
import uuid
import shutil
import logging

logger = logging.getLogger(__name__)

class TempStorageManager:
    """Manages ephemeral storage for Git clones and Zip extractions."""
    
    BASE_DIR = os.environ.get("TEMP_STORAGE_DIR", "/tmp/strata_ingests")

    @classmethod
    def get_job_dir(cls, job_id: str) -> str:
        """Returns a secure, absolute path for a specific job."""
        job_dir = os.path.join(cls.BASE_DIR, str(job_id))
        return os.path.abspath(job_dir)

    @classmethod
    def provision_job_dir(cls, job_id: str) -> str:
        """Creates and returns the directory for a job."""
        job_dir = cls.get_job_dir(job_id)
        os.makedirs(job_dir, exist_ok=True)
        return job_dir

    @classmethod
    def cleanup_job_dir(cls, job_id: str):
        """Permanently deletes the job directory and its contents."""
        job_dir = cls.get_job_dir(job_id)
        if os.path.exists(job_dir) and job_dir.startswith(cls.BASE_DIR):
            try:
                shutil.rmtree(job_dir)
                logger.info(f"Cleaned up temporary directory: {job_dir}")
            except Exception as e:
                logger.error(f"Failed to clean up {job_dir}: {e}")
