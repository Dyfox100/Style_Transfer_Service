import google.cloud.storage as storage
import hashlib
from PIL import Image
import io

def setup_test_image():
    image_file_name = "moon.jpg"
    image = Image.open(image_file_name)
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format=image.format)
    return imgByteArr.getvalue()

def upload_picture_to_bucket(image_bytes):
    blob_name = hashlib.md5(image_bytes).hexdigest()
    bucket_name = 'test-images-12345'
    file_name = "moon.jpg"
    storage_client = storage.Client()
    bucket = None
    buckets = storage_client.list_buckets()
    bucket_names = []
    for bucket in buckets:
        bucket_names.append(bucket.name)
    if bucket_name not in bucket_names:
        bucket = storage_client.create_bucket(bucket_name)
    else:
        bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(image_bytes, content_type='image/jpg')
    return blob_name

def get_image_from_bucket(image_hash):
    bucket_name = 'test-images-12345'
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(image_hash)
    image_returned = blob.download_as_string()
    return image_returned


if __name__ == "__main__":
    hash = upload_picture_to_bucket(setup_test_image())
    print('upload complete')
    print(get_image_from_bucket(hash))
