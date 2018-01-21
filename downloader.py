#!/usr/bin/env python3
from bs4 import BeautifulSoup
from datetime import datetime
import threading
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
    # Mimetypes initialization
    if not mimetypes.inited:
        mimetypes.init()

    # Create the place directory
    place_dir = os.path.join(folder, name)
    if not os.path.exists(place_dir):
        os.makedirs(place_dir)

    # Find the latest image
    files = sorted([i for i in os.listdir(place_dir)
                if os.path.isfile(os.path.join(place_dir, i))])

    try:
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
            else:
                print("Downloaded %s" % (name))
    except:
        pass


def main():
    with requests.Session() as s:
        photos = get_photos(s, INDEX_URL)
        d_threads = []
        for name in sorted(photos.keys()):
            if photos[name] is not None:
                d_threads.append(threading.Thread(target=download_latest_photo,
                    args=(s, DOWNLOAD_FOLDER, name, photos[name])))
                d_threads[-1].start()
        for d_thread in d_threads:
            d_thread.join()

if __name__ == '__main__':
    main()
