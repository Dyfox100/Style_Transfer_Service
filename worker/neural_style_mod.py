# Copyright (c) 2015-2019 Anish Athalye. Released under GPLv3.
import os
import math
import re
from argparse import ArgumentParser
from collections import OrderedDict

from PIL import Image
import numpy as np
import scipy.misc
from stylize import stylize

# default arguments
CONTENT_WEIGHT = 5e0
CONTENT_WEIGHT_BLEND = 1
STYLE_WEIGHT = 5e2
TV_WEIGHT = 1e2
STYLE_LAYER_WEIGHT_EXP = 1
LEARNING_RATE = 1e1
BETA1 = 0.9
BETA2 = 0.999
EPSILON = 1e-08
STYLE_SCALE = 1.0
ITERATIONS = 100
VGG_PATH = 'imagenet-vgg-verydeep-19.mat'
POOLING = 'max'


def build_parser():
    parser = ArgumentParser()
    parser.add_argument('--iterations', type=int,
            dest='iterations', help='iterations (default %(default)s)',
            metavar='ITERATIONS', default=ITERATIONS)
    parser.add_argument('--print-iterations', type=int,
            dest='print_iterations', help='statistics printing frequency',
            metavar='PRINT_ITERATIONS')
    parser.add_argument('--checkpoint-output',
            dest='checkpoint_output',
            help='checkpoint output format, e.g. output_{:05}.jpg or '
                 'output_%%05d.jpg',
            metavar='OUTPUT', default=None)
    parser.add_argument('--checkpoint-iterations', type=int,
            dest='checkpoint_iterations', help='checkpoint frequency',
            metavar='CHECKPOINT_ITERATIONS', default=None)
    parser.add_argument('--width', type=int,
            dest='width', help='output width',
            metavar='WIDTH')
    parser.add_argument('--style-scales', type=float,
            dest='style_scales',
            nargs='+', help='one or more style scales',
            metavar='STYLE_SCALE')
    parser.add_argument('--style-blend-weights', type=float,
            dest='style_blend_weights', help='style blending weights',
            nargs='+', metavar='STYLE_BLEND_WEIGHT')
    parser.add_argument('--initial',
            dest='initial', help='initial image',
            metavar='INITIAL')
    parser.add_argument('--initial-noiseblend', type=float,
            dest='initial_noiseblend',
            help='ratio of blending initial image with normalized noise '
                 '(if no initial image specified, content image is used) '
                 '(default %(default)s)',
            metavar='INITIAL_NOISEBLEND')
    parser.add_argument('--preserve-colors', action='store_true',
            dest='preserve_colors',
            help='style-only transfer (preserving colors) - if color transfer '
                 'is not needed')
    parser.add_argument('--overwrite', action='store_true', dest='overwrite',
            help='write file even if there is already a file with that name')
    return parser


def fmt_imsave(fmt, iteration):
    if re.match(r'^.*\{.*\}.*$', fmt):
        return fmt.format(iteration)
    elif '%' in fmt:
        return fmt % iteration
    else:
        raise ValueError("illegal format string '{}'".format(fmt))


def transform(content_file, style_file, iterations):

    # https://stackoverflow.com/a/42121886
    key = 'TF_CPP_MIN_LOG_LEVEL'
    if key not in os.environ:
        os.environ[key] = '2'

    parser = build_parser()
    options = parser.parse_args()

    if not os.path.isfile(VGG_PATH):
        parser.error("Network %s does not exist. (Did you forget to "
                     "download it?)" % VGG_PATH)

    content_image = content_file
    style_images = [style_file]

    width = options.width
    if width is not None:
        new_shape = (int(math.floor(float(content_image.shape[0]) /
                content_image.shape[1] * width)), width)
        content_image = scipy.misc.imresize(content_image, new_shape)
    target_shape = content_image.shape
    for i in range(len(style_images)):
        style_scale = STYLE_SCALE
        if options.style_scales is not None:
            style_scale = options.style_scales[i]
        style_images[i] = scipy.misc.imresize(style_images[i], style_scale *
                target_shape[1] / style_images[i].shape[1])

    style_blend_weights = options.style_blend_weights
    if style_blend_weights is None:
        # default is equal weights
        style_blend_weights = [1.0/len(style_images) for _ in style_images]
    else:
        total_blend_weight = sum(style_blend_weights)
        style_blend_weights = [weight/total_blend_weight
                               for weight in style_blend_weights]

    initial = options.initial
    if initial is not None:
        initial = scipy.misc.imresize(imread(initial), content_image.shape[:2])
        # Initial guess is specified, but not noiseblend - no noise should be blended
        if options.initial_noiseblend is None:
            options.initial_noiseblend = 0.0
    else:
        # Neither inital, nor noiseblend is provided, falling back to random
        # generated initial guess
        if options.initial_noiseblend is None:
            options.initial_noiseblend = 1.0
        if options.initial_noiseblend < 1.0:
            initial = content_image

    loss_arrs = None
    for iteration, image, loss_vals in stylize(
        network=VGG_PATH,
        initial=initial,
        initial_noiseblend=options.initial_noiseblend,
        content=content_image,
        styles=style_images,
        preserve_colors=options.preserve_colors,
        iterations=iterations,
        content_weight=CONTENT_WEIGHT,
        content_weight_blend=CONTENT_WEIGHT_BLEND,
        style_weight=STYLE_WEIGHT,
        style_layer_weight_exp=STYLE_LAYER_WEIGHT_EXP,
        style_blend_weights=style_blend_weights,
        tv_weight=TV_WEIGHT,
        learning_rate=LEARNING_RATE,
        beta1=BETA1,
        beta2=BETA2,
        epsilon=EPSILON,
        pooling=POOLING,
        print_iterations=options.print_iterations,
        checkpoint_iterations=options.checkpoint_iterations,
    ):
        continue

    return image

def imread(path):
    img = scipy.misc.imread(path).astype(np.float)
    if len(img.shape) == 2:
        # grayscale
        img = np.dstack((img,img,img))
    elif img.shape[2] == 4:
        # PNG with alpha channel
        img = img[:,:,:3]
    return img

def imsave(path, img):
    img = np.clip(img, 0, 255).astype(np.uint8)
    Image.fromarray(img).save(path, quality=95)
