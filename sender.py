#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et:


import io
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from base64 import b64encode
from os.path import getsize
from time import sleep

import cv2
import numpy
import pyqrcodeng
from barcode import Code128
from barcode.writer import ImageWriter


def create_qrcode(data):
    return pyqrcodeng.create(data, error=ec_lvl, version=qr_version, mode='binary')

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
    Parser.add_argument("-t", "-terminal", action="store", metavar="OUTPUT",
                        choices = ("text", "graphic"), default='graphic',
                        help="Terminal type")
    group = Parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--version", dest="version", action="store",
                       type=int, default=40,
                       help="Version number of the QR Code (default: %(default)d)")
    group.add_argument("-s", "--size", dest="size", action="store",
                       type=int, help="Size of the QR Code")
    Args = Parser.parse_args()

    if Args.size:
        qr_version = max(int((Args.size - 17)/4), 1)
    else:
        qr_version = Args.version
    ec_lvl = Args.ec_lvl

    # 4 for binary
    chunk_size = pyqrcodeng.tables.data_capacity[qr_version][ec_lvl][4]
    total_size = getsize(Args.input_file)
    total_chunks = (total_size-1)//chunk_size + 1
    #print(chunk_size, total_size, total_chunks)

    # Setup fullscreen window to display the QR/bar-code
    cv2.namedWindow("Image", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Image", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Send control frame to ensure proper start at the other end
    buffer = io.BytesIO()
    qrcode = create_qrcode("---START---#{}#{}".format(total_chunks, chunk_size).encode('ascii'))
    qrcode.png(buffer, scale=2)
    show_image(buffer)

    with open(Args.input_file, mode='rb') as f:
        chunk = total_chunks
        while chunk > 0:
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
