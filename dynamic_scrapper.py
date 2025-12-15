from pydantic import ValidationError
from google import genai
from google.genai import types
import os
import sys
import time
import json
import importlib
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

try:
    config_module = importlib.import_module("scraper_config")
    TARGET_SCHEMA = config_module.TARGET_SCHEMA # Sekarang UniversalOutputV27
    pd = config_module.pd 
except ImportError as e:
    print(f"ERROR: Gagal mengimpor konfigurasi dari scraper_config.py: {e}")
    sys.exit(1)

STORAGE_STATE_FILE = "playwright_state_v27.json" 

class AIScraperContext:
    def __init__(self, target_url): 
        self.target_url = target_url
        self.TargetSchema = TARGET_SCHEMA
        self.scraper_name = "Universal_V27_Monthly"
        
class UniversalScraperV27:
    
    def __init__(self, context: AIScraperContext):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY tidak ditemukan. Harap atur environment variable Anda.")
            
        self.client = genai.Client(api_key=api_key)
        self.context = context

    def _clean_text(self, text):
        if not text: return ""
        text = text.replace('\n', ' ').replace('\t', ' ').replace('  ', ' ')
        return " ".join(text.split()).strip()

    def _extract_data_ai(self, text_raw_full_page, url):
        """Zero-Shot Prompting: Fokus pada Multiple Time Forecast (Daily, Hourly, Monthly)."""
        
        TargetSchema = self.context.TargetSchema
        
        prompt = (
            "Anda adalah mesin ekstraksi data cuaca. Tugas Anda adalah memproses seluruh teks halaman web dan memetakannya ke dalam skema JSON hierarkis.\n\n"
            "Instruksi Kritis (Multiple Time Forecast):\n"
            "1. Identifikasi lokasi induk (Kota/Daerah) dan masukkan ke **'parent_location'**.\n"
            "2. **Ekstrak SEMUA jenis prakiraan cuaca yang ditemukan di halaman, dan masukkan ke field yang sesuai.**\n"
            "3. **Prakiraan Harian (Daily)**: Jika ada, masukkan ke **'all_locations_forecast'**. (Ini termasuk multi-lokasi atau ringkasan harian lokasi tunggal).\n"
            "4. **Prakiraan Per Jam (Hourly)**: Jika ada, ekstrak dan **KELOMPOKKAN** data per jam tersebut berdasarkan hari (e.g., Thursday, Friday) ke dalam list **'hourly_forecasts_grouped'**.\n"
            "5. **Prakiraan Bulanan (Monthly)**: Jika ada, ekstrak ke list **'monthly_forecasts'**.\n"
            "6. Jika suatu jenis prakiraan tidak ditemukan, **maka list tersebut harus kosong `[]`**.\n"
            "7. Jika suatu field tidak ditemukan (selain list), tetapkan nilainya sebagai 'N/A'.\n\n"
            "--- URL Target ---\n"
            f"{url}\n"
            "--- SELURUH Teks Mentah dari Halaman Web ---\n"
            f"{text_raw_full_page}\n"
        )

        try:

            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TargetSchema, 
                    temperature=0.0 
                ),
            )
            data_dict = json.loads(response.text)
            validated_data = TargetSchema.model_validate(data_dict)
            return validated_data.model_dump()

        except (genai.errors.APIError, json.JSONDecodeError, ValidationError) as e:
            print(f"!!! Error API/JSON Validation: {type(e).__name__}. Mengembalikan default.")
            return TargetSchema.default_data(url).model_dump()

    # ... (_human_like_interaction sama) ...
    def _human_like_interaction(self, page):
        """Simulasi interaksi manusia (scroll) untuk anti-bot."""
        print("Melakukan interaksi simulasi manusia (scroll acak)...")
        try:
            scroll_count = 5
            for i in range(scroll_count):
                page.evaluate(f"window.scrollBy(0, 500*{i})")
                time.sleep(1) 
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(2) 
            print("Simulasi interaksi selesai.")
        except Exception as e:
            print(f"Warning: Interaksi gagal, melanjutkan. Error: {e}")

    def scrape(self):
        url = self.context.target_url
        print(f"\n--- Memulai Scanning Zero-Shot Universal (V27) ---")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True, 
                channel="chrome", 
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-http2', 
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--single-process'
                ]
            )
            
            # --- Load state (V27) ---
            storage_path = STORAGE_STATE_FILE
            
            context_options = {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            if os.path.exists(storage_path):
                print(f"Menggunakan sesi persisten dari: {storage_path}")
                context_options['storage_state'] = storage_path
            else:
                print("Membuat sesi baru (state file tidak ditemukan).")

            context = browser.new_context(**context_options)
            page = context.new_page()

            try:
                print("Mengakses URL. Menunggu 'networkidle' (90s)...")
                page.goto(url, timeout=20000, wait_until='domcontentloaded') 
                

                
                self._human_like_interaction(page)

                # --- TUNGGU KONTEN DINAMIS ---
                print("Menunggu elemen utama prakiraan cuaca dimuat (45s)...")
                try:
                    # Selector Monthly Weather.com: MonthlyContent
                    monthly_selector = "//div[contains(@class, 'MonthlyContent') or contains(@class, 'Monthly--forecast')]"
                    
                    # Gabungkan dengan selector situs lain
                    combined_selector = f"{monthly_selector} | //div[contains(@class, 'DailyContent') or contains(@class, 'HourlyContent') or contains(@class, 'table-responsive') or contains(@class, 'forecast-container')]"

                    page.wait_for_selector(f"xpath={combined_selector}", timeout=10000)

                except PlaywrightTimeoutError:
                    print("Warning: Selector spesifik timeout. Melanjutkan dengan jeda 10s.")
                
                # EKSTRAKSI TEKS
                full_page_text = self._clean_text(page.locator('body').inner_text())
                
                if len(full_page_text) < 500:
                    print("Teks konten halaman terlalu singkat. Mungkin pemblokiran.")
                    return []
                    
                print(f"Mengirim {len(full_page_text)} karakter teks ke AI untuk diproses...")
                
                extracted = self._extract_data_ai(full_page_text, url)
                
                # Cek hasil dari salah satu dari 3 list
                if extracted.get('all_locations_forecast') or extracted.get('hourly_forecasts_grouped') or extracted.get('monthly_forecasts'):
                    extracted_locs = len(extracted.get('all_locations_forecast', []))
                    extracted_groups = len(extracted.get('hourly_forecasts_grouped', []))
                    extracted_monthly = len(extracted.get('monthly_forecasts', []))
                    print(f"Sukses! Berhasil mengekstrak {extracted_locs} lokasi (harian), {extracted_groups} grup jam, dan {extracted_monthly} entri bulanan.")
                    return [extracted]
                
                print("AI gagal mengekstrak data dari halaman.")
                return []
            
            except PlaywrightTimeoutError as e:
                print(f"Error Timeout Playwright: {e}")
                print("Halaman gagal dimuat. Coba jalankan ulang skrip ini.")
                return []
            except Exception as e:
                print(f"Error utama pada {url}: {e}")
                print("Kemungkinan deteksi bot.")
                return []
            finally:
                browser.close()

    def save_results(self, data):
        """Menyimpan data Bulanan, Multi-Lokasi, dan Hourly Grouped."""
        if not data:
            print("Tidak ada data valid yang ditemukan.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = self.context.scraper_name
        
        utama = data[0]
        parent_location = utama.get('parent_location')
        source_url = utama.get('source_url')
        forecast_period = utama.get('forecast_period')
        
        # 1. Simpan JSON
        filename_json = f"{prefix}_{timestamp}.json"
        with open(filename_json, 'w', encoding='utf-8') as f:
            json.dump(utama, f, indent=4, ensure_ascii=False)
            
        print(f"\n--- EKSTRAKSI SUKSES V27 ---")
        print(f"Hasil JSON (termasuk Monthly) disimpan ke: {filename_json}")

        # 2. Simpan CSV Monthly (Jika ada)
        if pd and utama.get('monthly_forecasts'):
            filename_monthly_csv = f"{prefix}_{timestamp}_MONTHLY.csv"
            rows_monthly = []
            
            for monthly_entry in utama['monthly_forecasts']:
                rows_monthly.append({
                    'parent_location': parent_location,
                    'source_url': source_url,
                    'forecast_period': forecast_period,
                    **monthly_entry
                })
            
            df_monthly = pd.DataFrame(rows_monthly)
            df_monthly.to_csv(filename_monthly_csv, index=False)
            print(f"Data Bulanan ({len(rows_monthly)} entri) disimpan ke: {filename_monthly_csv}")
        else:
            print("Penyimpanan CSV Bulanan dilewati.")


        # 3. Simpan CSV Hourly Grouped (Jika ada)
        if pd and utama.get('hourly_forecasts_grouped'):
            filename_hourly_csv = f"{prefix}_{timestamp}_HOURLY_GROUPED.csv"
            rows_hourly = []
            
            for daily_group in utama['hourly_forecasts_grouped']:
                date_day_name = daily_group['date_day_name']
                for hourly_entry in daily_group['hourly_entries']:
                    rows_hourly.append({
                        'parent_location': parent_location,
                        'date_day_name': date_day_name,
                        'source_url': source_url,
                        **hourly_entry
                    })
            
            df_hourly = pd.DataFrame(rows_hourly)
            df_hourly.to_csv(filename_hourly_csv, index=False)
            print(f"Data Per Jam ({len(rows_hourly)} total entri) disimpan ke: {filename_hourly_csv}")
        else:
            print("Penyimpanan CSV Per Jam dilewati.")

        # 4. Simpan CSV Multi-Lokasi / Lokasi Tunggal Harian (Jika ada)
        if pd and utama.get('all_locations_forecast'):
            filename_daily_csv = f"{prefix}_{timestamp}_DAILY_FORECAST.csv"
            rows_daily = []
            
            for location_forecast in utama['all_locations_forecast']:
                location_name = location_forecast['location_name']
                for daily_entry in location_forecast['daily_forecasts']:
                    rows_daily.append({
                        'parent_location': parent_location,
                        'location_name': location_name,
                        'source_url': source_url,
                        'forecast_period': forecast_period,
                        **daily_entry
                    })
            
            df_daily = pd.DataFrame(rows_daily)
            df_daily.to_csv(filename_daily_csv, index=False)
            print(f"Data Harian ({len(rows_daily)} entri) disimpan ke: {filename_daily_csv}")
        else:
            print("Penyimpanan CSV Harian dilewati.")



if __name__ == "__main__":
    target_url = input("Masukkan URL target (Monthly/Hourly/Daily): ").strip()

    if not target_url:
        print("\n[!!! GAGAL !!!] URL target tidak boleh kosong.")
        sys.exit(1)

    try:
        context = AIScraperContext(target_url=target_url)
        scraper = UniversalScraperV27(context)
        site_data = scraper.scrape()
        scraper.save_results(site_data)
        
    except EnvironmentError as e:
        print(f"\n[!!! GAGAL !!!] {e}")
    except Exception as e:
        print(f"\n[!!! KESALAHAN UMUM !!!] Terjadi kesalahan saat menjalankan scraper: {e}")