#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et:


from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from base64 import b32decode
from time import sleep

import cv2
from pyzbar.pyzbar import ZBarSymbol, decode


def decode_data(data):
    try:
        content = data.decode('ascii').replace('%', '=')
        return b32decode(content.encode('ascii'))
    except:
        return b''


if __name__ == '__main__':

    Parser = ArgumentParser()
    Parser.add_argument("output_file", action="store", metavar='OUPUT_FILE',
                        help="Output file")
    Args = Parser.parse_args()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
    #cap.set(cv2.CAP_PROP_FPS, 24)
    #cap.set(cv2.CAP_PROP_AUTO_WB, 1)
    return_val, frame = cap.read()

    chunk_size = 0
    chunk_seq = 0
    old_chunk_seq = 0
    mode = ''
    missing_chunks = []
    started = False
    expect_control_frame = True

    while return_val:
        return_val, frame = cap.read()
        decoded_objects = decode(frame, symbols=[ZBarSymbol.CODE128, ZBarSymbol.QRCODE])

        #if decoded_objects:
            #print(decoded_objects[0].data)

        if not started:
            cv2.imshow("Preview", frame)
            cv2.waitKey(100)

            for a in decoded_objects:
                if a.type == 'QRCODE':
                    start_frame = decode_data(a.data).decode('ascii').split('#')
                    if start_frame[0] == '---START---':
                        print("START OK")
                        mode = 'full'
                        total_chunk = int(start_frame[1])
                        chunk_size = int(start_frame[2])
                        chunk_seq = total_chunk
                        started = True
                        expect_control_frame = True
                        f = open(Args.output_file, mode='wb')
                    elif start_frame[0] == '---PARTIAL---':
                        print("PARTIAL OK")
                        mode = 'partial'
                        total_chunk = int(start_frame[1])
                        chunk_size = int(start_frame[2])
                        chunk_seq = total_chunk
                        started = True
                        expect_control_frame = True
                        f = open(Args.output_file, mode='wb+')
        else:
            for a in decoded_objects:
                if a.type == 'CODE128' and expect_control_frame:
                    chunk_seq = int(a.data)
                    print("Barcode #%d OK %r" % (chunk_seq, expect_control_frame))
                    if mode == 'partial':
                        f.seek((total_chunk-chunk_seq)*chunk_size)
                        expect_control_frame = False
                    else:
                        if old_chunk_seq - chunk_seq > 1:
                            for i in range(old_chunk_seq, chunk_seq, -1):
                                missing_chunks.append(i)
                                f.write(b'0'*chunk_size)
                            old_chunk_seq = chunk_seq
                            expect_control_frame = False
                        elif old_chunk_seq == chunk_seq:
                            expect_control_frame = True
                        else:
                            old_chunk_seq = chunk_seq
                            expect_control_frame = False
                elif a.type == 'QRCODE' and not expect_control_frame:
                    print("QRCODE OK %r" % (expect_control_frame,))
                    f.write(decode_data(a.data))
                    expect_control_frame = True
                else:
                    sleep(0.1)

            if not chunk_seq:
                break


    if f:
        f.close()
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

    print('Missing chunks:', missing_chunks)

