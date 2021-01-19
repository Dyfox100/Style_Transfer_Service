# Style Transfer Service
Style Transfer Service(STS) is a scalable web service to train style transfer neural nets. A style transfer neural net is a network that will transfer the "style" from one image to another. For more information on style transfer networks see [here](https://medium.com/tensorflow/neural-style-transfer-creating-art-with-deep-learning-using-tf-keras-and-eager-execution-7d541ac31398), and see examples below. 
## Usage
Each directory has start up scripts located in them. To set up the service, run all the startup scripts with access to a GCP account. Once the system is up and running, use the following steps to transfer the style of an image.
1. Get the address of the rest service.
2. Create a put request to the address of the REST service suffixed with "/image/" and the number of iterations to train the style transfer network for. Ex (35.232.96.31/image/200). In the body of this request, put the style image in the "style" attribute of the put request body and the content image in the "content" attribute.
3. Upon successfull completion of the request in part 2, a hash will be returned. The neural networks take a few minutes to train, so you use the hash to retrieve the image once the training has completed. 
4. After a few minutes, make a get request to the same address from part 1, suffixed with "/image/"with the hash returned in part 3. This will return the result image.
Alternatively, use the rest_client.py script to send requests. Usage of this script can be found in the file at rest/example_rest_client_call.txt.
## Examples
#### Content Image
![A building](https://github.com/Dyfox100/Style_Transfer_Service/blob/master/examples/2-content.jpg)

#### Style Image
![Abstract Art](https://github.com/Dyfox100/Style_Transfer_Service/blob/master/examples/2-style1.jpg)

#### Result of Style Transfer
![Result of Transfering the Style From the Abstract Art To The Building](https://github.com/Dyfox100/Style_Transfer_Service/blob/master/examples/2-output.jpg)


## Architecture
STS is built upon kubernetes, docker, redis, rabbitmq, flask, and google cloud. Each training request will be run on an instance of the worker code with a nvidia Tesla K80 gpu to facilitate training at a reasonable speed. The system will scale up to a maximum of 3 gpu instances at a time. If more than 3 concurrent training requests are issued, the requests will queue in RabbitMQ and be delt with once one of the gpu instances is free. All of the training requests are queued in RabbitMQ and will retry if the neural network fails to train. The resulting images are stored in a GCP bucket. The addresses and image hashes are stored in Redis for retrieval. See below diagram.

![Archetecture Diagram](https://github.com/Dyfox100/Style_Transfer_Service/blob/master/Data%20Flow%20Diagram.jpeg)

