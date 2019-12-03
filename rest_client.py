from __future__ import print_function
import requests
import json
import argparse
import time
from statistics import mean
import jsonpickle
#import redis
import os.path
import scipy.misc
import numpy as np

def imread(path):
    img = scipy.misc.imread(path).astype(np.float)
    if len(img.shape) == 2:
        # grayscale
        img = np.dstack((img,img,img))
    elif img.shape[2] == 4:
        # PNG with alpha channel
        img = img[:,:,:3]
    return img

def upload_pics(address, content_file, style_file, output_file):
    data = {"style": imread(style_file), "content": imread(content_file),
            "output_file": output_file}

    image_url = address + '/image/'+os.path.basename(content_file)
    return requests.put(image_url, data=jsonpickle.encode(data))

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
