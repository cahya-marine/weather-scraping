# ☁️ Weather Scraping Tool

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub contributors](https://img.shields.io/github/contributors/cahya-marine/weather-scraping.svg)](https://github.com/cahya-marine/weather-scraping/graphs/contributors)
[![GitHub stars](https://img.shields.io/github/stars/cahya-marine/weather-scraping.svg?style=social)](https://github.com/cahya-marine/weather-scraping/stargazers)


### Prasyarat Sistem

Pastikan sistem Anda telah terinstal:

1.  **Python 3.8 atau lebih baru.**
2.  **Git** (untuk *cloning* repositori).

###  Instalation


1.  **Buat Lingkungan Virtual (`venv`):**
    ```bash
    python -m venv venv
    ```
2.  **Aktifkan Lingkungan Virtual:**
    * **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    * **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    *(Anda akan melihat `(venv)` di depan prompt terminal Anda)*
3.  **Instal Pustaka yang Diperlukan:** Instal semua dependensi yang terdaftar di `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

###  Eksekusi

1.  **Konfigurasi (Opsional):** Jika Anda ingin mengubah kota target atau URL sumber data, buka file `config.py` atau `main.py` dan ubah variabel `TARGET_CITIES` atau `TARGET_URLS` yang ada.
2.  **Jalankan Scraper:** Eksekusi file utama aplikasi.
    ```bash
    python main.py
    ```


## Kontak

* **Pengembang:** Cahya Caa
* **GitHub:** [@cahyacaa](https://github.com/cahyacaa)
* **Link Proyek:** [https://github.com/cahya-marine/weather-scraping](https://github.com/cahya-marine/weather-scraping)