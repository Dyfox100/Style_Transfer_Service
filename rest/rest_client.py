
import argparse
import io
import json
import jsonpickle
from PIL import Image
import requests


def upload_pics(address, content_file_path, style_file_path):

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

def main(server_address, endpoint, content_file, style_file):
    address = 'http://'+server_address+':5000'

    if endpoint == "image":
        address += '/image'
        response = upload_pics(address, content_file,
                               style_file).json()
        while response is None:
            pass
        print(response)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Makes calls to style transfer service. \
        Returns image hash, which can be used to retrieve image with style transfered.")

    parser.add_argument('server_address',
                        type=str,
                        help='Address of the server.')

    parser.add_argument('content_file',
                        type=str,
                        help='The file to transform.')

    parser.add_argument('style_file',
                        type=str,
                        help='The source file for the style.')

    parser.add_argument('endpoint',
                        type=str,
                        default="image",
                        help='The endpoint of the server to query.')

    args = parser.parse_args()

    main(args.server_address, args.endpoint, args.content_file,
         args.style_file)
