"""MinIO / S3 Storage service for document persistence and lifecycle management."""

from datetime import timedelta
import io
from typing import List, Optional
from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.core.logging import app_logger


class MinIOService:
    """MinIO client wrapper handling uploads, downloads, presigned URLs, and cascading deletes."""

    def __init__(self) -> None:
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME

        # External/Public signer client specifically for generating presigned URLs (SigV4 Host header matching)
        if settings.MINIO_PUBLIC_URL:
            public_host = (
                settings.MINIO_PUBLIC_URL.replace("http://", "")
                .replace("https://", "")
                .rstrip("/")
            )
            is_secure = settings.MINIO_PUBLIC_URL.startswith("https")
            # Explicit region="us-east-1" enables 100% offline SigV4 calculation without internal network calls to public host
            self.signer_client = Minio(
                endpoint=public_host,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=is_secure,
                region="us-east-1",
            )
        else:
            self.signer_client = self.client

    def ensure_bucket_exists(self) -> None:
        """Create storage bucket if it does not already exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                app_logger.info(f"Created MinIO bucket '{self.bucket_name}'")
        except Exception as exc:
            app_logger.warning(f"MinIO bucket check warning: {str(exc)}")

    def upload_bytes(
        self,
        storage_path: str,
        data_bytes: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw bytes to MinIO storage path."""
        self.ensure_bucket_exists()
        stream = io.BytesIO(data_bytes)
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=storage_path,
            data=stream,
            length=len(data_bytes),
            content_type=content_type,
        )
        app_logger.info(f"Saved {len(data_bytes)} bytes to MinIO: {storage_path}")
        return storage_path

    def get_bytes(self, storage_path: str) -> bytes:
        """Retrieve raw file bytes from MinIO."""
        response = None
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=storage_path,
            )
            return response.read()
        finally:
            if response:
                response.close()
                response.release_conn()

    def generate_presigned_get_url(
        self, storage_path: str, expires_seconds: int = 1800
    ) -> str:
        """Generate a temporary presigned GET URL for secure viewing."""
        try:
            url = self.signer_client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=storage_path,
                expires=timedelta(seconds=expires_seconds),
            )
            return url
        except Exception as exc:
            app_logger.error(f"Error generating presigned URL for '{storage_path}': {str(exc)}")
            return ""

    def delete_object(self, storage_path: str) -> bool:
        """Delete a single object from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, storage_path)
            app_logger.info(f"Removed object from MinIO: {storage_path}")
            return True
        except S3Error as exc:
            app_logger.error(f"Failed to delete object '{storage_path}': {str(exc)}")
            return False

    def delete_prefix(self, prefix: str) -> int:
        """Cascade hard-delete all objects starting with prefix (RN-13 Right to be Forgotten)."""
        deleted_count = 0
        try:
            objects = self.client.list_objects(
                self.bucket_name, prefix=prefix, recursive=True
            )
            for obj in objects:
                self.client.remove_object(self.bucket_name, obj.object_name)
                deleted_count += 1
            app_logger.info(
                f"Cascade hard-deleted {deleted_count} objects under prefix '{prefix}' from MinIO"
            )
            return deleted_count
        except Exception as exc:
            app_logger.error(f"Error during prefix deletion '{prefix}': {str(exc)}")
            return deleted_count


# Global singleton instance
minio_service = MinIOService()
