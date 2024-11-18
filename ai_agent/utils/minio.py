from minio import Minio
from django.conf import settings

bucket_name = settings.MINIO_BUCKET_NAME
minio_base_path = settings.MINIO_BASE_PATH

# SPEAK_TEXT = {"text":f"Hello Amul, this is Ginie from Army of Me. I hope you're doing well today! We provide a range of accounting and financial services, including bookkeeping, tax preparation, payroll processing, and more. Is there a particular service you are interested in, or would you like an overview of our offerings? "}

minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRETE_KEY,
    secure=settings.MINIO_USE_HTTPS,
)


# public_url_storage = {}

# def store_public_url(call_sid, public_url):
#     public_url_storage[call_sid] = public_url

# def retrieve_public_url(call_sid):
#     return public_url_storage.get(call_sid)
