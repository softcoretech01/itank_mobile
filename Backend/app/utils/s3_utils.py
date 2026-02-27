import os
import re
import boto3
from datetime import datetime
from io import BytesIO

AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
PROJECT_NAME = os.getenv("PROJECT_NAME", "imageprocess")
CLOUDFRONT_BASE_URL = os.getenv("CLOUDFRONT_BASE_URL")

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

def clean_filename(filename: str) -> str:
    if not filename:
        return "file.bin"
    name, ext = os.path.splitext(filename.strip().lower())
    name = re.sub(r"[^a-zA-Z0-9_.-]", "", name.replace(" ", "_"))
    if not ext:
        ext = ".bin"
    return f"{name}{ext}"

def build_s3_key(original_filename: str) -> str:
    now = datetime.utcnow()
    year = now.year
    month = f"{now.month:02d}"
    timestamp = int(now.timestamp())
    clean_name = clean_filename(original_filename)
    return f"uploads/{PROJECT_NAME}/{year}/{month}/{timestamp}_{clean_name}"

def upload_fileobj_to_s3(fileobj, key: str, content_type: str) -> None:
    fileobj.seek(0)
    ct = content_type or "application/octet-stream"
    s3_client.upload_fileobj(
        fileobj,
        AWS_S3_BUCKET,
        key,
        ExtraArgs={"ContentType": ct}
    )

def delete_s3_object(key: str) -> None:
    try:
        s3_client.delete_object(Bucket=AWS_S3_BUCKET, Key=key)
    except Exception as e:
        print(f"S3 delete error for {key}: {e}")

def get_presigned_url(key: str, expiration=3600) -> str:
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': AWS_S3_BUCKET, 'Key': key},
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        print(f"Error generating presigned URL for {key}: {e}")
        return key

def to_cdn_url(key: str) -> str:
    if CLOUDFRONT_BASE_URL:
        return f"{CLOUDFRONT_BASE_URL}/{key.lstrip('/')}"
    return get_presigned_url(key)
