#!/usr/bin/env python
import pika
import time
import sys
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import jsonpickle
from openalpr import Alpr
import io
import redis
import socket

def get_exif_data(image):
    """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for gps_tag in value:
                    sub_decoded = GPSTAGS.get(gps_tag, gps_tag)
                    gps_data[sub_decoded] = value[gps_tag]

                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value

    return exif_data

def _convert_to_degress(value):
    """Helper function to convert the GPS coordinates stored in the EXIF to degress in float format"""
    deg_num, deg_denom = value[0]
    d = float(deg_num) / float(deg_denom)

    min_num, min_denom = value[1]
    m = float(min_num) / float(min_denom)

    sec_num, sec_denom = value[2]
    s = float(sec_num) / float(sec_denom)

    return d + (m / 60.0) + (s / 3600.0)

def get_lat_lon(exif_data, debug=False):
    """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)"""
    lat = None
    lon = None

    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]

        gps_latitude = gps_info.get("GPSLatitude")
        gps_latitude_ref = gps_info.get('GPSLatitudeRef')
        gps_longitude = gps_info.get('GPSLongitude')
        gps_longitude_ref = gps_info.get('GPSLongitudeRef')

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = _convert_to_degress(gps_latitude)
            if gps_latitude_ref != "N":
                lat *= -1

            lon = _convert_to_degress(gps_longitude)
            if gps_longitude_ref != "E":
                lon *= -1
    else:
        if debug:
            print("No EXIF data")

    return lat, lon

def getLatLon(image_bytes, debug=False):
    try:
        ioBuffer = io.BytesIO(image_bytes)
        image = Image.open(ioBuffer)
        exif_data = get_exif_data(image)
        return get_lat_lon(exif_data, debug)
    except Exception as inst:
        print("GetLatLon function")
        print(inst)
        return None

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
    If successful, it gets the license plates in the image, stores them in Redis
    database 1 as a hash:license plate/geocoordinate dictionary key-value pair.
    It then stores the plate:hash-list key value pair in Redis database 3. It also sends
    error or success messages to the logs.

    Parameters:
    - body(jsonpickle object): The body of the request. In this case, a JSON with
    the MD5 hash value and the bytes of the image.

    """
    data = jsonpickle.decode(body)
    try:
        redis_dict = get_license_plates(data["image"])
        send_to_redis(data["hash"], jsonpickle.encode(redis_dict), 1)
        if redis_dict["plates"]:
            for plate in redis_dict["plates"]:
                hash_list = get_from_redis(plate["plate"], 3)
                if hash_list is None:
                    send_to_redis(plate["plate"], jsonpickle.encode([data["hash"]]), 3)
                else:
                    hash_list = jsonpickle.decode(hash_list)
                    hash_list.append(data["hash"])
                    send_to_redis(plate["plate"], jsonpickle.encode(hash_list), 3)
                send_to_logs("Image Processed (Hash): " +data["hash"]+ ", Status: success, Plate: "+plate["plate"]+ ", Worker: " + socket.gethostname())
        else:
            send_to_logs("Image Processed (Hash): " +data["hash"]+ ", Status: success, Plate: none, Worker: " + socket.gethostname())
    except Exception as inst:
        send_to_logs("Image Processed (Hash): " +data["hash"]+ ", Status: failure, Error: "+inst+ ", Worker: " + socket.gethostname())
    ch.basic_ack(delivery_tag=method.delivery_tag)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)

#print(' [*] Waiting for messages. To exit press CTRL+C')

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)
channel.start_consuming()

