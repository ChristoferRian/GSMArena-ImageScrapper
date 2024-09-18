import os
import pandas as pd
import requests
from pathlib import Path
from stem import Signal
from stem.control import Controller
import logging

# Logger untuk mencatat proses
logger = logging.getLogger("gsmarena-scraper")

class tor_network:
    def __init__(self):
        # Membuat sesi HTTP yang menggunakan proxy Tor (port 9050)
        self.session = requests.session()
        self.session.proxies = {
            "http": "socks5h://localhost:9050",
            "https": "socks5h://localhost:9050",
        }
        self.ntries = 0

    def get_soup(self, url):
        """Mengambil konten dari sebuah URL dalam bentuk soup."""
        while True:
            try:
                self.ntries += 1
                soup = BeautifulSoup(self.session.get(url).content, 'lxml')
                if soup.find("title").text.lower() == "too many requests":
                    logger.info("Too many requests.")
                    self.request_new_ip()
                elif soup or self.ntries > 30:
                    self.ntries = 0
                    break
                logger.debug(f"Try {self.ntries} : Problem with soup for {url}.")
            except Exception as e:
                logger.debug(f"Can't extract webpage {url}.")
                self.request_new_ip()
        return soup

    def request_new_ip(self):
        """Meminta IP baru dari jaringan Tor."""
        logger.info("Requesting new IP address.")
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password="my password")
            controller.signal(Signal.NEWNYM)
        self.session = requests.session()
        self.session.proxies = {
            "http": "socks5h://localhost:9050",
            "https": "socks5h://localhost:9050",
        }
        self.ntries = 0

def download_image(session, image_url, save_path):
    """Mendownload gambar menggunakan sesi Tor."""
    try:
        response = session.get(image_url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Image successfully downloaded: {save_path}")
        else:
            print(f"Failed to download image: {image_url}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    """Fungsi utama untuk membaca CSV dan mendownload gambar."""
    network = tor_network()

    input_file = input('masukkan nama file csv nya : ')

    csv_file = f"Exports/{input_file}.csv"  # Nama file CSV
    save_directory = f'Images/{input_file}'  # Folder tempat menyimpan gambar

    df = pd.read_csv(csv_file, sep=";")
    Path(save_directory).mkdir(parents=True, exist_ok=True)

    for index, row in df.iterrows():
        image_url = row['Image']  # Kolom yang berisi URL gambar
        image_name = image_url.split("/")[-1].replace("-", " ")  # Nama file gambar dari URL
        save_path = os.path.join(save_directory, image_name)  # Path tempat gambar disimpan

        download_image(network.session, image_url, save_path)

if __name__ == "__main__":
    main()
