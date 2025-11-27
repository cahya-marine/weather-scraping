import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime

def scrape_bmkg_weather(url):
    """
    Scrape data cuaca dari website BMKG
    
    Args:
        url: URL halaman prakiraan cuaca BMKG
        
    Returns:
        list: List of dictionaries containing weather data
    """
    print(f"Mengambil data dari: {url}")
    
    # Headers untuk menghindari blocking
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Fetch halaman
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Cari tabel
        table = soup.find('table')
        if not table:
            print("Error: Tabel tidak ditemukan!")
            return []
        
        # Ambil header tanggal
        dates = []
        thead = table.find('thead')
        if thead:
            headers = thead.find_all('th')
            for i, th in enumerate(headers):
                if i > 0:  # Skip kolom pertama (Kab/Kota)
                    date_text = th.get_text(strip=True)
                    if date_text:
                        dates.append(date_text)
        
        # Ambil data dari tbody
        data = []
        tbody = table.find('tbody')
        if not tbody:
            print("Error: Tbody tidak ditemukan!")
            return []
        
        rows = tbody.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 0:
                continue
            
            # Ambil nama kabupaten/kota
            kab_kota_cell = cells[0]
            link = kab_kota_cell.find('a')
            kab_kota = link.get_text(strip=True) if link else kab_kota_cell.get_text(strip=True)
            
            # Iterasi setiap kolom cuaca (skip kolom pertama)
            for i, cell in enumerate(cells[1:]):
                date_index = i
                tanggal = dates[date_index] if date_index < len(dates) else f"Hari ke-{i+1}"
                
                # Parse isi cell
                cell_text = cell.get_text('\n', strip=True)
                lines = [line.strip() for line in cell_text.split('\n') if line.strip()]
                
                keterangan_cuaca = ''
                suhu = ''
                kelembapan = ''
                
                if len(lines) >= 3:
                    keterangan_cuaca = lines[0]
                    suhu = lines[1]
                    kelembapan = lines[2]
                elif len(lines) == 2:
                    keterangan_cuaca = lines[0]
                    suhu = lines[1]
                elif len(lines) == 1:
                    keterangan_cuaca = lines[0]
                
                if kab_kota and keterangan_cuaca:
                    data.append({
                        'kabupaten_kota': kab_kota,
                        'tanggal': tanggal,
                        'keterangan_cuaca': keterangan_cuaca,
                        'suhu': suhu,
                        'kelembapan': kelembapan
                    })
        
        print(f"Berhasil scraping {len(data)} data!")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error saat fetch: {e}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def save_to_csv(data, filename=None):
    """Simpan data ke CSV"""
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'bmkg_cuaca_{timestamp}.csv'
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Data berhasil disimpan ke: {filename}")
    return filename


def save_to_json(data, filename=None):
    """Simpan data ke JSON"""
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'bmkg_cuaca_{timestamp}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Data berhasil disimpan ke: {filename}")
    return filename


def print_data_preview(data, limit=10):
    """Tampilkan preview data"""
    print("\n" + "="*80)
    print("PREVIEW DATA")
    print("="*80)
    
    if not data:
        print("Tidak ada data!")
        return
    
    for i, item in enumerate(data[:limit]):
        print(f"\n[{i+1}]")
        print(f"  Kabupaten/Kota  : {item['kabupaten_kota']}")
        print(f"  Tanggal         : {item['tanggal']}")
        print(f"  Cuaca           : {item['keterangan_cuaca']}")
        print(f"  Suhu            : {item['suhu']}")
        print(f"  Kelembapan      : {item['kelembapan']}")
    
    if len(data) > limit:
        print(f"\n... dan {len(data) - limit} data lainnya")
    
    print("\n" + "="*80)


# ============================================================================
# MAIN PROGRAM
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("BMKG WEATHER SCRAPER")
    print("="*80)
    
    # URL target - bisa diganti sesuai provinsi yang diinginkan
    # Contoh URL:
    # 62 = Kalimantan Tengah
    # 63 = Kalimantan Selatan  
    # 64 = Kalimantan Timur
    # 31 = DKI Jakarta
    # 32 = Jawa Barat
    
    url = "https://www.bmkg.go.id/cuaca/prakiraan-cuaca/62"
    
    # Scrape data
    weather_data = scrape_bmkg_weather(url)
    
    if weather_data:
        # Preview data
        print_data_preview(weather_data, limit=5)
        
        # Simpan ke CSV
        csv_file = save_to_csv(weather_data)
        
        # Simpan ke JSON
        json_file = save_to_json(weather_data)
        
        print("\n✓ Scraping selesai!")
        print(f"  Total data: {len(weather_data)}")
        print(f"  File CSV  : {csv_file}")
        print(f"  File JSON : {json_file}")
    else:
        print("\n✗ Gagal scraping data!")
    
    print("\n" + "="*80)