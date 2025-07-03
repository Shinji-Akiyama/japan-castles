#!/usr/bin/env python3
"""
Final castle data scraper for cmeg.jp
Collects comprehensive castle data from all Japanese prefectures with proper parsing
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import re
from urllib.parse import quote

# Prefecture data
PREFECTURES = [
    # Tohoku (福島県 only - others already collected)
    ('福島県', 'Fukushima'),
    # Kanto
    ('茨城県', 'Ibaraki'),
    ('栃木県', 'Tochigi'),
    ('群馬県', 'Gunma'),
    ('埼玉県', 'Saitama'),
    ('千葉県', 'Chiba'),
    ('東京都', 'Tokyo'),
    ('神奈川県', 'Kanagawa'),
    # Chubu
    ('新潟県', 'Niigata'),
    ('富山県', 'Toyama'),
    ('石川県', 'Ishikawa'),
    ('福井県', 'Fukui'),
    ('山梨県', 'Yamanashi'),
    ('長野県', 'Nagano'),
    ('岐阜県', 'Gifu'),
    ('静岡県', 'Shizuoka'),
    ('愛知県', 'Aichi'),
    # Kinki
    ('三重県', 'Mie'),
    ('滋賀県', 'Shiga'),
    ('京都府', 'Kyoto'),
    ('大阪府', 'Osaka'),
    ('兵庫県', 'Hyogo'),
    ('奈良県', 'Nara'),
    ('和歌山県', 'Wakayama'),
    # Chugoku
    ('鳥取県', 'Tottori'),
    ('島根県', 'Shimane'),
    ('岡山県', 'Okayama'),
    ('広島県', 'Hiroshima'),
    ('山口県', 'Yamaguchi'),
    # Shikoku
    ('徳島県', 'Tokushima'),
    ('香川県', 'Kagawa'),
    ('愛媛県', 'Ehime'),
    ('高知県', 'Kochi'),
    # Kyushu/Okinawa
    ('福岡県', 'Fukuoka'),
    ('佐賀県', 'Saga'),
    ('長崎県', 'Nagasaki'),
    ('熊本県', 'Kumamoto'),
    ('大分県', 'Oita'),
    ('宮崎県', 'Miyazaki'),
    ('鹿児島県', 'Kagoshima'),
    ('沖縄県', 'Okinawa'),
]

def get_page(url, retries=3):
    """Fetch a web page with retries"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"    Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5)
    return None

def extract_castle_from_resultbox(resultbox, prefecture_jp):
    """Extract castle information from a resultbox div"""
    castle = {
        'ID': '',
        '都道府県': prefecture_jp,
        '城名': '',
        '読み方': '',
        '種類': '',
        '所在地': '',
        '築城年代': '',
        '城主・築城者': '',
        '別名': '',
        '備考': ''
    }
    
    # Get castle name and reading
    h2 = resultbox.find('h2')
    if h2 and h2.find('a'):
        link = h2.find('a')
        # Extract castle name and reading
        text = link.get_text(strip=True)
        # Match pattern like "会津若松城（あいづわかまつじょう）"
        match = re.match(r'(.+?)（(.+?)）', text)
        if match:
            castle['城名'] = match.group(1)
            castle['読み方'] = match.group(2)
        else:
            castle['城名'] = text
        
        # Extract ID from URL
        href = link.get('href', '')
        id_match = re.search(r'/castles/(\d+)', href)
        if id_match:
            castle['ID'] = id_match.group(1)
    
    # Extract details from dl.result-list
    dl = resultbox.find('dl', class_='result-list')
    if dl:
        # Get all dt/dd pairs
        dts = dl.find_all('dt')
        dds = dl.find_all('dd')
        
        for dt, dd in zip(dts, dds):
            dt_text = dt.get_text(strip=True)
            dd_text = dd.get_text(strip=True)
            
            if '通称' in dt_text or '別名' in dt_text:
                castle['別名'] = dd_text
            elif '所在地' in dt_text:
                castle['所在地'] = dd_text
            elif '主な城主' in dt_text or '城主' in dt_text:
                castle['城主・築城者'] = dd_text
            elif '遺構' in dt_text:
                castle['備考'] = f"遺構: {dd_text}"
            elif '築城' in dt_text:
                castle['築城年代'] = dd_text
            elif '城郭構造' in dt_text or '種別' in dt_text:
                castle['種類'] = dd_text
    
    return castle

