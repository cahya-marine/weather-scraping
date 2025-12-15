import time
import schedule
import os
import sys
from datetime import datetime

try:
    from dynamic_scrapper import UniversalScraperV27, AIScraperContext
except ImportError:
    print("ERROR: Tidak dapat menemukan file scraper asli.")
    print("Pastikan file scraper (misal: universal_scraper.py) ada di folder yang sama.")
    sys.exit(1)


TARGET_URL = "https://www.bmkg.go.id/cuaca/prakiraan-cuaca/62"  # URL statis untuk otomatisasi
SCHEDULE_TIME = "00:00"  # Jam 12 Malam (Format 24 jam)

def job_scraping_otomatis():
    """Fungsi wrapper yang akan dipanggil oleh scheduler"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏰ Waktunya Scraping Otomatis!")
    
    try:
        
        print(f"Target URL: {TARGET_URL}")
        context = AIScraperContext(target_url=TARGET_URL)
        
    
        if "GEMINI_API_KEY" not in os.environ:
            print("❌ ERROR: GEMINI_API_KEY tidak ditemukan di environment variable.")
            return

        scraper = UniversalScraperV27(context)
        
        # 3. Jalankan Scrape
        data = scraper.scrape()
        
        # 4. Simpan Hasil
        if data:
            scraper.save_results(data)
            print("✅ Scraping Selesai dan Data Tersimpan.")
        else:
            print("⚠️ Scraping selesai tapi tidak ada data yang valid.")
            
    except Exception as e:
        print(f"❌ TERJADI ERROR SAAT SCRAPING: {e}")

# --- SETUP JADWAL ---
print("--- 🤖 WEATHER SCRAPER SCHEDULER STARTED ---")
print(f"Target: {TARGET_URL}")
print(f"Jadwal: Setiap hari pukul {SCHEDULE_TIME}")
print("Status: LISTENING (Tekan Ctrl+C untuk berhenti)...")

# Atur jadwal harian
schedule.every().day.at(SCHEDULE_TIME).do(job_scraping_otomatis)

# testing setiap 1 menit
# schedule.every(1).minutes.do(job_scraping_otomatis)

# --- LOOP LISTENING ---
if __name__ == "__main__":
    try:
        while True:
            schedule.run_pending()
            # Tidur sebentar agar CPU tidak boros (cek setiap 1 detik)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Scheduler dihentikan oleh user.")