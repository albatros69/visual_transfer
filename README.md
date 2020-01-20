# visual_transfer

## A bit of context
This tool is a kind of [Sneakernet](https://en.wikipedia.org/wiki/Sneakernet). I started this as a proof of concept,
trying to see how to exfiltrate data from a computer when you have no network of course (or when any file transfer is
unavalaible), but also no USB, Bluetooth or whatever mean to interact with this host apart from a screen and a keyboard.
Then, you need to think creatively: what are the other way of getting data. [Sound](http://www.whence.com/minimodem/)
might be way to go. But imagine you want to get data out of a bastion host you can only get a terminal onto (either
graphic or text).

The only available channel remaining is this particular terminal. So you just have somehow to channel your data in a 
picture (or stream of pictures) and record it on the other side. This would have to be reliable though, so any lossy 
encoding has to be avoided. Actually, it does ring a bell: you do that every time you read a QR-code on your smartphone...

Then why not splitting your file in as many chunks as needed, encoding each chunk in a QR-code, and display them on the
screen. On the other end, you can extract the data out of each QR-code and stitch them together to get the original file.
This is the basic idea, and after a bit of polishing, I have my PoC!

## Transfer principle

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
                              Version number of the QR-code (default: 40)
        -s SIZE, --size SIZE  Size of the QR-code

You can set the different parameters of the QR-code (size or version, error correction). The transfer will start right
after you launch the command: a fullscreen window will appear and display the stream of codes. In partial mode, only the
the specified chunks are transfered.

## The receiver

    usage: receiver.py [-h] OUTPUT_FILE

    positional arguments:
        OUTPUT_FILE  Output file

    optional arguments:
        -h, --help  show this help message and exit

On the receiver, you just have to give the output file. After you launch the command, a window appear to give you the
opportunity to set the image capture by the webcam correctly: try to get as much as the other side screen, to improve
the quality of the transfer. As soon as the start of the transfer is detected, the window is closed. You can stop the
transfer before completion by hitting Ctrl+C. At the end of the transfer, a list of missed chunks (if any) is provided.
You can start again to transfer those ones by starting again the sender in partial mode.
