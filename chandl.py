#!/usr/bin/env python2.7

import argparse
import copy
import errno
import json
import os
import re
import requests
import urlparse
import threading
import time

board = None
chan = None
dest = None
ext = None
hashlist = None
thread = None

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
    global board, chan, dest, ext, thread

    filename = post["filename"]
    extension = post["ext"]

    if not "*" in ext:
        if not any(e in extension for e in ext):
            return

    if chan == "8chan":
        url = "https://8ch.net/%s/src/%s" % (board, str(post["tim"]) + extension)
    else:
        url = "https://i.4cdn.org/%s/%s" % (board, str(post["tim"]) + extension)
    path = os.path.join(dest, filename + extension)
    if not os.path.isfile(path):
        print "Downloading: " + url
        with open(path, "wb") as file:
            file.write(requests.get(url).content)

def main():
    global board, dest, ext, hashlist, thread

    parser = argparse.ArgumentParser()
    parser.add_argument('url', help="The URL of the thread you want to download")
    parser.add_argument('-d', "--destination", default=".", help="Where the files are to be stored.")
    parser.add_argument('-ext', "--extension", default="*", help="What file extensions to download, format: ext1,ext2;...")
    parser.add_argument('-t', "--threads", default=1, help="How many theads to use", type=int)
    args = parser.parse_args()

    dest = args.destination
    threadcount = args.threads
    ext = str(args.extension).lower().split(',')

    board, thread = parse_url(args.url)

    if thread.endswith(".html"): 
        thread = thread.replace(".html", ".json")
    elif not thread.endswith(".json"):
        print "URL is invalid, please check!"
        exit(-1)

    print "Downloading thread data"
    r = requests.get(thread)
    print "done"

    datapath = os.path.join(dest, ".chandl")
    try:
        os.mkdir(datapath)
    except os.error, e:
        if e.errno != errno.EEXIST:
            raise

    if not os.path.exists(os.path.join(datapath, "hashlist")):
        open(os.path.join(datapath, "hashlist"), 'w').close()

    # Read hashlist
    with open(os.path.join(datapath, "hashlist"), "r") as f:
        hashlist = f.readlines()

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

    # Serialize hash list
    with open(os.path.join(datapath, "hashlist"), "w") as f:
        for hash in hashlist:
            f.write("%s\n" % str(hash))

if __name__ == "__main__":
    main()
