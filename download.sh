#!/bin/bash
cd "$(dirname "$0")"
# Download Everyting
#pipenv run python downloader.py --folder /mnt/movies/raspberry_timelapse
# Download only the first three places
pipenv run python downloader.py --folder /mnt/movies/raspberry_timelapse --include [1,2,3]
cd -
