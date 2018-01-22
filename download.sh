#!/bin/bash
cd "$(dirname "$0")"
pipenv run python downloader.py --folder /media/pi/TIMELAPSE/
cd -
