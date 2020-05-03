#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et:


from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from base64 import b32decode

import cv2
from pyzbar.pyzbar import ZBarSymbol, decode


def decode_data(data):
    content = b32decode(data.decode('ascii').replace('%', '=').encode('ascii'))
    cursor = 0
    header = {}
    for k,size in header_size.items():
        header[k] = int.from_bytes(content[cursor:cursor+size], 'big')
        cursor += size
    payload = content[cursor:]

    return header, payload


if __name__ == '__main__':

    Parser = ArgumentParser()
    Parser.add_argument("output_file", action="store", metavar='OUPUT_FILE',
                        help="Output file")
    Args = Parser.parse_args()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)
    #cap.set(cv2.CAP_PROP_FPS, 24)
    #cap.set(cv2.CAP_PROP_AUTO_WB, 1)
    return_val, frame = cap.read()

    header_size = { 'mode': 1, 'chunk': 4 , 'size': 8 }
    chunk_size = 0
    total_chunks = 0
    remaining_size = 0
    chunk_seq = 0
    old_chunk_seq = 0
    mode = False
    missing_chunks = []
    started = False
    f = None

    while return_val:
        return_val, frame = cap.read()
        decoded_objects = decode(frame, symbols=[ZBarSymbol.CODE128, ZBarSymbol.QRCODE])

        if not started:
            cv2.imshow("Preview", frame)
            cv2.waitKey(100)

        for a in decoded_objects:
            if a.type != 'QRCODE':
                continue

            started = True
            header, payload = decode_data(a.data)

            chunk_seq = header['chunk']
            chunk_size = len(payload)
            if not total_chunks:
                total_chunks = (header['size']-1)//chunk_size + 1

            mode = header['mode']
            if not f:
                if mode:
                    f = open(Args.output_file, mode='r+b')
                else:
                    f = open(Args.output_file, mode='wb')

            if mode:
                if old_chunk_seq == chunk_seq:
                    continue
                print("QRCode #%d OK %d" % (header['chunk'], remaining_size))
                old_chunk_seq = chunk_seq
                f.seek((total_chunks-chunk_seq)*chunk_size)
            else:
                if old_chunk_seq-chunk_seq > 1:
                    for i in range(old_chunk_seq-1, chunk_seq, -1):
                        missing_chunks.append(i)
                        remaining_size -= chunk_size
                        f.write(b'0'*chunk_size)
                    old_chunk_seq = chunk_seq
                elif old_chunk_seq == chunk_seq: # QRCode captured twice
                    continue
                else: #if old_chunk_seq-chunk_seq == 1:
                    print("QRCode #%d OK %d" % (header['chunk'], remaining_size))
                    old_chunk_seq = chunk_seq

            if remaining_size and started:
                remaining_size -= chunk_size
            elif chunk_size:
                remaining_size = header['size'] - chunk_size
            f.write(payload)

        if started and not chunk_seq:
            break


    if f:
        f.truncate(header['size'])
        f.close()
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

    if remaining_size != 0 and not mode:
        print('File not fully received (%d missing bytes): some chunks might also be missing at the beginning of the transfer.' % (remaining_size, ))
    if missing_chunks:
        print('Missing chunks:', missing_chunks)
