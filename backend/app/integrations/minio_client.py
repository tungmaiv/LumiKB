"""MinIO S3-compatible object storage integration."""

import hashlib
from typing import BinaryIO
from uuid import UUID

import boto3
import structlog
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings

logger = structlog.get_logger(__name__)


class MinIOService:
    """Service for MinIO S3-compatible object storage operations.

    Each Knowledge Base has its own bucket named `kb-{uuid}`.
    Files are stored at path: `{kb_id}/{doc_id}/{filename}`.
    """

    def __init__(self) -> None:
        """Initialize MinIO client with settings."""
        self._client: boto3.client | None = None

    @property
    def client(self) -> boto3.client:
        """Lazy initialization of S3/MinIO client.

        Returns:
            boto3.client: The S3-compatible client instance.
        """
        if self._client is None:
            # Tech Debt Fix P2: Add timeouts to prevent hanging connections
            # that can cause documents to get stuck in Processing status
            config = Config(
                connect_timeout=30,  # 30 seconds to establish connection
                read_timeout=60,  # 60 seconds for read operations
                retries={"max_attempts": 3},  # Retry up to 3 times on failure
            )
            endpoint_url = (
                f"{'https' if settings.minio_secure else 'http'}://"
                f"{settings.minio_endpoint}"
            )
            self._client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=settings.minio_access_key,
                aws_secret_access_key=settings.minio_secret_key,
                region_name="us-east-1",  # Required by boto3, not used by MinIO
                config=config,
            )
        return self._client

    def _bucket_name(self, kb_id: UUID) -> str:
        """Generate bucket name for a KB.

        Args:
            kb_id: The Knowledge Base UUID.

        Returns:
            Bucket name in format `kb-{uuid}`.
        """
        return f"kb-{kb_id}"

    async def ensure_bucket_exists(self, kb_id: UUID) -> None:
        """Ensure a bucket exists for a Knowledge Base.

        Creates the bucket if it doesn't exist.

        Args:
            kb_id: The Knowledge Base UUID.
        """
        bucket = self._bucket_name(kb_id)

        try:
            self.client.head_bucket(Bucket=bucket)
            logger.debug(
                "minio_bucket_exists",
                bucket=bucket,
                kb_id=str(kb_id),
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                # Bucket doesn't exist, create it
                self.client.create_bucket(Bucket=bucket)
                logger.info(
                    "minio_bucket_created",
                    bucket=bucket,
                    kb_id=str(kb_id),
                )
            else:
                logger.error(
                    "minio_bucket_check_failed",
                    bucket=bucket,
                    kb_id=str(kb_id),
                    error=str(e),
                )
                raise

    async def upload_file(
        self,
        kb_id: UUID,
        object_path: str,
        file: BinaryIO,
        content_type: str,
    ) -> str:
        """Upload a file to MinIO.

        Args:
            kb_id: The Knowledge Base UUID (determines bucket).
            object_path: The path within the bucket (e.g., "{doc_id}/{filename}").
            file: The file-like object to upload.
            content_type: The MIME type of the file.

        Returns:
            The full path of the uploaded file: "{bucket}/{object_path}".

        Raises:
            ClientError: If upload fails.
        """
        bucket = self._bucket_name(kb_id)

        try:
            # Ensure bucket exists
            await self.ensure_bucket_exists(kb_id)

            # Get file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning

            self.client.upload_fileobj(
                file,
                bucket,
                object_path,
                ExtraArgs={
                    "ContentType": content_type,
                },
            )

            logger.info(
                "minio_file_uploaded",
                bucket=bucket,
                object_path=object_path,
                content_type=content_type,
                file_size=file_size,
            )

            return f"{bucket}/{object_path}"

        except Exception as e:
            logger.error(
                "minio_upload_failed",
                bucket=bucket,
                object_path=object_path,
                error=str(e),
            )
            raise

    async def delete_file(self, kb_id: UUID, object_path: str) -> None:
        """Delete a file from MinIO.

        Args:
            kb_id: The Knowledge Base UUID (determines bucket).
            object_path: The path within the bucket.

        Raises:
            ClientError: If deletion fails.
        """
        bucket = self._bucket_name(kb_id)

        try:
            self.client.delete_object(Bucket=bucket, Key=object_path)

            logger.info(
                "minio_file_deleted",
                bucket=bucket,
                object_path=object_path,
            )

        except Exception as e:
            logger.error(
                "minio_delete_failed",
                bucket=bucket,
                object_path=object_path,
                error=str(e),
            )
            raise

    async def file_exists(self, kb_id: UUID, object_path: str) -> bool:
        """Check if a file exists in MinIO.

        Args:
            kb_id: The Knowledge Base UUID (determines bucket).
            object_path: The path within the bucket.

        Returns:
            True if file exists, False otherwise.
        """
        bucket = self._bucket_name(kb_id)

        try:
            self.client.head_object(Bucket=bucket, Key=object_path)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            raise

    async def download_file(self, kb_id: UUID, object_path: str) -> bytes:
        """Download a file from MinIO.

        Args:
            kb_id: The Knowledge Base UUID (determines bucket).
            object_path: The path within the bucket.

        Returns:
            The file contents as bytes.

        Raises:
            ClientError: If download fails or file not found.
        """
        bucket = self._bucket_name(kb_id)

        try:
            response = self.client.get_object(Bucket=bucket, Key=object_path)
            data = response["Body"].read()

            logger.info(
                "minio_file_downloaded",
                bucket=bucket,
                object_path=object_path,
                file_size=len(data),
            )

            return data

        except Exception as e:
            logger.error(
                "minio_download_failed",
                bucket=bucket,
                object_path=object_path,
                error=str(e),
            )
            raise

    async def list_objects(
        self,
        kb_id: UUID,
        prefix: str = "",
    ) -> list[str]:
        """List objects in a bucket with optional prefix.

        Args:
            kb_id: The Knowledge Base UUID (determines bucket).
            prefix: Optional prefix to filter objects.

        Returns:
            List of object keys matching the prefix.
        """
        bucket = self._bucket_name(kb_id)
        object_keys: list[str] = []

        try:
            # Check if bucket exists first
            try:
                self.client.head_bucket(Bucket=bucket)
            except ClientError as e:
                if e.response.get("Error", {}).get("Code") == "404":
                    logger.debug(
                        "minio_bucket_not_found",
                        bucket=bucket,
                        kb_id=str(kb_id),
                    )
                    return []
                raise

            # Use paginator for large buckets
            paginator = self.client.get_paginator("list_objects_v2")
            pages = paginator.paginate(
                Bucket=bucket,
                Prefix=prefix,
            )

            for page in pages:
                contents = page.get("Contents", [])
                for obj in contents:
                    object_keys.append(obj["Key"])

            logger.debug(
                "minio_objects_listed",
                bucket=bucket,
                prefix=prefix,
                count=len(object_keys),
            )

            return object_keys

        except Exception as e:
            logger.error(
                "minio_list_objects_failed",
                bucket=bucket,
                prefix=prefix,
                error=str(e),
            )
            raise

    async def delete_objects(self, kb_id: UUID, object_keys: list[str]) -> int:
        """Delete multiple objects from a bucket.

        Args:
            kb_id: The Knowledge Base UUID (determines bucket).
            object_keys: List of object keys to delete.

        Returns:
            Number of objects deleted.
        """
        if not object_keys:
            return 0

        bucket = self._bucket_name(kb_id)

        try:
            # S3 delete_objects accepts up to 1000 keys per request
            deleted_count = 0
            batch_size = 1000

            for i in range(0, len(object_keys), batch_size):
                batch = object_keys[i : i + batch_size]
                delete_request = {
                    "Objects": [{"Key": key} for key in batch],
                    "Quiet": True,
                }

                response = self.client.delete_objects(
                    Bucket=bucket,
                    Delete=delete_request,
                )

                # Count errors if any
                errors = response.get("Errors", [])
                deleted_count += len(batch) - len(errors)

                if errors:
                    logger.warning(
                        "minio_delete_objects_partial_failure",
                        bucket=bucket,
                        error_count=len(errors),
                        errors=errors[:5],  # Log first 5 errors
                    )

            logger.info(
                "minio_objects_deleted",
                bucket=bucket,
                deleted_count=deleted_count,
                requested_count=len(object_keys),
            )

            return deleted_count

        except Exception as e:
            logger.error(
                "minio_delete_objects_failed",
                bucket=bucket,
                object_count=len(object_keys),
                error=str(e),
            )
            raise

    async def delete_bucket(self, kb_id: UUID) -> bool:
        """Delete a bucket and all its contents.

        Args:
            kb_id: The Knowledge Base UUID (determines bucket).

        Returns:
            True if bucket was deleted, False if it didn't exist.
        """
        bucket = self._bucket_name(kb_id)

        try:
            # Check if bucket exists
            try:
                self.client.head_bucket(Bucket=bucket)
            except ClientError as e:
                if e.response.get("Error", {}).get("Code") == "404":
                    logger.debug(
                        "minio_bucket_not_found_for_delete",
                        bucket=bucket,
                        kb_id=str(kb_id),
                    )
                    return False
                raise

            # Delete all objects first
            object_keys = await self.list_objects(kb_id)
            if object_keys:
                await self.delete_objects(kb_id, object_keys)

            # Now delete the empty bucket
            self.client.delete_bucket(Bucket=bucket)

            logger.info(
                "minio_bucket_deleted",
                bucket=bucket,
                kb_id=str(kb_id),
            )
            return True

        except Exception as e:
            logger.error(
                "minio_bucket_delete_failed",
                bucket=bucket,
                kb_id=str(kb_id),
                error=str(e),
            )
            raise

    async def health_check(self) -> bool:
        """Check if MinIO connection is healthy.

        Returns:
            True if connection is healthy, False otherwise.
        """
        try:
            self.client.list_buckets()
            return True
        except Exception as e:
            logger.error("minio_health_check_failed", error=str(e))
            return False


def compute_checksum(file: BinaryIO) -> str:
    """Compute SHA-256 checksum of a file.

    Args:
        file: The file-like object.

    Returns:
        Hex-encoded SHA-256 checksum.
    """
    sha256 = hashlib.sha256()
    file.seek(0)

    for chunk in iter(lambda: file.read(8192), b""):
        sha256.update(chunk)

    file.seek(0)  # Reset for subsequent reads
    return sha256.hexdigest()


# Singleton instance for use across the application
minio_service = MinIOService()
