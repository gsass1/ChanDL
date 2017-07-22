#!/usr/bin/env python2.7

#    DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#                    Version 2, December 2004
#
# Copyright (C) 2017 Gian Sass <gian.sass@outlook.de>
#
# Everyone is permitted to copy and distribute verbatim or modified
# copies of this license document, and changing it is allowed as long
# as the name is changed.
#
#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
#
#  0. You just DO WHAT THE FUCK YOU WANT TO.

import argparse
import base64
import copy
import errno
import hashlib
import json
import os
import re
import requests
import urlparse
import threading
import time

board = None
chan = None
datapath = None
dest = None
ext = None
hashlist = []
thread = None
orig_filenames = False

# Split a sequence into num chunks
def chunks(seq, num):
    avg = len(seq) / float(num)
    last = 0.0

    while last < len(seq):
        yield seq[int(last):int(last + avg)]
        last += avg

def parse_url(url):
    global chan

    parseurl = urlparse.urlparse(url)
    urldef = parseurl[2].split("/")[1:]

    board = urldef[0]

    if urldef[1] == "thread":
        chan = "4chan"
    elif urldef[1] == "res":
        chan = "8chan"
    else:
        chan = None

    if chan == "4chan" and len(urldef) == 4:
        del urldef[3]

    if chan == "8chan":
        threadurl = "https://8ch.net/"
    else:
        threadurl = "https://a.4cdn.org/"

    threadurl += "/".join(urldef)

    if threadurl.endswith(".html"): 
            threadurl = threadurl.replace(".html", ".json")
    elif not threadurl.endswith(".json"):
        threadurl += ".json"

    return board, threadurl

def download_images_thread(images):
    for i in images:
        if not i["md5"] in hashlist:
            download_image(i)
            hashlist.append(i["md5"])

def download_image(post):
    global board, chan, dest, ext, orig_filenames, thread

    filename = post["filename"] if orig_filenames else str(post["tim"])
    extension = post["ext"]

    if not "*" in ext:
        if not any(e in extension for e in ext):
            return

    if chan == "8chan":
        url = "https://8ch.net/%s/src/%s" % (board, str(post["tim"]) + extension)
    else:
        url = "https://i.4cdn.org/%s/%s" % (board, str(post["tim"]) + extension)
    path = os.path.join(dest, filename + extension)
    if not os.path.isfile(path) and not post["md5"] in hashlist:
        print "Downloading: " + url
        with open(path, "wb") as file:
            file.write(requests.get(url).content)

def write_hashlist():
    global datapath, hashlist

    with open(os.path.join(datapath, "hashlist"), "w") as f:
        for hash in hashlist:
            f.write("%s\n" % str(hash))

def gen_md5(path):
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return base64.b64encode(hash_md5.digest()).strip()

def gen_hashlist(d):
    for f in os.listdir(d):
        if not f.lower().endswith(('.png', '.jpg', '.webm', '.jpeg', '.gif')):
            continue
        hashlist.append(gen_md5(os.path.join(d, f)))
    write_hashlist()

def main():
    global board, datapath, dest, ext, hashlist, orig_filenames, thread

    parser = argparse.ArgumentParser()
    parser.add_argument('-url', "--url", help="The URL of the thread you want to download (4chan and 8chan supported).")
    parser.add_argument('-d', "--destination", default=".", help="Where the files are to be stored.")
    parser.add_argument('-ext', "--extension", default="*", help="What file extensions to download, format: ext1,ext2;...")
    parser.add_argument('-t', "--threads", default=1, help="How many threads to utilise.", type=int)
    parser.add_argument('-w', "--watch", action='store_true', help="Continually search for new images to download.")
    parser.add_argument('-u', "--update-interval", default=60, help="Interval in seconds after which to trigger a new poll update when enabled with -w.", type=int)
    parser.add_argument('-o', "--original-filenames", action='store_true', help="Whether to use the original filename of the uploaded images.")
    parser.add_argument('-gh', "--gen-hashlist", default=None, help="Generate hashlist from directory.", type=str)
    args = parser.parse_args()

    dest = args.destination
    threadcount = args.threads
    ext = str(args.extension).lower().split(',')
    orig_filenames = args.original_filenames
    watch = args.watch
    update_interval = args.update_interval
    url = args.url

    if args.gen_hashlist is not None:
        datapath = os.path.join(args.gen_hashlist, ".chandl")
        try:
            os.mkdir(datapath)
        except os.error, e:
            if e.errno != errno.EEXIST:
                raise
        gen_hashlist(args.gen_hashlist)
        exit(0)

    if url is None:
        print "Missing url"
        exit(1)

    if update_interval <= 0:
        print "Invalid update interval"
        exit(1)

    board, thread = parse_url(url)

    if thread.endswith(".html"): 
        thread = thread.replace(".html", ".json")
    elif not thread.endswith(".json"):
        print "Invalid URL"
        exit(1)

    r = requests.get(thread)

    datapath = os.path.join(dest, ".chandl")
    try:
        os.mkdir(datapath)
    except os.error, e:
        if e.errno != errno.EEXIST:
            raise

    if not os.path.exists(os.path.join(datapath, "hashlist")):
        open(os.path.join(datapath, "hashlist"), 'w').close()
    else:
        # Read hashlist
        with open(os.path.join(datapath, "hashlist"), "r") as f:
            hashlist = [line.rstrip('\n') for line in f.readlines()]

    # Collect all images into this array
    images = []

    for post in r.json()["posts"]:
        if "filename" in post:
            images.append(copy.deepcopy(post))
        if "extra_files" in post:
            for f in post["extra_files"]:
                images.append(copy.deepcopy(f)) 

    threads = []
    for c in chunks(images, threadcount):
        t = threading.Thread(target=download_images_thread, args=(c,))
        threads.append(t)
        t.daemon = True
        t.start()

    while threading.active_count() - 1 > 0:
        time.sleep(0.1)

    for t in threads:
        t.join()

    write_hashlist()
    
    if not watch:
        exit(0)

    print "Entering watch mode (update interval = %us)" % update_interval

    while True:
        images = []

        time.sleep(float(update_interval))
        r = requests.get(thread)

        for post in r.json()["posts"]:
            if "filename" in post:
                if post["md5"] not in hashlist:
                    images.append(copy.deepcopy(post))
            if "extra_files" in post:
                for f in post["extra_files"]:
                    if post["md5"] not in hashlist:
                        images.append(copy.deepcopy(f)) 

        download_images_thread(images)
        write_hashlist()

if __name__ == "__main__":
    main()
