#!/usr/bin/env python3
"""
Comprehensive castle data scraper for cmeg.jp
Collects castle data from ALL Japanese prefectures with pagination handling
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin

# All Japanese prefectures organized by region
PREFECTURES = {
    'Tohoku': {
        '福島県': 'fukushima'
    },
    'Kanto': {
        '茨城県': 'ibaraki',
        '栃木県': 'tochigi', 
        '群馬県': 'gunma',
        '埼玉県': 'saitama',
        '千葉県': 'chiba',
        '東京都': 'tokyo',
        '神奈川県': 'kanagawa'
    },
    'Chubu': {
        '新潟県': 'niigata',
        '富山県': 'toyama',
        '石川県': 'ishikawa',
        '福井県': 'fukui',
        '山梨県': 'yamanashi',
        '長野県': 'nagano',
        '岐阜県': 'gifu',
        '静岡県': 'shizuoka',
        '愛知県': 'aichi'
    },
    'Kinki': {
        '三重県': 'mie',
        '滋賀県': 'shiga',
        '京都府': 'kyoto',
        '大阪府': 'osaka',
        '兵庫県': 'hyogo',
        '奈良県': 'nara',
        '和歌山県': 'wakayama'
    },
    'Chugoku': {
        '鳥取県': 'tottori',
        '島根県': 'shimane',
        '岡山県': 'okayama',
        '広島県': 'hiroshima',
        '山口県': 'yamaguchi'
    },
    'Shikoku': {
        '徳島県': 'tokushima',
        '香川県': 'kagawa',
        '愛媛県': 'ehime',
        '高知県': 'kochi'
    },
    'Kyushu': {
        '福岡県': 'fukuoka',
        '佐賀県': 'saga',
        '長崎県': 'nagasaki',
        '熊本県': 'kumamoto',
        '大分県': 'oita',
        '宮崎県': 'miyazaki',
        '鹿児島県': 'kagoshima',
        '沖縄県': 'okinawa'
    }
}

# We already have data from these prefectures in Tohoku
ALREADY_COLLECTED = ['青森県', '岩手県', '宮城県', '秋田県', '山形県']

def get_page_content(url):
    """Fetch page content with retry logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(5)
    return None

def extract_castle_data(soup, prefecture_name):
    """Extract castle data from a page"""
    castles = []
    
    # Find all castle entries - they're usually in table rows or list items
    # Try multiple selectors to handle different page structures
    castle_elements = soup.select('table tr') or soup.select('ul li') or soup.select('.castle-item')
    
    for element in castle_elements:
        # Skip header rows
        if element.find('th'):
            continue
            
        castle_data = {
            'ID': '',
            '都道府県': prefecture_name,
            '城名': '',
            '読み方': '',
            '種類': '',
            '所在地': '',
            '築城年代': '',
            '城主・築城者': '',
            '別名': '',
            '備考': ''
        }
        
        # Extract text from the element
        text = element.get_text(strip=True, separator=' ')
        
        # Try to extract castle name (usually a link)
        castle_link = element.find('a')
        if castle_link:
            castle_data['城名'] = castle_link.get_text(strip=True)
            
            # Extract ID from URL if available
            href = castle_link.get('href', '')
            id_match = re.search(r'(\d+)', href)
            if id_match:
                castle_data['ID'] = id_match.group(1)
        
        # Extract other data from table cells or text
        cells = element.find_all('td')
        if cells:
            # Typical table structure
            for i, cell in enumerate(cells):
                cell_text = cell.get_text(strip=True)
                if i == 0 and not castle_data['城名']:
                    castle_data['城名'] = cell_text
                elif i == 1:
                    castle_data['読み方'] = cell_text
                elif i == 2:
                    castle_data['種類'] = cell_text
                elif i == 3:
                    castle_data['所在地'] = cell_text
                elif i == 4:
                    castle_data['築城年代'] = cell_text
                elif i == 5:
                    castle_data['城主・築城者'] = cell_text
                elif i == 6:
                    castle_data['別名'] = cell_text
                elif i == 7:
                    castle_data['備考'] = cell_text
        
        # Only add if we found a castle name
        if castle_data['城名']:
            castles.append(castle_data)
    
    return castles

def get_all_pages_for_prefecture(base_url, prefecture_name):
    """Get all castle data from all pages for a prefecture"""
    all_castles = []
    page_num = 1
    
    while True:
        # Construct page URL
        if page_num == 1:
            url = base_url
        else:
            # Try different pagination patterns
            url = f"{base_url}?page={page_num}" if '?' not in base_url else f"{base_url}&page={page_num}"
        
        print(f"  Fetching page {page_num}: {url}")
        content = get_page_content(url)
        
        if not content:
            print(f"  Failed to fetch page {page_num}")
            break
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract castles from this page
        page_castles = extract_castle_data(soup, prefecture_name)
        
        if not page_castles:
            print(f"  No castles found on page {page_num}")
            break
        
        all_castles.extend(page_castles)
        print(f"  Found {len(page_castles)} castles on page {page_num}")
        
        # Check for next page link
        next_link = soup.find('a', text=re.compile(r'次|next|→'))
        if not next_link or 'disabled' in next_link.get('class', []):
            break
        
        page_num += 1
        time.sleep(2)  # Be polite to the server
    
    return all_castles

def main():
    """Main scraping function"""
    all_castles = []
    castle_id = 1
    
    # Read existing data
    print("Reading existing data...")
    try:
        with open('castle_data.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert to new format
                castle_data = {
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
                all_castles.append(castle_data)
                castle_id += 1
        print(f"Loaded {len(all_castles)} existing castles")
    except Exception as e:
        print(f"Could not read existing data: {e}")
    
    # Scrape new data
    for region, prefectures in PREFECTURES.items():
        print(f"\n=== Processing {region} Region ===")
        
        for prefecture_jp, prefecture_en in prefectures.items():
            if prefecture_jp in ALREADY_COLLECTED:
                print(f"Skipping {prefecture_jp} - already collected")
                continue
            
            print(f"\nProcessing {prefecture_jp} ({prefecture_en})...")
            
            # Try different URL patterns
            urls_to_try = [
                f"https://cmeg.jp/w/{prefecture_en}",
                f"https://cmeg.jp/castles/{prefecture_en}",
                f"https://cmeg.jp/{prefecture_en}",
                f"https://cmeg.jp/list/{prefecture_en}"
            ]
            
            prefecture_castles = []
            for url in urls_to_try:
                prefecture_castles = get_all_pages_for_prefecture(url, prefecture_jp)
                if prefecture_castles:
                    break
            
            # Assign IDs to new castles
            for castle in prefecture_castles:
                castle['ID'] = str(castle_id)
                castle_id += 1
            
            all_castles.extend(prefecture_castles)
            print(f"Total castles for {prefecture_jp}: {len(prefecture_castles)}")
            
            time.sleep(3)  # Be polite between prefectures
    
    # Save all data
    print(f"\n=== Saving {len(all_castles)} total castles ===")
    
    with open('all_japan_castles.csv', 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['ID', '都道府県', '城名', '読み方', '種類', '所在地', '築城年代', '城主・築城者', '別名', '備考']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_castles)
    
    print(f"Data saved to all_japan_castles.csv")
    
    # Print summary
    prefecture_counts = {}
    for castle in all_castles:
        pref = castle['都道府県']
        prefecture_counts[pref] = prefecture_counts.get(pref, 0) + 1
    
    print("\n=== Summary by Prefecture ===")
    for pref, count in sorted(prefecture_counts.items()):
        print(f"{pref}: {count} castles")

if __name__ == "__main__":
    main()