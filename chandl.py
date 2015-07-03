#!/usr/bin/env python2.7

import argparse
import json
import os
import re
import requests
import urlparse

board = None
chan = None
dest = None
ext = None
thread = None

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

def download_images(post):
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
    global board, dest, ext, thread

    parser = argparse.ArgumentParser()
    parser.add_argument('url', help="The URL of the thread you want to download")
    parser.add_argument('-d', "--destination", default=".", help="Where the files are to be stored.")
    parser.add_argument('-ext', "--extension", default="*", help="What file extensions to download, format: ext1,ext2;...")
    args = parser.parse_args()

    dest = args.destination
    ext = str(args.extension).lower().split(',')

    board, thread = parse_url(args.url)

    if thread.endswith(".html"): 
        thread = thread.replace(".html", ".json")
    elif not thread.endswith(".json"):
        print "URL is invaid, please check!" 
        exit(-1)

    r = requests.get(thread)
    for post in r.json()["posts"]:
        if "filename" in post:
            download_images(post)
        if "extra_files" in post:
            for f in post["extra_files"]:
                download_images(f) 

if __name__ == "__main__":
    main()
