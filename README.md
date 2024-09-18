# gsmarena_scraper

SHOUT OUT TO : dbeley https://github.com/dbeley

This project is based from this page https://github.com/dbeley/gsmarena-scraper, with modifications to focus on downloading smartphone images.

The script extracts image links of phones from the gsmarena.com website to a CSV file, one for each brand. You can use a second script to download images from the generated CSV files.

To avoid spam detection, run with TOR (see below).

## Requirements

- python + pip
- docker + docker-compose

## Installation

Clone the repository:
```
git clone https://github.com/ChristoferRian/GSMArena-ImageScrapper
cd gsmarena-scraper
```

Install the python dependencies:
```
pip install requests beautifulsoup4 lxml pandas pysocks stem
```

If you prefer, you can also install the requirements in a virtual environment with pipenv (in order to run the python script, you will need to use `pipenv run python gsmarena-scraper.py` instead of `python gsmarena-scraper.py`):
```
pipenv install
```

## Usage

Run the docker container containing the tor proxy (you can tweak the torrc configuration file if you want, but the defaults should be good):
```
docker-compose up -d
```

Run the scrapper script:
```
python Scrapper.py
```

Download the images using:
```
python Downloader.py
```
After completion, you can stop the docker container with `docker-compose down`.

## Example Usage

Scrapper:
```
python Scrapper.py
input brand URL : https://www.gsmarena.com/google-phones-107.php
```

Downloader:
```
python Downloader.py
masukkan nama file csv nya : google
```

## Files exported

The `Scrapper.py` script will generate a CSV file with image links for each phone in the folder `Exports/{Brand_Name}.csv.`

To download the images, use the `Downloader.py` script with the CSV file of the desired brand.

