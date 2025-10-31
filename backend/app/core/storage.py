import logging

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO storage client wrapper"""

    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensure the default bucket exists"""
        try:
            if not self.client.bucket_exists(settings.MINIO_BUCKET):
                self.client.make_bucket(settings.MINIO_BUCKET)
                logger.info(f"Created bucket: {settings.MINIO_BUCKET}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")

    def upload_file(self, file_path: str, object_name: str, content_type: str = None):
        """Upload a file to MinIO"""
        try:
            self.client.fput_object(
                settings.MINIO_BUCKET, object_name, file_path, content_type=content_type
            )
            return True
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            return False

    def download_file(self, object_name: str, file_path: str):
        """Download a file from MinIO"""
        try:
            self.client.fget_object(settings.MINIO_BUCKET, object_name, file_path)
            return True
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            return False

    def delete_file(self, object_name: str):
        """Delete a file from MinIO"""
        try:
            self.client.remove_object(settings.MINIO_BUCKET, object_name)
            return True
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            return False

    def get_presigned_url(self, object_name: str, expires: int = 3600):
        """Get a presigned URL for an object"""
        try:
            url = self.client.presigned_get_object(
                settings.MINIO_BUCKET, object_name, expires=expires
            )
            return url
        except S3Error as e:
            logger.error(f"Error getting presigned URL: {e}")
            return None


# Singleton instance
minio_client = MinIOClient()
