#!/usr/bin/env python

from google.cloud import storage
import jsonpickle
import hashlib
import io
import numpy as np #needed to convert image to right file type for style transfer lib
import pika
from PIL import Image
import scipy.misc #needed to convert image to right file type for style transfer lib
import sys

from neural_style_mod import transform



def upload_picture_to_bucket(image_bytes, hash_value):
    """
    This function uploads an image to the a gcp storage bucket.
    The storage blob is named by the value given in hash value.

    Parameter:
    -image_bytes(bytes): the image to upload
    -hash_value(str): md5 hash value of image bytes. Bucket is named after this. Blob is incremented once for every image uploaded.
    """

    bucket_name = 'csci5253-style'
    bucket_name += '-' + hash_value

    storage_client = storage.Client()

    #get all bucket names
    bucket = None
    buckets = storage_client.list_buckets()
    bucket_names = []
    for bucket in buckets:
        bucket_names.append(bucket.name)

    #if bucket exists, get it, otherwise create it
    if bucket_name not in bucket_names:
        bucket = storage_client.create_bucket(bucket_name)
    else:
        bucket = storage_client.get_bucket(bucket_name)

    #Get all blobs names. Create incrementer for blob name
    blobs = bucket.list_blobs()
    num_blobs = 0
    for blob in blobs:
        num_blobs += 1

    blob = bucket.blob(str(num_blobs))
    blob.upload_from_string(image_bytes, content_type='image/jpg')

def send_to_logs(message):
    """
    This function takes a log message and sends it to a RabbitMQ "worker.debug" topic
    hosted on the "rabbitmq" VM using "logs" exchange.

    Parameters:
    - message(str): A string containing information such as file name,
    hash, HTTP status code, worker name, and error message (if applicable)

    """
    channel.exchange_declare(exchange='logs', exchange_type='topic')
    channel.basic_publish(
        exchange='logs',
        routing_key='worker.debug',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,
        ))

def _imread(image_file_or_path):
    """Utility function to convert image to same format as style transfer library requires.
    Parameters:
    -image_file_or_path(str or file object): A file path string to the image,
        or a object that implements file semantics, and has image in it.
    """
    img = scipy.misc.imread(image_file_or_path).astype(np.float)
    if len(img.shape) == 2:
        # grayscale
        img = np.dstack((img,img,img))
    elif img.shape[2] == 4:
        # PNG with alpha channel
        img = img[:,:,:3]
    return img


def callback(ch, method, properties, body):
    """
    This function takes the next job from the worker queue and processes it.


    Parameters:
    - body(jsonpickle object): The body of the request
    """

    try:
        data = jsonpickle.decode(body)
        hash_value = data['hash']
        iterations = data['iterations']

        #Get file type object for target and style so we can use imread helper.
        target_image = io.BytesIO(data['content'])
        style_image = io.BytesIO(data['style'])
        transformed_image = transform(_imread(target_image), _imread(style_image), iterations)

        #Convert back to bytes from np floating point array
        transformed_image_bytes = io.BytesIO()
        transformed_image = np.clip(transformed_image, 0, 255).astype(np.uint8)
        image = Image.fromarray(transformed_image)
        image.save(transformed_image_bytes,format='JPEG')
        upload_picture_to_bucket(transformed_image_bytes.getvalue(), hash_value)
        #Successfully transformed and uploaded
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        send_to_logs(str(e))


while True:
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbitmq', heartbeat=0))
        channel = connection.channel()
        channel.queue_declare(queue='task_queue', durable=True)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='task_queue', on_message_callback=callback)

        channel.start_consuming()

        # Don't recover if connection was closed by broker
    except pika.exceptions.ConnectionClosedByBroker:
        break
        # Don't recover on channel errors
    except pika.exceptions.AMQPChannelError:
        break
        # Recover on all other connection errors
    except pika.exceptions.AMQPConnectionError:
        continue
    except pika.exceptions.ConnectionWrongStateError:
        continue
