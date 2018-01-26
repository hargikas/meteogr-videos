#!/usr/bin/env python3
from datetime import datetime
import concurrent.futures
import mimetypes
import hashlib
import shutil
import errno
import os.path
import os

import requests
from PIL import Image
from bs4 import BeautifulSoup
from tendo import singleton
import fire

INDEX_URL = 'http://meteo.gr/webcameras.cfm'
TIMEOUT = 30

def md5(fname):
    """Calculate the md5 sum of a file"""
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chuck in iter(lambda: f.read(4096), b""):
            hash_md5.update(chuck)
        return hash_md5.hexdigest()

def silentremove(fname):
    """Remove a file and supress any errors if the file doesn't exist"""
    if fname is not None:
        try:
            os.remove(fname)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

def verify_photo(fname):
    """Guess if the file is a corrupted image or not"""
    try:
        with Image.open(fname) as image:
            image.verify()
        with Image.open(fname) as image:
            image.load()
    except:
        return False
    return True

def get_photos(session, url):
    """Query the index page (url) for the meteo images"""
    photos = {}
    r = session.get(url, timeout=TIMEOUT)
    soup = BeautifulSoup(r.text[:], 'html.parser')
    for table in soup.find_all('table'):
        class_attrs = table.get('class')
        if ((class_attrs is not None) and 
                (set(class_attrs) == set(['table',
                    'table-striped', 'table-bordered']))):
            headers = True
            for row in table.find_all('tr'):
                if headers:
                    places = []
                else:
                    images = []
                for col in row.find_all('td'):
                    if headers:
                        places.append(str(col.string).strip())
                    else:
                        for img in col.find_all('img'):
                            images.append(img.get('src'))

                if not headers:
                    for i in range(len(places)):
                        if images[i] is not None:
                            photos[places[i]] = images[i]

                headers = not headers
    return photos

def download_latest_photo(session, folder, name, url):
    """Downloads the latest photo in the folder"""
    download_errors = False
    output = ""
    
    # Create the place directory
    place_dir = os.path.join(folder, name)
    if not os.path.exists(place_dir):
        os.makedirs(place_dir)

    # Find the latest image
    files = sorted([i for i in os.listdir(place_dir)
                if os.path.isfile(os.path.join(place_dir, i))])

    filename = None
    try:
        r = session.get(url, stream=True, timeout=TIMEOUT)
        if r.status_code == 200:
            ext = mimetypes.guess_extension(r.headers.get('content-type'))
            filename = os.path.join(place_dir,
                    datetime.utcnow().strftime('%Y%m%d%H%M%S'))
            if ext is not None:
                if ext in ['.jpe', '.jpeg']:
                    ext = '.jpg'
                filename = filename + ext
            with open(filename, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            download_errors = True
            output = "Error Status Code: %d" % (r.status_code)
    except requests.exceptions.RequestException as e:
        download_errors = True
        output = "Error downloading. %s" % (e)

    if (not download_errors) and (not verify_photo(filename)):
        download_errors = True
        output = "Error downloading. Not a valid image."

    if not download_errors:
        if ((len(files) > 0) and
                (md5(os.path.join(place_dir, files[-1])) == md5(filename))):
            silentremove(filename)
            output = "Not Downloaded. Latest Image: %s" % (files[-1])
        else:
            output = "Downloaded as: %s" % (os.path.basename(filename))
    else:
        silentremove(filename)

    return output


def start(folder, url=INDEX_URL, only=None, exclude=[]):
    """The main process, of quering the index page and create
    a thread for each photo."""
    # Initialize the mimetypes in order not to create more IO in the worker
    # threads
    mimetypes.init()

    with requests.Session() as s:
        print("Querying Index Page: %r" % (url))
        photos = get_photos(s, INDEX_URL)
        print("Got %d indexes" % (len(photos)))

        # If only parameter is specified, then download only this place
        if only is not None:
            tmp = {}
            if only in photos:
                tmp[only] = photos[only]
            photos = tmp

        # Delete all the files for the excluded files
        if len(exclude) > 0:
            tmp = {}
            for item in exclude:
                for key in photos:
                    if key != item:
                        tmp[key] = photos[key]
            photos = tmp

        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = {executor.submit(download_latest_photo, s,
                folder, i, photos[i]): i for i in photos
                if photos[i] is not None}
            for future in concurrent.futures.as_completed(threads):
                name = threads[future]
                try:
                    output = future.result()
                except Exception as exc:
                    print("%s: EXCEPTION: %s" % (name, exc))
                else:
                    print("%s: %s" % (name, output))


def main():
    me = singleton.SingleInstance()
    fire.Fire(start)


if __name__ == '__main__':
    main()
