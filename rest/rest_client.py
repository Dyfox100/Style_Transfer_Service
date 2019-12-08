
import argparse
import io
import json
import jsonpickle
from PIL import Image
import requests


def upload_pics(address, content_file_path, style_file_path, iterations):
    address += '/image/' + str(iterations)
    #get raw image from content file and style file
    byte_stream = io.BytesIO()
    content_image = Image.open(content_file_path)
    content_image.save(byte_stream, format='JPEG')
    content_bytes = byte_stream.getvalue()

    byte_stream = io.BytesIO()
    style_image = Image.open(style_file_path)
    style_image.save(byte_stream, format="JPEG")
    style_bytes = byte_stream.getvalue()

    data = {"style":style_bytes , "content":content_bytes}

    return requests.put(address, data=jsonpickle.encode(data))

def get_pics(address, hash):
    response = requests.get(address + '/image/' + hash)
    while response is None:
        pass
    if 'message' in response.json():
        print(response.json())
        return response.json()['message']
    data = jsonpickle.decode(response.content)
    byte_stream = io.BytesIO()
    byte_stream.write(data['image'])
    image = Image.open(byte_stream)
    image.save(hash + '.jpg', format='JPEG')
    print('Image finished saving')


def main(server_address, endpoint, iterations, content_file=None, style_file=None, hash=None):
    address = 'http://'+server_address+':5000'
    if endpoint == 'transformed':
        get_pics(address, hash)

    if endpoint == "image":
        response = upload_pics(address, content_file,
                               style_file, iterations).json()
        while response is None:
            pass

        print(response)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Makes calls to style transfer service. \
        Returns image hash, which can be used to retrieve image with style transfered.")

    parser.add_argument('server_address',
                        type=str,
                        help='Address of the server.')

    parser.add_argument('endpoint',
                        type=str,
                        help='The endpoint of the server to query. Either image or transformed.')
    parser.add_argument('iterations',
                        type=int,
                        default=100,
                        help="The number of epochs of training of nural net for style transfer")

    parser.add_argument('-content_file',
                        default=None,
                        type=str,
                        help='The file to transform.')

    parser.add_argument('-style_file',
                        default=None,
                        type=str,
                        help='The source file for the style.')

    parser.add_argument('-hash',
                        default=None,
                        type=str,
                        help='Image hash to get a transformed image.')


    args = parser.parse_args()
    main(args.server_address, args.endpoint,args.iterations, args.content_file,
         args.style_file, args.hash)
