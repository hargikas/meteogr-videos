# Meteo.gr Timelapse Images and Videos

Python scripts to create timelapse images and videos by downloading images from web-cameras from [meteo.gr](http://meteo.gr/webcameras.cfm).

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

The scripts require python 3, and the following third party libraries:

* Beautiful Soup
* Requests
* Fire
* Tendo
* Pillow

### Installing

You can automatically install all the required package by using [pipenv](http://pipenv.readthedocs.io/en/latest/):

```bash
pipenv install
```

Or you can install manually the required libraries:

```bash
pip3 install beautifulsoup4
pip3 install requests
pip3 install fire
pip3 install tendo
pip3 install pillow
```

### Executing

The main script is [downloader.py](downloader.py) and you can easily execute either with pipenv or just with python.

Pipenv:

```bash
pipenv run python downloader.py --folder /folder/of/images/to/save
```

Just Python:

```bash
python downloader.py --folder /folder/of/images/to/save
```

There is also a sample script file [download.sh](download.sh) which correctly changes to the script working directory in order to create the correct virtual enviroment.

## Built With

* [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) - The HTML parser used
* [Requests](http://docs.python-requests.org/en/master/) - The HTTP library used
* [Fire](https://github.com/google/python-fire) - For command line argument parsing
* [Tendo](https://github.com/pycontribs/tendo) - Single Instance to prevent your script from running in parallel.
* [Pillow](https://pillow.readthedocs.io/en/latest/) - Imaging Library for checking the validity of an image.

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/hargikas/7d68fd0dbb2932d0a3a851e253b48fc5) for details on our code of conduct, and the process for submitting pull requests to us.

## Authors

* **Charalampos Gkikas** - *Initial work* - [hargikas](https://github.com/hargikas)

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* The meteo.gr free use of web-cameras, and anyone who publices their meteo footage.
