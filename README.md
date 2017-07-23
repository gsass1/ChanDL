# ChanDL
Downloads files of a 4chan/8chan thread into a folder with multithreading.

## Dependencies
* Python 2.7
* requests module

## Usage
```
usage: chandl.py [-h] [-url URL] [-d DESTINATION] [-ext EXTENSION]
                 [-t THREADS] [-w] [-u UPDATE_INTERVAL] [-o]
                 [-gh GEN_HASHLIST]

optional arguments:
  -h, --help            show this help message and exit
  -url URL, --url URL   The URL of the thread you want to download (4chan and
                        8chan supported).
  -d DESTINATION, --destination DESTINATION
                        Where the files are to be stored.
  -ext EXTENSION, --extension EXTENSION
                        What file extensions to download, format:
                        ext1,ext2;...
  -t THREADS, --threads THREADS
                        How many threads to utilise.
  -w, --watch           Continually search for new images to download.
  -u UPDATE_INTERVAL, --update-interval UPDATE_INTERVAL
                        Interval in seconds after which to trigger a new poll
                        update when enabled with -w.
  -o, --original-filenames
                        Whether to use the original filename of the uploaded
                        images.
  -gh GEN_HASHLIST, --gen-hashlist GEN_HASHLIST
                        Generate hashlist from directory.
```


URL can be a 4chan or 8chan thread link such as 


http://boards.4chan.org/wsg/thread/738403/anime-thread-1730


or


http://8ch.net/wsg/res/45.html


Example: Download all .webm files of some thread

~/Pictures/Anime - is the folder where the files will be stored
>chandl.py -url http://boards.4chan.org/wsg/thread/738403/anime-thread-1730 -d ~/Pictures/Anime -ext webm

You can also download all extensions by leaving the -ext parameter out.

## Hash List
The program collects the MD5 hashes supplied by the API and uses them to skip files that already exist in the folder. It stores the hash list in a file it creates called .chandl/hashlist.

If your folder already contains images and you'd like to prevent unnecessary duplicates, you can generate a hash list from a local directory as well.

Example:
>chandl.py --gen-hashlist FOLDER
