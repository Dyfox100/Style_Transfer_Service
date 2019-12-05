FROM ubuntu:bionic-20191029
RUN apt-get update && \
    apt install wget && \
    apt install -y python3-flask && \
    pip3 install pika && \
    pip3 install jsonpickle && \
    pip3 install redis && \
    mkdir style_rest

WORKDIR /style_rest
ADD rest_server.py rest_server.py
EXPOSE 5000
RUN chmod 777 rest_server.py
CMD python3 rest-server.py
