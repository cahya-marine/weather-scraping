# scraper_config.py (V20 Multi-Lokasi)

from pydantic import BaseModel, Field
import pandas as pd



# --- Skema Harian (Sama seperti sebelumnya) ---
class UniversalDailyEntry(BaseModel):
    date_day: str = Field(description="Hari dan Tanggal (e.g., Thu, 27 Nov).")
    high_temp: str = Field(description="Suhu tertinggi, termasuk unit (e.g., 30 °C).")
    low_temp: str = Field(description="Suhu terendah, termasuk unit (e.g., 25 °C).")
    condition_summary: str = Field(description="Deskripsi cuaca (e.g., Hujan Ringan, Berawan).")
    precipitation_chance: str = Field(description="Peluang Presipitasi. Jika tidak ada, isi 'N/A'.")
    wind_speed: str = Field(description="Kecepatan Angin dan arah. Jika tidak ada, isi 'N/A'.")

# --- SKEMA BARU: Prakiraan untuk Satu Lokasi (LocationForecast) ---
# Ini adalah objek yang akan diulang untuk setiap kota
class LocationForecast(BaseModel):
    location_name: str = Field(description="Nama kota/kabupaten spesifik yang diekstrak (e.g., Sampit, Pangkalan Bun).")
    daily_forecasts: list[UniversalDailyEntry] = Field(description="Daftar prakiraan harian untuk lokasi ini.")


# --- SKEMA CUACA UNIVERSAL OUTPUT (Multi-Lokasi) ---
class MultiLocationOutput(BaseModel):
    # Nama daerah yang lebih besar (misal Provinsi)
    parent_location: str = Field(description="Nama provinsi, negara bagian, atau area induk yang ditemukan di halaman web (e.g., Kalimantan Tengah). Jika tidak ada, isi 'N/A'.")
    source_url: str = Field(description="URL dari mana data ini diambil.")
    forecast_period: str = Field(description="Rentang tanggal prakiraan yang dicakup (e.g., 5 hari ke depan).")
    
    # LIST UTAMA: Daftar semua lokasi yang ditemukan di halaman
    all_locations_forecast: list[LocationForecast] = Field(description="Daftar lengkap prakiraan untuk **SEMUA** kota/kabupaten yang ditemukan di halaman.")
    
    @classmethod
    def default_data(cls, url):
        return cls(parent_location="N/A", source_url=url, forecast_period="N/A", all_locations_forecast=[])
class HourlyEntry(BaseModel):
    time_of_day: str = Field(description="Waktu dalam jam (e.g., 1 PM, 14:00, 08:00).")
    temp: str = Field(description="Suhu pada jam tersebut, termasuk unit (e.g., 28°C).")
    condition: str = Field(description="Deskripsi cuaca per jam (e.g., Cloudy, Light Rain).")
    feels_like: str = Field(description="Suhu RealFeel/Terasa seperti (e.g., 30°C). Jika tidak ada, isi 'N/A'.")
    wind: str = Field(description="Kecepatan dan arah angin (e.g., 10 km/h W). Jika tidak ada, isi 'N/A'.")


# --- SKEMA CUACA UNIVERSAL OUTPUT (V21: Multi-Lokasi + Hourly) ---
class DailyHourlyGroup(BaseModel):
    date_day_name: str = Field(description="Nama hari untuk grup ini (e.g., Thursday, Friday, Saturday).")
    hourly_entries: list[HourlyEntry] = Field(description="Daftar prakiraan per jam yang hanya berlaku untuk hari ini.")

# --- SKEMA CUACA UNIVERSAL OUTPUT (V22: Multi-Lokasi + Hourly Grouped) ---
class MonthlyEntry(BaseModel):
    date_month_day: str = Field(description="Tanggal (e.g., Nov 27, Dec 1).")
    day_temp: str = Field(description="Suhu rata-rata siang, termasuk unit (e.g., 30°C).")
    night_temp: str = Field(description="Suhu rata-rata malam, termasuk unit (e.g., 23°C).")
    condition_summary: str = Field(description="Deskripsi cuaca (e.g., Scattered Thunderstorms).")
    precipitation_chance: str = Field(description="Peluang Presipitasi. Jika tidak ada, isi 'N/A'.")

# --- SKEMA CUACA UNIVERSAL OUTPUT (V27: Monthly + Grouped Hourly + Multi-Lokasi) ---
class UniversalOutputV27(BaseModel):
    parent_location: str = Field(description="Nama kota/area induk.")
    source_url: str = Field(description="URL dari mana data ini diambil.")
    forecast_period: str = Field(description="Rentang tanggal prakiraan (e.g., Monthly forecast for November 2025).")
    
    # Data Harian (dari Multi-Lokasi atau Lokasi Tunggal)
    all_locations_forecast: list[LocationForecast] = Field(description="Daftar prakiraan harian. Kosongkan list [] jika halaman adalah Monthly/Hourly.")
    
    # Data Per Jam yang Dikelompokkan
    hourly_forecasts_grouped: list[DailyHourlyGroup] = Field(description="Daftar prakiraan per jam yang dikelompokkan per hari. Kosongkan list [] jika halaman adalah Monthly/Daily.")
    
    # FIELD BARU: Data Bulanan
    monthly_forecasts: list[MonthlyEntry] = Field(description="Daftar prakiraan Bulanan, mencakup semua hari dalam kalender yang terlihat. Kosongkan list [] jika halaman adalah Hourly/Daily.")

    @classmethod
    def default_data(cls, url):
        return cls(parent_location="N/A", source_url=url, forecast_period="N/A", 
                   all_locations_forecast=[], hourly_forecasts_grouped=[], monthly_forecasts=[])

TARGET_SCHEMA = UniversalOutputV27