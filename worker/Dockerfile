FROM tensorflow/tensorflow:1.15.0-gpu-py3
RUN apt-get update && \
    apt install wget && \
    apt-get install -y python3 python3-pip python3-redis && \
    pip3 install scipy==1.1 && \
    pip3 install pika && \
    pip3 install jsonpickle && \
    pip3 install pillow && \
    mkdir style_files

WORKDIR /style_files
RUN wget http://www.vlfeat.org/matconvnet/models/imagenet-vgg-verydeep-19.mat
ADD stylize.py stylize.py
ADD vgg.py vgg.py
ADD neural_style_mod.py neural_style_mod.py
ADD worker_server.py worker_server.py
RUN pip3 install google-cloud-storage
RUN chmod 777 stylize.py && chmod 777 vgg.py && chmod 777 neural_style_mod.py && chmod 777 worker_server.py
CMD python3 worker_server.py
