# visual_transfer

## A bit of context
This tool is a kind of [Sneakernet](https://en.wikipedia.org/wiki/Sneakernet). I started this as a proof of concept,
trying to see how to exfiltrate data from a computer when you have no network of course (or when any file transfer is
unavalaible), but also no USB, Bluetooth or whatever mean to interact with this host apart from a screen and a keyboard.
Then, you need to think creatively: what are the other way of getting data. [Sound](http://www.whence.com/minimodem/)
might be a way to go. But imagine you want to get data out of a bastion host you can only get a terminal onto (either
graphic or text).

The only available channel remaining is this particular terminal. So you just have somehow to channel your data in a
picture (or stream of pictures) and record it on the other side. This would have to be reliable though, so any lossy
encoding has to be avoided. Actually, it does ring a bell: you do that every time you read a QR-code on your smartphone...

Then why not split your file in as many chunks as needed, encode each chunk in a QR-code, and display them on the screen.
On the other end, you can extract the data out of each QR-code and stitch them together to get the original file. This is
the basic idea, and after a bit of polishing, I have my PoC!

## Transfer principles

As exposed above, the original file is splitted in chunks. The sender sends within each QRcode a header and the payload
(the chunk content, as binary). The header is 15-byte long and consists in three fields:

|M|CSEQ|SIZE    |
|-|----|--------|
|1|1234|12345678|

- the transfer mode (full/0 or partial/1),
- the chunk sequence number (4 bytes),
- the total file size (8 bytes).

There is a waste of bits for the first field: let's assume this is on purpose, for future use. The header and payload
are concatenated and encoded in base32 (with the '=' sign replaced by a '#'), before being encoded in the QR-code in
alphanumeric mode (thus the '='/'#' shenanigan to cope with the two different alphabets). Binary mode is not a
reliable solution because of the decoders that often choke on pure binary data. All this is then a tradeoff to put as
much data as possible inside a single QR-code.

Based on all this, you should choose the version and the EC level of the QR-code based on your hardware (screen size,
webcam quality, etc.) but also to accomodate for this header, meaning that, for high and quartile EC level, any version
greater than 3 is sufficient, and for medium and low, any version greater than 2.

There is also obviously a structural limit to the size of the file you can transfer. First, as the size is encoded on 64
bits, you are limited by this, but this should not be too much of an issue. Secondly, the chunk sequence number on 32
bits also limits the total size, depending essentially on the version and EC level of the QR-code. For instance, with a
v10 'L' QR-code, you can transfer up to 920GB. If you use v25 instead, you will be able to transfer up to 4.5TB.

## The sender

    usage: sender.py [-h] [-e {L,l,7%,0.7,M,m,15%,0.15,Q,q,25%,0.25,H,h,30%,0.3}]
                     [-m {full,partial}] [-c CHUNK_NB [CHUNK_NB ...]]
                     [-v VERSION | -s SIZE]
                     INPUT_FILE

    positional arguments:
        INPUT_FILE            Input file to be transfered

    optional arguments:
        -h, --help            show this help message and exit
        -e {L,l,7%,0.7,M,m,15%,0.15,Q,q,25%,0.25,H,h,30%,0.3}, --error-correction {L,l,7%,0.7,M,m,15%,0.15,Q,q,25%,0.25,H,h,30%,0.3}
                              Error correction level (default: L)
        -m {full,partial}, --mode {full,partial}
                              Transfer mode (default: full)
        -c CHUNK_NB [CHUNK_NB ...], -chunks CHUNK_NB [CHUNK_NB ...]
                              Chunks list in partial mode
        -v VERSION, --version VERSION
                              Version number of the QR-code (default: 20)
        -s SIZE, --size SIZE  Size of the QR-code

You can set the different parameters of the QR-code (size or version, error correction). The transfer will start right
after you launch the command: a fullscreen window will appear and display the stream of codes. In partial mode, only the
specified chunks are transfered.

After a few tests, I reckon I'm limited to version 25. I guess this is due to the resolution of the webcam on my laptop.
I will need to do some other tests as soon as I get a hand on a better webcam. I also tried with a sport camera, but it
doesn't bring any improvements (even if the resolution is supposed to be better). Maybe the wide-angle lens doesn't help.

## The receiver

    usage: receiver.py [-h] OUTPUT_FILE

    positional arguments:
        OUTPUT_FILE  Output file

    optional arguments:
        -h, --help  show this help message and exit

On the receiver, you just have to give the output file. After you launch the command, a window appear to give you the
opportunity to set the image capture by the webcam correctly: try to get as much of the other side screen, to improve
the quality of the transfer. As soon as the start of the transfer is detected, the window is closed. You can stop the
transfer before completion by hitting Ctrl+C. At the end of the transfer, a list of missed chunks (if any) is provided.
You can transfer those ones by starting again the sender in partial mode.
