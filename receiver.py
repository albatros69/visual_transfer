#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et:


from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from time import sleep

import cv2
from pyzbar.pyzbar import decode, ZBarSymbol


if __name__ == '__main__':

    Parser = ArgumentParser()
    Parser.add_argument("output_file", action="store", metavar='INPUT_FILE',
                        help="Output file")
    Args = Parser.parse_args()

    cap = cv2.VideoCapture(0)
    return_val, frame = cap.read()
    
    with open(Args.output_file, mode='wb') as f:
        chunk_size = 0
        chunk_seq = 0
        old_chunk_seq = 0
        missing_chunks = []
        started = False
        expect_control_frame = True
        
        while return_val:
            return_val, frame = cap.read()
            decoded_objects = decode(frame, symbols=[ZBarSymbol.CODE128, ZBarSymbol.QRCODE])

            if decoded_objects:
                print(decoded_objects[0].type, decoded_objects[0].data[:10])

            if not started:
                for a in decoded_objects:
                    if a.type == 'QRCODE':
                        start_frame = a.data.decode('ascii').split('#')
                        if start_frame[0] == '---START---':
                            print("START OK")
                            chunk_seq = int(start_frame[1])
                            chunk_size = int(start_frame[2])
                            started = True
                            expect_control_frame = True
                    # else:
                    #     sleep(0.1)
            else:
                for a in decoded_objects:
                    if a.type == 'CODE128' and expect_control_frame:
                        chunk_seq = int(a.data)
                        print("Barcode #%d OK" % (chunk_seq, ))
                        if old_chunk_seq - chunk_seq > 1:
                            for i in range(old_chunk_seq, chunk_seq, -1):
                                missing_chunks.append(i)
                                f.write(b'0'*chunk_size)
                        old_chunk_seq = chunk_seq
                        expect_control_frame = False
                    elif a.type == 'QRCODE' and not expect_control_frame:
                        print("QRCODE OK")
                        f.write(a.data)
                        expect_control_frame = True
                    # else:
                    #     sleep(0.1)
                
                if not chunk_seq:
                    break
            
            cv2.imshow("Preview", frame)
            cv2.waitKey(100)
    
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
    
    print('Missing chunks:', missing_chunks)