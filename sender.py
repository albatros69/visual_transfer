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


def create_qrcode(data):
    content = b32encode(data).decode('ascii').replace('=', '%')
    return pyqrcodeng.create(content, error=ec_lvl, version=qr_version, mode='alphanumeric', encoding='ascii')

def show_image(buf):
    buf.flush()
    buf.seek(0)

    png = numpy.frombuffer(buf.read(), dtype=numpy.uint8)
    image = cv2.imdecode(png, cv2.IMREAD_UNCHANGED)
    cv2.imshow("Image", image)
    cv2.waitKey(700)

    buffer.seek(0)
    buffer.truncate()
   # sleep(1)


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
    Parser.add_argument("-c", "-chunks", dest="chunks", action="store", metavar="CHUNKS_LIST",
                        type=int, nargs='+', help="Chunks list in partial mode")
    group = Parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--version", dest="version", action="store",
                       type=int, default=40,
                       help="Version number of the QR Code (default: %(default)d)")
    group.add_argument("-s", "--size", dest="size", action="store",
                       type=int, help="Size of the QR Code")
    Args = Parser.parse_args()

    if Args.mode.lower() == "partial" and not Args.chunks:
        raise ArgumentError('chunks', "In partial mode, chunks list must be provided.")

    if Args.size:
        qr_version = max(int((Args.size - 17)/4), 1)
    else:
        qr_version = Args.version
    ec_lvl = Args.ec_lvl

    # 2 for alphanumeric, 4 for binary + base32 ratio
    chunk_size = pyqrcodeng.tables.data_capacity[qr_version][ec_lvl][2]*5//40*5
    total_size = getsize(Args.input_file)
    total_chunks = (total_size-1)//chunk_size + 1

    # Setup fullscreen window to display the QR/bar-code
    cv2.namedWindow("Image", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Image", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Send control frame to ensure proper start at the other end
    buffer = io.BytesIO()
    if Args.mode.lower() == 'partial':
        qrcode = create_qrcode("---PARTIAL---#{}#{}".format(total_chunks, chunk_size).encode('ascii'))
    else:
        qrcode = create_qrcode("---START---#{}#{}".format(total_chunks, chunk_size).encode('ascii'))
    qrcode.png(buffer, scale=2)
    show_image(buffer)

    with open(Args.input_file, mode='rb') as f:
        if Args.mode.lower() == "partial":
            chunks_list = Args.chunks
            chunk = len(chunks_list)
        else:
            chunk = total_chunks
        while chunk > 0:
            if Args.mode.lower() == 'partial':
                cursor = chunks_list.pop()
                barcode = Code128(str(cursor), writer=ImageWriter())
                f.tell((total_chunks-cursor)*chunk_size)

            barcode = Code128(str(chunk), writer=ImageWriter())
            barcode.write(buffer)
            show_image(buffer)

            data = f.read(chunk_size)
            qrcode = create_qrcode(data)
            qrcode.png(buffer, scale=2)
            show_image(buffer)

            chunk -= 1

        barcode = Code128(str(chunk), writer=ImageWriter())
        barcode.write(buffer)
        show_image(buffer)

    cv2.destroyAllWindows()
