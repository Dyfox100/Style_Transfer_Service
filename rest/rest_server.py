#!/usr/bin/env python

from flask import Flask, request, Response
import io
import jsonpickle
import hashlib
import pika

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
    connection.close()


#######################
#FLASK APP CODE FOR ENDPOINTS
app = Flask(__name__)

@app.route('/image', methods=['PUT'])
def transform_image():
    """
    Route to style transfer two images.

    Parameters:

    Returns:
    - response(jsonpickle object): If request is successful, the response to the client
    is a HTTP 200 code and the hash of the image. If request is unsuccessful, the Response
    is a HTTP 500 code and the associated error.
    """

    try:
        data = jsonpickle.decode(request.data)
        hash = hashlib.md5(data["content"]).hexdigest()
        data.update({"hash": hash})
        send_to_worker_queue(jsonpickle.encode(data))
        response = {
            "hash" : hash,
            }
        response = Response(response=jsonpickle.encode(response), status=200, mimetype="application/json")
        send_to_logs("Image Received: Hash: "+hash+", Status code: "+str(response.status_code))
        return response

    except Exception as e:
        response = Response(status=500, mimetype="application/json")
        send_to_logs("Image Received: " +filename + ", Hash: "+hash+", Status code: "+str(response.status_code)+ ", Error: " +str(e))
        return response

@app.route('/image/<hashvalue>', methods=['GET'])
def get_transformed_image(hashvalue):
    """
    Route to get an image that has been style transfered.

    Parameters:

    Returns:
    - response(jsonpickle object): If request is successful, the response to the client
    is a HTTP 200 code and the hash of the image. If request is unsuccessful, the Response
    is a HTTP 500 code and the associated error.
    """

    try:
        ##TO DO: ADD GET Route
        pass

    except Exception as e:
        response = Response(status=500, mimetype="application/json")
        send_to_logs("Image Received: " +filename + ", Hash: "+hash+", Status code: "+str(response.status_code)+ ", Error: " +str(e))
        return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
