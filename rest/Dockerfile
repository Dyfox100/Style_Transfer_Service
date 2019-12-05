FROM tensorflow/tensorflow:1.15.0-gpu-py3
RUN apt-get update && \
    apt install wget && \
    apt install -y python3-flask && \
    pip install scipy==1.1 && \
    pip install pillow && \
    mkdir style_files

WORKDIR /style_files
RUN wget http://www.vlfeat.org/matconvnet/models/imagenet-vgg-verydeep-19.mat
ADD stylize.py stylize.py
ADD vgg.py vgg.py
ADD neural_style.py neural_style.py
#ADD rest_server.py rest_server.py
ADD ../examples/1-content.jpg 1-content.jpg
ADD ../examples/1-style.jpg 1-style.jpg
EXPOSE 5000
RUN chmod 777 stylize.py && chmod 777 vbb.py && chmod 777 neural_style.py
CMD python neural_style.py --content 1-content.jpg --styles 1-style.jpg --output test.jpg --iterations 50
