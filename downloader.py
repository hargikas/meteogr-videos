#!/usr/bin/env python3
from datetime import datetime
import concurrent.futures
import mimetypes
import hashlib
import shutil
import errno
import os.path
import os


from bs4 import BeautifulSoup
from romanize import romanize
from tendo import singleton
from PIL import Image
import requests
import fire

# The main index page of web-cameras of meteo.gr
INDEX_URL = 'http://meteo.gr/webcameras.cfm'

# It's a good practice to set connect timeouts to slightly larger than a
# multiple of 3, which is the default TCP packet retransmission window.
TIMEOUT = 31

class WebCamerasLocations(object):
    def __init__(self):
        self.index = []
        self.dict = {}
        self.correlation = {}

    def __str_null_or_empty__(self, str_input):
        if not str_input:
            return False
        str_input = str_input.strip()
        return bool(str_input)

    def __find_first_empty__(self):
        for i in self.index:
            if i not in self.correlation:
                return i
        return None

    def __len__(self):
        return len([i for i in self.correlation if self.correlation[i]])

    def unique_name(self, x):
        if (type(x).__name__ == 'int'):
            if x < len(self.index):
                return self.index[x]
            return None
        else:
            if x in self.dict:
                return self.dict[x]
            return None


    def add_place_name(self, place_name):
        if self.__str_null_or_empty__(place_name):
            return
        place_name = place_name.strip()
        unique_name = '{:03d}'.format(len(self.index)) + '.' + place_name
        self.index.append(unique_name)
        if place_name not in self.dict:
            self.dict[place_name] = [] 
        self.dict[place_name].append(unique_name)

    def add_image_src(self, img):
        unique_name = self.__find_first_empty__()
        if unique_name:
            self.correlation[unique_name] = img

def md5(fname):
    """Calculate the md5 sum of a file"""
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f_p:
        for chuck in iter(lambda: f_p.read(4096), b""):
            hash_md5.update(chuck)
        return hash_md5.hexdigest()

def silentremove(fname):
    """Remove a file and supress any errors if the file doesn't exist"""
    if fname is not None:
        try:
            os.remove(fname)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

def verify_photo(fname):
    """Guess if the file is a corrupted image or not"""
    try:
        with Image.open(fname) as image:
            image.verify()
        with Image.open(fname) as image:
            image.load()
    except Exception:
        return False
    return True

def get_photos(session, url):
    """Query the index page (url) for the meteo images"""
    result = WebCamerasLocations()

    req = session.get(url, timeout=TIMEOUT)
    soup = BeautifulSoup(req.text[:], 'html.parser')
    for table in soup.find_all('table'):
        class_attrs = table.get('class')
        if ((class_attrs is not None)
                and (set(class_attrs) == set(['table', 'table-striped',
                                              'table-bordered']))):
            headers = True
            for row in table.find_all('tr'):
                for col in row.find_all('td'):
                    if headers:
                        result.add_place_name(str(col.string))
                    else:
                        img = col.find('img')
                        if img is not None:
                            result.add_image_src(img.get('src'))
                        else:
                            result.add_image_src(None)
                headers = not headers

    return result


def download_latest_photo(session, folder, name, url):
    """Downloads the latest photo in the folder"""
    download_errors = False
    output = ""

    # Create the place directory
    place_dir = os.path.join(folder, romanize(name))
    if not os.path.exists(place_dir):
        os.makedirs(place_dir)

    # Find the latest image
    files = sorted([i for i in os.listdir(place_dir)
                    if os.path.isfile(os.path.join(place_dir, i))])

    filename = None
    try:
        req = session.get(url, stream=True, timeout=TIMEOUT)
        if req.status_code == 200:
            ext = mimetypes.guess_extension(req.headers.get('content-type'))
            filename = os.path.join(place_dir,
                                    datetime.utcnow()
                                    .strftime('%Y%m%d%H%M%S'))
            if ext is not None:
                if ext in ['.jpe', '.jpeg']:
                    ext = '.jpg'
                filename = filename + ext
            with open(filename, 'wb') as f_p:
                req.raw.decode_content = True
                shutil.copyfileobj(req.raw, f_p)
        else:
            download_errors = True
            output = "Error Status Code: %d" % (req.status_code)
    except requests.exceptions.RequestException as exc:
        download_errors = True
        output = "Error downloading. %s" % (exc)

    if (not download_errors) and (not verify_photo(filename)):
        download_errors = True
        output = "Error downloading. Not a valid image."

    if not download_errors:
        if (files
                and (md5(os.path.join(place_dir,
                                      files[-1])) == md5(filename))):
            silentremove(filename)
            output = "Not Downloaded. Latest Image: %s" % (files[-1])
        else:
            output = "Downloaded as: %s" % (os.path.basename(filename))
    else:
        silentremove(filename)

    return output

def sane_arguments(fire_input):
    """Transform the argument into a list of strings or a list of integers"""
    type_of = type(fire_input).__name__
    result = []

    # Try to convert possible
    if ((type_of == 'str') or (type_of == 'int') or (type_of == 'float')):
        result = [fire_input]
    elif type_of == 'list':
        result = fire_input[:]
    elif type_of == 'tuple':
        result = list(fire_input)
    elif type_of == 'dict':
        result = [key for key in fire_input]

    result = [int(i) if type(i).__name__ == 'float' else i for i in result]
    return result


def start(folder, url=INDEX_URL, include=None, exclude=None):
    """The main process, of quering the index page and create
    a thread for each photo."""
    # Initialize the mimetypes in order not to create more IO in the worker
    # threads
    mimetypes.init()

    with requests.Session() as session:
        print("Querying Index Page: %r" % (url))
        photos = get_photos(session, INDEX_URL)
        print("Got %d indexes" % (len(photos)))

        # If include parameter is specified, then download only these places
        if include is not None:
            tmp = {}
            for item in sane_arguments(include):
                unique_name = photos.unique_name(item)
                if unique_name in photos.correlation:
                    tmp[unique_name] = photos.correlation[unique_name]
            photos.correlation = tmp

        # Delete all the files for the excluded files
        if exclude is not None:
            tmp = {}
            for item in sane_arguments(exclude):
                unique_name = photos.unique_name(item)
                for key in photos.correlation:
                    if key != unique_name:
                        tmp[key] = photos.correlation[key]
            photos.correlation = tmp

        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = {executor.submit(download_latest_photo,
                                       session, folder, i, photos.correlation[i]):
                       i for i in photos.correlation if photos.correlation[i] is not None}
            for future in concurrent.futures.as_completed(threads):
                name = threads[future]
                try:
                    output = future.result()
                except Exception as exc:
                    print("%s: EXCEPTION: %s" % (name, exc))
                else:
                    print("%s: %s" % (name, output))


def main():
    """The main function of the script. It prohibits to run in parallel
       and also make the argument parsing"""
    _ = singleton.SingleInstance()
    fire.Fire(start)


if __name__ == '__main__':
    main()
