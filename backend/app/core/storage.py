import io
import logging
from datetime import timedelta
from urllib.parse import urlparse, urlunparse

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

    def upload_data(self, data: bytes, object_name: str, content_type: str = "application/octet-stream") -> bool:
        """Upload raw bytes to MinIO without writing a temporary file."""
        try:
            self.client.put_object(
                settings.MINIO_BUCKET,
                object_name,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            return True
        except S3Error as e:
            logger.error(f"Error uploading data to {object_name}: {e}")
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

    def file_exists(self, object_name: str) -> bool:
        """Check if a file exists in MinIO"""
        try:
            self.client.stat_object(settings.MINIO_BUCKET, object_name)
            return True
        except S3Error:
            return False

    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str | None:
        """Get a presigned URL for an object.

        Args:
            object_name: The object key in the bucket.
            expires: URL expiration time in seconds (default 1 hour).

        Returns:
            The presigned URL string, or None on error.

        If ``MINIO_PUBLIC_URL`` is configured, the internal MinIO hostname is
        replaced with the public base URL so that external services (e.g. the
        Instagram Graph API) can actually reach the file.  The HMAC signature
        in the presigned URL is computed over the path and query string only,
        not the hostname, so rewriting the host does not invalidate it.
        """
        try:
            url = self.client.presigned_get_object(
                settings.MINIO_BUCKET,
                object_name,
                expires=timedelta(seconds=expires),
            )
            if settings.MINIO_PUBLIC_URL:
                url = self._rewrite_to_public_url(url)
            return url
        except S3Error as e:
            logger.error(f"Error getting presigned URL for {object_name}: {e}")
            return None

    @staticmethod
    def _rewrite_to_public_url(internal_url: str) -> str:
        """Replace the internal MinIO scheme+host with the configured public URL.

        The presigned HMAC signature covers the path and query string, not the
        host header, so this rewrite is safe and does not break the signature.

        Example:
            internal:  http://minio:9000/clipper-media/media/uuid.png?X-Amz-...
            public:    https://machine-systems.org/minio/clipper-media/media/uuid.png?X-Amz-...
        """
        public = settings.MINIO_PUBLIC_URL.rstrip("/")
        parsed_internal = urlparse(internal_url)
        parsed_public = urlparse(public)

        rewritten = urlunparse((
            parsed_public.scheme,
            parsed_public.netloc,
            parsed_public.path.rstrip("/") + parsed_internal.path,
            parsed_internal.params,
            parsed_internal.query,
            parsed_internal.fragment,
        ))
        return rewritten


# Singleton instance
minio_client = MinIOClient()
