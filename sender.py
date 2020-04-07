#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et:


import io
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, ArgumentError
from base64 import b32encode
from os.path import getsize
from time import sleep

import cv2
import numpy
import pyqrcodeng
from barcode import Code128
from barcode.writer import ImageWriter


def create_qrcode(header, payload):
    try:
        data = b''.join([ header[k].to_bytes(header_size[k], 'big') for k in header ]) + payload
    except OverflowError:
        raise ValueError('The chosen file is too big to be transfered using these QR-code parameters.')
    content = b32encode(data).decode('ascii').replace('=', '%')
    return pyqrcodeng.create(content, error=ec_lvl, version=qr_version, mode='alphanumeric', encoding='ascii')

def show_image(buf):
    buf.flush()
    buf.seek(0)

    png = numpy.frombuffer(buf.read(), dtype=numpy.uint8)
    image = cv2.imdecode(png, cv2.IMREAD_UNCHANGED)
    cv2.imshow("Image", image)
    cv2.waitKey(200)

    buffer.seek(0)
    buffer.truncate()


if __name__ == '__main__':

    Parser = ArgumentParser()
    Parser.add_argument("input_file", action="store", metavar='INPUT_FILE',
                        help="Input file to be transfered")
    Parser.add_argument("-e", "--error-correction", dest="ec_lvl", action="store",
                        choices=pyqrcodeng.tables.error_level.keys(), default='L',
                        help="Error correction level (default: %(default)s)")
    #Parser.add_argument("-t", "--terminal", action="store", metavar="OUTPUT",
    #                    choices = ("text", "graphic"), default='graphic',
    #                    help="Terminal type")
    Parser.add_argument("-m", "--mode", dest="mode", action="store", #metavar="MODE",
                        choices=("full", "partial"), default='full',
                        help="Transfer mode (default: %(default)s)")
    Parser.add_argument("-c", "-chunks", dest="chunks", action="store", metavar="CHUNK_NB",
                        type=int, nargs='+', help="Chunks list in partial mode")
    group = Parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--version", dest="version", action="store",
                       type=int, default=40,
                       help="Version number of the QR-code (default: %(default)d)")
    group.add_argument("-s", "--size", dest="size", action="store",
                       type=int, help="Size of the QR-code")
    Args = Parser.parse_args()

    if Args.mode.lower() == "partial" and not Args.chunks:
        raise ArgumentError('chunks', "In partial mode, chunks list must be provided.")

    if Args.size:
        qr_version = max(int((Args.size - 17)/4), 1)
    else:
        qr_version = Args.version
    ec_lvl = Args.ec_lvl
    mode = Args.mode.lower() == 'partial'

    total_size = getsize(Args.input_file)
    header_size = { 'mode': 1, 'chunk': 4 , 'size': 8 }
    header = { 'mode': int(mode), 'chunk': 0 , 'size': total_size }
    # 2 for alphanumeric, 4 for binary + base32 ratio
    chunk_size = pyqrcodeng.tables.data_capacity[qr_version][ec_lvl][2]*5//40*5
    for v in header_size.values():
        chunk_size -= v
    if chunk_size <= 0:
        raise ValueError("The chosen QR-code parameters can't accomodate the header size.")
    total_chunks = (total_size-1)//chunk_size + 1
    if total_chunks > 256**header_size['chunk'] or total_size >= 256**header_size['size']:
        raise ValueError('The chosen file is too big to be transfered using these QR-code parameters.')

    # Setup fullscreen window to display the QR/bar-code
    cv2.namedWindow("Image", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Image", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    buffer = io.BytesIO()

    with open(Args.input_file, mode='rb') as f:
        if mode:
            chunks_list = sorted(Args.chunks)
            chunk = len(chunks_list)
        else:
            chunk = total_chunks

        while chunk > 0:
            if mode:
                cursor = chunks_list.pop()
                f.seek((total_chunks-cursor)*chunk_size)
                header['chunk'] = cursor
            else:
                header['chunk'] = chunk

            data = f.read(chunk_size)
            qrcode = create_qrcode(header, data)
            qrcode.png(buffer, scale=2)
            show_image(buffer)

            chunk -= 1

        header['chunk'] = 0
        qrcode = create_qrcode(header, b'')
        qrcode.png(buffer, scale=2)
        show_image(buffer)

    cv2.destroyAllWindows()
