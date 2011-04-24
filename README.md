
**i wrote this tool ages ago for educational purposes. the code is a hack, do
not use it for something serious, it may break something.**

ymap is command line tool written in python to upload and download yenc encoded
files to and from imap folders.

what is and why yenc?  binary attachments for email messages are usually
encoded using base64, which has a big overhead. yenc is an alternative encoding
scheme with less overhead, see http://en.wikipedia.org/wiki/YEnc for more
information.

requirements:

* python 2.6
* yenc module for python: http://www.golug.it/yenc.html

usage:

copy the example configuration file ymap.cfg.example to your home directory and
rename it to .ymap.cfg.  modify the file and put your imap server credentials
in there. you can define multiple server profiles if you want. each ini-section
specifies a different profile.

to switch to a profile type:

    ymap profile default

to yencode and upload a file to your server type:

    ymap put example.file

to get a file list type:

    ymap list

each file is prepended with a number. to download file number 1 type:

    ymap get 1


written by sebastian volland

