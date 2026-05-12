from __future__ import annotations

import asyncio
from typing import Any
import logging

import boto3
from botocore.config import Config

from ..config import Settings
from ..utils.http import fetch_bytes


class StorageService:
	"""S3-compatible storage wrapper."""

	_logger = logging.getLogger(__name__)

	def __init__(self, settings: Settings) -> None:
		self._settings = settings
		self._client = self._create_client()

	def _create_client(self) -> Any:
		"""Create an S3 client with optional role assumption."""
		endpoint_url = self._settings.s3_endpoint_url or None
		base_session = boto3.Session(
			aws_access_key_id=self._settings.aws_access_key_id,
			aws_secret_access_key=self._settings.aws_secret_access_key,
			region_name=self._settings.aws_region,
		)
		if self._settings.aws_role_arn:
			sts_client = base_session.client("sts")
			response = sts_client.assume_role(
				RoleArn=self._settings.aws_role_arn,
				RoleSessionName=self._settings.aws_role_session_name,
			)
			creds = response["Credentials"]
			session = boto3.Session(
				aws_access_key_id=creds["AccessKeyId"],
				aws_secret_access_key=creds["SecretAccessKey"],
				aws_session_token=creds["SessionToken"],
				region_name=self._settings.aws_region,
			)
		else:
			session = base_session
		config = None
		if endpoint_url:
			config = Config(s3={"addressing_style": "path"})
		return session.client(
			"s3",
			endpoint_url=endpoint_url,
			config=config,
		)

	async def upload_bytes(self, key: str, data: bytes, content_type: str | None) -> str:
		"""Upload bytes and return a storage URL."""
		await asyncio.to_thread(
			self._client.put_object,
			Bucket=self._settings.aws_s3_bucket,
			Key=key,
			Body=data,
			ContentType=content_type or "application/octet-stream",
		)
		self._logger.info(
			"Storage: uploaded bucket=%s key=%s content_type=%s",
			self._settings.aws_s3_bucket,
			key,
			content_type or "application/octet-stream",
		)
		return self._build_url(key)

	def _build_url(self, key: str) -> str:
		"""Build a public or s3 URL for the object."""
		if self._settings.s3_public_base_url:
			base = self._settings.s3_public_base_url.rstrip("/")
			return f"{base}/{key}"
		return f"s3://{self._settings.aws_s3_bucket}/{key}"

	def _parse_s3_url(self, url: str) -> tuple[str, str]:
		if not url.startswith("s3://"):
			raise ValueError("URL is not an s3:// URL")
		path = url.replace("s3://", "", 1)
		if "/" not in path:
			raise ValueError("S3 URL missing key")
		bucket, key = path.split("/", 1)
		return bucket, key

	async def download_bytes_from_url(self, url: str) -> bytes:
		"""Download bytes from s3:// or http(s) URL."""
		if url.startswith("s3://"):
			bucket, key = self._parse_s3_url(url)
			return await self.download_bytes(key, bucket=bucket)
		if url.startswith("http://") or url.startswith("https://"):
			return await fetch_bytes(
				url,
				auth=None,
				timeout_seconds=self._settings.http_timeout_seconds,
				max_retries=self._settings.http_max_retries,
			)
		raise ValueError("Unsupported URL scheme")

	async def download_bytes(self, key: str, bucket: str | None = None) -> bytes:
		"""Download bytes from S3."""
		bucket_name = bucket or self._settings.aws_s3_bucket
		def _read() -> bytes:
			response = self._client.get_object(Bucket=bucket_name, Key=key)
			return response["Body"].read()
		data = await asyncio.to_thread(_read)
		self._logger.info("Storage: downloaded bucket=%s key=%s", bucket_name, key)
		return data

	def generate_presigned_url(self, key: str, expires_in: int = 3600, bucket: str | None = None) -> str:
		"""Generate a presigned URL for a private object."""
		bucket_name = bucket or self._settings.aws_s3_bucket
		url = self._client.generate_presigned_url(
			"get_object",
			Params={"Bucket": bucket_name, "Key": key},
			ExpiresIn=expires_in,
		)
		self._logger.info("Storage: presigned url generated bucket=%s key=%s", bucket_name, key)
		return url

	def presign_s3_url(self, s3_url: str, expires_in: int = 3600) -> str:
		"""Generate a presigned URL from an s3:// URL."""
		bucket, key = self._parse_s3_url(s3_url)
		return self.generate_presigned_url(key, expires_in=expires_in, bucket=bucket)
