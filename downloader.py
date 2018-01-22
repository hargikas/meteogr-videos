#!/usr/bin/env python3
from bs4 import BeautifulSoup
from datetime import datetime
import concurrent.futures
import mimetypes
import requests
import hashlib
import os.path
import shutil
import os

INDEX_URL = 'http://meteo.gr/webcameras.cfm'
DOWNLOAD_FOLDER = '/media/pi/TIMELAPSE/'

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chuck in iter(lambda: f.read(4096), b""):
            hash_md5.update(chuck)
        return hash_md5.hexdigest()

def get_photos(session, url):
    photos = {}
    r = session.get(url)
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
    output = ""
    
    # Create the place directory
    place_dir = os.path.join(folder, name)
    if not os.path.exists(place_dir):
        os.makedirs(place_dir)

    # Find the latest image
    files = sorted([i for i in os.listdir(place_dir)
                if os.path.isfile(os.path.join(place_dir, i))])

    r = session.get(url, stream=True)
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

        if ((len(files) > 0) and
                (md5(os.path.join(place_dir, files[-1])) == md5(filename))):
            os.remove(filename)
            output = "Not Downloaded. Latest Image: %s" % (files[-1])
        else:
            output = "Downloaded as: %s" % (os.path.basename(filename))

    return output


def main():
    # Initialize the mimetypes in order not to create more IO 
    # in the worker threads
    mimetypes.init()

    with requests.Session() as s:
        print("Querying Index Page: %r" % (INDEX_URL))
        photos = get_photos(s, INDEX_URL)
        print("Got %d indexes" % (len(photos)))
        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = {executor.submit(download_latest_photo, s,
                DOWNLOAD_FOLDER, i, photos[i]): i for i in photos
                if photos[i] is not None}
            for future in concurrent.futures.as_completed(threads):
                name = threads[future]
                try:
                    output = future.result()
                except Exception as exc:
                    print("%s: EXCEPTION: %s" % (name, exc))
                else:
                    print("%s: %s" % (name, output))

if __name__ == '__main__':
    main()
