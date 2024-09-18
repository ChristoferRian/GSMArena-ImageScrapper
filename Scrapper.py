import time
import logging
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from stem import Signal
from stem.control import Controller

# Logger untuk mencatat proses scraping
logger = logging.getLogger("gsmarena-scraper")

# Kelas untuk menangani koneksi melalui jaringan Tor
class tor_network:
    def __init__(self):
        # Membuat sesi HTTP yang menggunakan proxy Tor (port 9050)
        self.session = requests.session()
        self.session.proxies = {
            "http": "socks5h://localhost:9050",
            "https": "socks5h://localhost:9050",
        }
        # Variabel untuk menghitung jumlah percobaan koneksi
        self.ntries = 0

    # Fungsi untuk mengambil konten dari sebuah URL dalam bentuk soup
    def get_soup(self, url):
        while True:
            try:
                # Mencoba mengambil konten dari URL
                self.ntries += 1
                soup = BeautifulSoup(
                    self.session.get(url).content, features="lxml"
                )
                # Jika ada respons "Too Many Requests", ganti IP Tor
                if soup.find("title").text.lower() == "too many requests":
                    logger.info(f"Too many requests.")
                    self.request_new_ip()
                # Jika konten berhasil didapatkan atau percobaan sudah melebihi 30 kali
                elif soup or self.ntries > 30:
                    self.ntries = 0
                    break
                # Catat percobaan yang gagal
                logger.debug(f"Try {self.ntries} : Problem with soup for {url}.")
            except Exception as e:
                # Jika ada error, ganti IP dan coba lagi
                logger.debug(f"Can't extract webpage {url}.")
                self.request_new_ip()
        return soup

    # Fungsi untuk meminta IP baru dari jaringan Tor
    def request_new_ip(self):
        logger.info("Requesting new IP address.")
        # Terhubung ke Tor Controller pada port 9051 dan mengirim sinyal NEWNYM untuk mengganti IP
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password="my password")  # Autentikasi dengan password
            controller.signal(Signal.NEWNYM)  # Mengganti IP
        # Memperbarui sesi HTTP dengan proxy yang baru
        self.session = requests.session()
        self.session.proxies = {
            "http": "socks5h://localhost:9050",
            "https": "socks5h://localhost:9050",
        }
        self.ntries = 0

# Fungsi untuk mengekstrak informasi smartphone dari sebuah elemen HTML
def extract_smartphone_infos(network, smartphone):
    # Dictionary untuk menyimpan informasi smartphone
    smartphone_dict = dict()
    
    # Mengambil URL dari elemen <a> dan membentuk URL lengkap
    smartphone = smartphone.find("a")
    url_smartphone = f"https://www.gsmarena.com/{str(smartphone['href'])}"
    logger.debug("url_smartphone : %s", url_smartphone)
    
    # Mengambil URL gambar smartphone
    smartphone_dict["Image"] = str(smartphone.find("img")["src"])
    
    # Mendapatkan konten halaman smartphone dengan Tor
    soup_smartphone = network.get_soup(url_smartphone)
    
    # Mengosongkan memori dari soup yang tidak diperlukan
    soup_smartphone.decompose()
    
    # Mengembalikan informasi smartphone sebagai dictionary
    return smartphone_dict

# Fungsi untuk mengekstrak nama brand dari URL
def extract_brand_name(url_brand_index):
    # Memisahkan URL berdasarkan tanda "-" dan "/"
    parts = url_brand_index.split('-')
    # Mengambil bagian terakhir dari URL yang merupakan nama brand
    name = parts[0].split('/')[-1]
    return name

# Fungsi untuk mengekstrak informasi smartphone dari setiap halaman brand
def extract_phone_brand_infos(network, url_brand_index):
    index_page = 1  # Nomor halaman yang akan diproses
    url_split = url_brand_index.rsplit("-", 1)  # Memisahkan URL berdasarkan tanda "-"
    brand_name = url_split[0].split("/")[-1]  # Mendapatkan nama brand dari URL
    brand_id = url_split[1].split(".")[0]  # Mendapatkan ID brand dari URL
    logger.info(f"Processing brand {brand_name}")  # Mencatat proses brand
    brand_page_base = f"https://www.gsmarena.com/{brand_name}-f-{brand_id}-0"  # URL dasar untuk setiap halaman brand
    smartphone_list = []  # List untuk menyimpan informasi semua smartphone

    while True:
        # Membentuk URL untuk setiap halaman
        url_brand_page = f"{brand_page_base}-p{index_page}.php"
        logger.debug(url_brand_page)
        index_page += 1
        
        # Mendapatkan konten halaman brand
        soup_page = network.get_soup(url_brand_page)
        logger.debug(f"Page URL : {url_brand_page}")

        # Memeriksa apakah halaman memiliki list smartphone
        if soup_page.find("div", {"class": "section-body"}).select("li"):
            smartphones = soup_page.find("div", {"class": "section-body"}).find_all("li")
            soup_page.decompose()
            # Mengekstrak informasi untuk setiap smartphone
            for smartphone in smartphones:
                smartphone_dict = extract_smartphone_infos(network, smartphone)
                smartphone_list.append(smartphone_dict)  # Menambahkan ke list smartphone
        else:
            soup_page.decompose()
            logger.error("%s : seharusnya sudah selesai", url_brand_page)
            return smartphone_list  # Mengembalikan list smartphone

# Fungsi utama untuk menjalankan proses scraping
def main():
    network = tor_network()  # Inisialisasi koneksi melalui jaringan Tor
    
    url_brand_index = input('Input brand URL : ')  # Meminta input URL brand dari pengguna
    
    # Ekstrak nama brand dari URL
    brand_name = extract_brand_name(url_brand_index)
    
    # Membuat direktori untuk menyimpan hasil jika belum ada
    Path("Exports").mkdir(parents=True, exist_ok=True)

    global_list_smartphones = pd.DataFrame()  # DataFrame global untuk menyimpan semua smartphone
    
    # Menjalankan fungsi untuk mengekstrak informasi smartphone dari brand URL
    smartphone_list = extract_phone_brand_infos(network, url_brand_index)

    # Mengonversi list smartphone menjadi DataFrame
    phone_dict = pd.DataFrame.from_records(smartphone_list)

    # Menambahkan ke DataFrame global
    global_list_smartphones = pd.concat([global_list_smartphones, phone_dict], sort=False).drop_duplicates()
    
    
    
    # di filter biar gak ada gif di dalam csv nya, jadi cuma jpg doang
    global_list_smartphones = global_list_smartphones[~global_list_smartphones.apply(lambda row: row.astype(str).str.contains('.gif').any(), axis=1)]

    # Menyimpan DataFrame global ke file CSV dengan nama sesuai brand
    global_export_file = f"Exports/{brand_name}.csv"

    

    #di save ke csv
    global_list_smartphones.to_csv(global_export_file, sep=";", index=False)
    
    logger.info(f"All data has been saved to {global_export_file}")  # Mencatat bahwa data telah disimpan

if __name__ == "__main__":
    main()  # Memanggil fungsi utama ketika script dijalankan
