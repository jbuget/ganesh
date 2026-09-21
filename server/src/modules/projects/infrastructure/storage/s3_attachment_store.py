"""The object store, spoken to over the S3 API.

One adapter, two addresses: in production it talks to S3 and the instance's
IAM role signs the calls; on a laptop `s3_endpoint_url` points at the MinIO of
`docker-compose.yml`, with keys from `.env`. What runs locally is therefore
what runs in production, which is where the surprises otherwise hide.

`aioboto3` rather than `boto3`: every I/O of this project is awaited, and a
blocking call here would hold the loop for as long as a ten-megabyte upload
takes.
"""

from typing import Any

import aioboto3
from botocore.exceptions import ClientError

from src.modules.projects.domain.repositories.attachment_store import AttachmentStore
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

#: What S3 answers when the key holds nothing. MinIO answers the same.
_ABSENT = {"NoSuchKey", "404", "NoSuchBucket"}


class S3AttachmentStore(AttachmentStore):
    """Files, in a bucket."""

    def __init__(
        self,
        bucket: str,
        region: str,
        endpoint_url: str = "",
        access_key_id: str = "",
        secret_access_key: str = "",
    ) -> None:
        self._bucket = bucket
        self._session = aioboto3.Session(
            region_name=region or None,
            # Left empty in production: the instance carries a role, and
            # botocore finds it on its own. Handing it empty strings instead
            # would make it sign every call as nobody.
            aws_access_key_id=access_key_id or None,
            aws_secret_access_key=secret_access_key or None,
        )
        self._endpoint_url = endpoint_url or None

    def _client(self) -> Any:
        return self._session.client("s3", endpoint_url=self._endpoint_url)

    async def put(self, key: str, content: bytes, content_type: str) -> None:
        async with self._client() as s3:
            await s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
            )

    async def get(self, key: str) -> bytes:
        async with self._client() as s3:
            try:
                answer = await s3.get_object(Bucket=self._bucket, Key=key)
            except ClientError as error:
                if error.response.get("Error", {}).get("Code") in _ABSENT:
                    raise EntityNotFoundError("The file cannot be found.") from error
                raise
            content: bytes = await answer["Body"].read()
            return content

    async def delete(self, key: str) -> None:
        # S3 says nothing when the key held nothing, and that is the right
        # answer: a file already gone is a file gone.
        async with self._client() as s3:
            await s3.delete_object(Bucket=self._bucket, Key=key)
