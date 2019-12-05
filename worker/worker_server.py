#!/usr/bin/env python
import pika
import time
import sys
import jsonpickle
import io
import redis
import hashlib
import socket
from neural_style_mod import transform


def upload_picture_to_bucket(image_bytes, hash_value):
    """
    This function uploads an image to the a gcp storage bucket.
    The storage blob is named by the value given in hash value.

    Parameter:
    -image_bytes(bytes): the image to upload
    -hash_value(str): md5 hash value of image bytes. Blob is named after this in gcp cloud storage.
    """

    blob_name = hash_value
    bucket_name = 'style-transfer-images'
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

def send_to_redis(key, value, db_number):
    """
    This function puts a key-value pair into a user-defined Redis database

    Parameter:
    - key (str): The key of the key-value pair. In the case of our first
    API endpoint, it is the filename of the image.
    - value (varies): The value of the key-value pair.
    - db_number: The Redis database where we wish to store key-value pair

    """
    r=redis.Redis(host='redis', port=6379, db=db_number)
    r.set(key, value)

def get_from_redis(key, db_number):
    """
    This function takes a key and returns the associated value from a
    user-defined Redis database

    Parameters:
    - key (str): The key of the key-value pair.

    """
    r=redis.Redis(host='redis', port=6379, db=db_number)
    return r.get(key)

def send_to_logs(message):
    """
    This function takes a log message and sends it to a RabbitMQ "worker.debug" topic
    hosted on the "rabbitmq" VM using "logs" exchange.

    Parameters:
    - message(str): A string containing information such as file name,
    hash, HTTP status code, worker name, and error message (if applicable)

    """
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.exchange_declare(exchange='logs', exchange_type='topic')
    channel.basic_publish(
        exchange='logs',
        routing_key='worker.debug',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,
        ))

    #print("Logs delivered")
    connection.close()

def callback(ch, method, properties, body):
    """
    This function takes the next job from the worker queue and processes it.


    Parameters:
    - body(jsonpickle object): The body of the request
    """
    data = jsonpickle.decode(body)
    try:
        transformed_image = transform(data["content"], data["style"])
        hash_value = data['hash']
        upload_picture_to_bucket(transformed_image, hash_value)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        send_to_logs(e)


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)

#print(' [*] Waiting for messages. To exit press CTRL+C')

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)
channel.start_consuming()
