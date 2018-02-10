import mimetypes
import tempfile
import datetime
import requests
import shutil
import sched
import os

from astral import Astral
import imageio
import fire
import pytz

from tools import print_progress, sane_arguments, silentremove
import downloader

# The main index page of web-cameras of meteo.gr
INDEX_URL = 'http://meteo.gr/webcameras.cfm'

# It's a good practice to set connect timeouts to slightly larger than a
# multiple of 3, which is the default TCP packet retransmission window. 
TIMEOUT = 31

def write_frame(session, writer, url, cur_frame, total_frame):
    """Write a frame using the URL of a webcam"""
    filepath = None
    try:
        req = session.get(url, stream=True, timeout=TIMEOUT)
        if req.status_code == 200:
            req.raw.decode_content = True
            ext = mimetypes.guess_extension(req.headers.get('content-type'))
            if ext is not None:
                if ext in ['.jpe', '.jpeg']:
                    ext = '.jpg'

            fp, filepath = tempfile.mkstemp(suffix=ext)

            with os.fdopen(fp, 'wb') as file:
                shutil.copyfileobj(req.raw, file)
        
            image = imageio.imread(filepath)
            writer.append_data(image)
    except Exception as exc:
        print("Warning Exception: %s" % (exc))
    silentremove(filepath)
    print_progress(cur_frame+1, total_frame, prefix='Progress:', suffix='Complete', length=50)


def start(video, place, interval=10, fps=30, force_today=False, url=INDEX_URL):
    mimetypes.init()
    with requests.Session() as session:
        print("Querying Index Page: %r" % (url))
        photos = downloader.get_photos(session, url)
        print("Got %d indexes" % (len(photos)))

    photo_url = None
    for item in sane_arguments(place):
        unique_names = photos.unique_name(item)
        for unique_name in unique_names:
            if unique_name in photos.correlation:
                photo_url = photos.correlation[unique_name]

    print(photo_url)

    # Setting Up Astral
    city_name = 'Athens'
    a = Astral()
    a.solar_depression = 'nautical'
    city = a[city_name]

    print('Information for %s/%s\n' % (city_name, city.region))
    print('Timezone: %s' % city.timezone)
    print('Latitude: %.02f; Longitude: %.02f\n' % \
           (city.latitude, city.longitude))

    now = datetime.datetime.utcnow()
    now = now.replace(tzinfo=pytz.utc)
    start_day = datetime.date.today()
    sun = city.sun(date=start_day, local=False)

    # If we missed the dawn wait for next day
    if ((not force_today) and (sun['dawn'] < now)):
        start_day = start_day + datetime.timedelta(days=1)
        sun = city.sun(date=start_day, local=False)

    print('Dawn:    %s' % str(sun['dawn']))
    print('Sunrise: %s' % str(sun['sunrise']))
    print('Noon:    %s' % str(sun['noon']))
    print('Sunset:  %s' % str(sun['sunset']))
    print('Dusk:    %s' % str(sun['dusk']))

    start_secs = max(int((sun['dawn'] - now).total_seconds()), 0)
    end_secs = max(int((sun['dusk'] - now).total_seconds()), 0)

    with requests.Session() as session:
        session.headers.update({'Cache-Control': 'no-cache, no-store, no-transform'})
        s = sched.scheduler()
        with imageio.get_writer(video, mode='I', fps=fps) as writer:
            for i in range(start_secs,end_secs,interval):
                s.enter(i, 1, write_frame, argument=(session, writer, photo_url, i, end_secs - start_secs))
            print("Capturing %d frames" % (len(s.queue)))
            s.run()
        

def main():
    fire.Fire(start)

if __name__ == '__main__':
    main()
