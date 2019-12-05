#!/usr/bin/env python
from flask import Flask, request, Response
import jsonpickle
import io
import hashlib
import pika
#import redis

def send_to_worker_queue(message):
    """
    This function takes a message and sends it to a RabbitMQ worker queue
    "task_queue" hosted on the "rabbitmq" VM using "toWorker" exchange.

    Parameters:
    - message(jsonpickle object):

    """
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    worker_channel = channel.queue_declare(queue='task_queue', durable=True)
    channel.exchange_declare(exchange='toWorker', exchange_type='direct')
    channel.queue_bind(exchange='toWorker',queue=worker_channel.method.queue)
    channel.basic_publish(
        exchange='toWorker',
        routing_key='task_queue',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,
        ))
    #print("Message delivered")
    connection.close()

def send_to_logs(message):
    """
    This function takes a log message and sends it to a RabbitMQ "rest.debug" topic
    hosted on the "rabbitmq" VM using "logs" exchange.

    Parameters:
    - message(str): A string containing information such as file name,
    hash, HTTP status code, and error message (if applicable)

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

def send_to_redis(key, value, db_number):
    """
    This function puts a key-value pair into a user-defined Redis database

    Parameter:
    - key (str): The key of the key-value pair. In the case of our first
    API endpoint, it is the filename of the image.
    - value (str): The value of the key-value pair. In the case of our first
    API endpoint, it is the hash value of the images
    - db_number: The Redis database where we wish to store key-value pair

    """
    r=redis.Redis(host='redis', port=6379, db=db_number)
    r.set(key, value)

# Initialize the Flask application
app = Flask(__name__)
@app.route('/image/<string:filename>', methods=['PUT'])
def transform_image(filename):
    """
    This function...

    Parameters:

    Returns:
    - response(jsonpickle object): If request is successful, the response to the client
    is a HTTP 200 code and the hash of the image. If request is unsuccessful, the Response
    is a HTTP 500 code and the associated error.
    """

    data = jsonpickle.decode(request.data)
    #transform(data["content"], data["style"], data["output_file"])

    hash = None
    try:
        hash = hashlib.md5(data["content"]).hexdigest()
        data.update({"hash": hash})
        print(data)
        #send_to_worker_queue(jsonpickle.encode(data))
        #send_to_redis(filename, message["hash"], 2)
        response = {
            "hash" : hash,
            }
        response = Response(response=jsonpickle.encode(response), status=200, mimetype="application/json")
        send_to_logs("Image Received: " +filename+ ", Hash: "+hash+", Status code: "+str(response.status_code))
        return response

    except Exception as inst:
        response = {"Error": inst}
        response = Response(response=jsonpickle.encode(response), status=500, mimetype="application/json")
        send_to_logs("Image Received: " +filename + ", Hash: "+hash+", Status code: "+str(response.status_code)+ ", Error: " +str(inst))
        return response

app.run(host="0.0.0.0", port=5000)
