from __future__ import print_function
import requests
import json
import argparse
import time
from statistics import mean
import redis
import os.path

def upload_pics(address, content_file, style_file, output_file):
    files = {"style": open(style_file, "rb"), "content": open(content_file, "rb")}
    r = requests.post('http://httpbin.org/post', files=files)
    #headers = {'content-type': 'image/png'}
    #img = open(image_file, 'rb').read()
    image_url = address + '/image/'+os.path.basename(content_file)
    return requests.put(image_url, files=files)#, headers=headers)

def main(server_address, endpoint, content_file, style_file, output_file):
    address = 'http://'+server_address+':5000'

    if endpoint == "image":
        response = upload_pics(address, content_file,
                               style_file, output_file).json()
        print(response)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="REST API")

    parser.add_argument('server_address',
                        type=str,
                        help='Address of the server ex. localhost')

    parser.add_argument('endpoint',
                        type=str,
                        help='The endpoint of the server we wish to query')

    parser.add_argument('--content_file',
                        type=str,
                        help='The file we wish to transform')

    parser.add_argument('--style_file',
                        type=str,
                        help='The source file for the style')

    parser.add_argument('--output_file',
                        type=str,
                        help='The output file for the transformed image')

    args = parser.parse_args()
    main(args.server_address, args.endpoint, args.content_file,
         args.style_file, args.output_file)
