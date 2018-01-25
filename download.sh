#!/bin/bash
cd "$(dirname "$0")"
pipenv run python downloader.py --folder /mnt/movies/raspberry_timelapse
cd -
