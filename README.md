# ChanDL

Downloads files of a 4chan/8chan into a folder with multithreading.

## Installation

You need to install the requests module

>pip install requests

## Usage
>chandl.py URL -d [destination] -ext [extensions]


URL can be a 4chan or 8chan thread link such as 


http://boards.4chan.org/wsg/thread/738403/anime-thread-1730


or


http://8ch.net/wsg/res/45.html


Example: Download all .webm files of some thread


~/Pictures/Anime - is the folder where the files will be stored
>chandl.py http://boards.4chan.org/wsg/thread/738403/anime-thread-1730 -d ~/Pictures/Anime -ext webm

You can also download all extensions by leaving the -ext parameter out.


The program collects the MD5 hashes supplied by the API and uses them to skip files that already exist in the folder.

## Extra Options

### -t COUNT
Specifies amount of threads to use, defaults to 1.
The image list is divided into equal chunks and a thread is created for each chunk.