def scrape_prefecture_page(url, prefecture_jp):
    """Scrape a single page of castle listings"""
    print(f"  Fetching: {url}")
    content = get_page(url)
    
    if not content:
        print(f"    Failed to fetch page")
        return []
    
    soup = BeautifulSoup(content, 'html.parser')
    castles = []
    
    # Find all resultbox divs
    resultboxes = soup.find_all('div', class_='resultbox')
    
    for resultbox in resultboxes:
        castle = extract_castle_from_resultbox(resultbox, prefecture_jp)
        if castle['城名']:  # Only add if we found a castle name
            castles.append(castle)
    
    print(f"    Found {len(castles)} castles")
    return castles

def scrape_prefecture_castles(prefecture_jp, prefecture_en):
    """Scrape all castles for a given prefecture with pagination"""
    all_castles = []
    page = 1
    base_url = f"https://cmeg.jp/w/castles/{quote(prefecture_jp)}"
    
    while True:
        # Construct URL with pagination
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}/{page}"
        
        # Scrape this page
        page_castles = scrape_prefecture_page(url, prefecture_jp)
        
        if not page_castles:
            break
        
        all_castles.extend(page_castles)
        
        # Check if we should continue (cmeg.jp shows 30 items per page typically)
        if len(page_castles) < 30:
            break
        
        page += 1
        time.sleep(2)  # Be polite to the server
    
    return all_castles

def load_existing_data():
    """Load existing castle data from CSV"""
    existing = []
    try:
        with open('castle_data.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            castle_id = 1
            for row in reader:
                # Convert to new format
                castle = {
                    'ID': str(castle_id),
                    '都道府県': row.get('Prefecture', ''),
                    '城名': row.get('Castle Name (Japanese)', ''),
                    '読み方': row.get('Castle Name (Romaji)', ''),
                    '種類': '',
                    '所在地': row.get('Location', ''),
                    '築城年代': '',
                    '城主・築城者': row.get('Main Lords', ''),
                    '別名': row.get('Alternative Names', ''),
                    '備考': row.get('Remaining Structures', '')
                }
                existing.append(castle)
                castle_id += 1
        print(f"Loaded {len(existing)} existing castles from castle_data.csv")
    except Exception as e:
        print(f"Could not load existing data: {e}")
    return existing

def save_data(castles, filename):
    """Save castle data to CSV"""
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['ID', '都道府県', '城名', '読み方', '種類', '所在地', '築城年代', '城主・築城者', '別名', '備考']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(castles)
    print(f"\nSaved {len(castles)} castles to {filename}")

def main():
    """Main function"""
    print("Castle Data Collection from cmeg.jp")
    print("=" * 50)
    
    # Load existing data
    all_castles = load_existing_data()
    
    # Track highest ID
    max_id = 0
    for castle in all_castles:
        try:
            castle_id = int(castle['ID'])
            if castle_id > max_id:
                max_id = castle_id
        except:
            pass
    
    next_id = max_id + 1
    
    # Process each prefecture
    for prefecture_jp, prefecture_en in PREFECTURES:
        print(f"\n{'='*50}")
        print(f"Processing {prefecture_jp} ({prefecture_en})")
        
        # Scrape castles for this prefecture
        prefecture_castles = scrape_prefecture_castles(prefecture_jp, prefecture_en)
        
        # Assign IDs to new castles
        for castle in prefecture_castles:
            if not castle['ID'] or not castle['ID'].isdigit():
                castle['ID'] = str(next_id)
                next_id += 1
        
        all_castles.extend(prefecture_castles)
        print(f"Total castles for {prefecture_jp}: {len(prefecture_castles)}")
        
        # Save progress after each prefecture
        save_data(all_castles, 'all_japan_castles.csv')
        
        time.sleep(3)  # Longer pause between prefectures
    
    # Final save and summary
    save_data(all_castles, 'all_japan_castles.csv')
    
    # Also save as JSON
    with open('all_japan_castles.json', 'w', encoding='utf-8') as f:
        json.dump(all_castles, f, ensure_ascii=False, indent=2)
    print(f"Also saved to all_japan_castles.json")
    
    # Print summary
    print(f"\n{'='*50}")
    print("FINAL SUMMARY")
    print(f"{'='*50}")
    print(f"Total castles collected: {len(all_castles)}")
    
    # Count by prefecture
    prefecture_counts = {}
    for castle in all_castles:
        pref = castle['都道府県']
        prefecture_counts[pref] = prefecture_counts.get(pref, 0) + 1
    
    print("\nCastles by Prefecture:")
    for pref, count in sorted(prefecture_counts.items()):
        print(f"  {pref}: {count}")

if __name__ == "__main__":
    main()