#!/usr/bin/env python
import pika
import time
import sys
import jsonpickle
import io
import redis
import socket
from neural_style_mod import transform



def get_license_plates(image_array):
    alpr = Alpr('us', '/etc/openalpr/openalpr.conf', '/usr/share/openalpr/runtime_data')
    results = alpr.recognize_array(image_array)
    redis_dict = {}
    plates = []
    try:
        for i in range(len(results["results"])):
            tmp_dict = {}
            tmp_dict.update({"plate": results["results"][i]["plate"]})
            tmp_dict.update({"confidence": results["results"][i]["confidence"]})
            plates.append(tmp_dict)
    except:
        print("License plate not found")

    redis_dict.update({"plates": plates})
    coordinates = getLatLon(image_array)
    redis_dict.update({"latitude": coordinates[0], "longitude": coordinates[1]})

    return redis_dict

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
    This function takes a log message and sends it to a RabbitMQ "rest.debug" topic
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
        routing_key='rest.debug',
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
        transform(data["content"], data["style"], data["output_file"])
    ch.basic_ack(delivery_tag=method.delivery_tag)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)

#print(' [*] Waiting for messages. To exit press CTRL+C')

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)
channel.start_consuming()
