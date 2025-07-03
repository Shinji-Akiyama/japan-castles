#!/usr/bin/env python3
"""
Castle data scraper for cmeg.jp
Collects comprehensive castle data from all Japanese prefectures
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import re
from urllib.parse import urljoin, quote

# Prefecture data with Japanese names and URL encodings
PREFECTURES = [
    # Tohoku (we'll skip already collected ones)
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

# Prefectures we already have data for
ALREADY_COLLECTED = ['青森県', '岩手県', '宮城県', '秋田県', '山形県']

def get_page(url, retries=3):
    """Fetch a web page with retries"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5)
    return None

def extract_castle_info(castle_elem):
    """Extract castle information from a castle element"""
    castle = {
        'ID': '',
        '都道府県': '',
        '城名': '',
        '読み方': '',
        '種類': '',
        '所在地': '',
        '築城年代': '',
        '城主・築城者': '',
        '別名': '',
        '備考': ''
    }
    
    # Extract castle name
    name_elem = castle_elem.find('h3') or castle_elem.find('h4') or castle_elem.find('strong')
    if name_elem:
        castle['城名'] = name_elem.get_text(strip=True)
    
    # Extract castle link and ID
    link_elem = castle_elem.find('a')
    if link_elem:
        href = link_elem.get('href', '')
        # Extract ID from URL like /w/castles/1234
        id_match = re.search(r'/castles/(\d+)', href)
        if id_match:
            castle['ID'] = id_match.group(1)
    
    # Extract details from text
    text_content = castle_elem.get_text(separator='\n', strip=True)
    lines = text_content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Reading (usually in parentheses after castle name)
        if '（' in line and '）' in line and castle['城名'] in line:
            reading_match = re.search(r'（([^）]+)）', line)
            if reading_match:
                castle['読み方'] = reading_match.group(1)
        
        # Location
        if '所在地' in line or any(suffix in line for suffix in ['市', '町', '村', '区']):
            location = line.replace('所在地：', '').replace('所在地', '').strip()
            if location and len(location) > 2:
                castle['所在地'] = location
        
        # Castle type
        if '城' in line and any(type_word in line for type_word in ['平城', '山城', '平山城', '水城', '海城']):
            for type_word in ['平城', '山城', '平山城', '水城', '海城']:
                if type_word in line:
                    castle['種類'] = type_word
                    break
        
        # Alternative names
        if '別名' in line or '別称' in line:
            alt_names = line.replace('別名：', '').replace('別称：', '').replace('別名', '').replace('別称', '').strip()
            castle['別名'] = alt_names
        
        # Construction period
        if '築城' in line or '年' in line:
            period_match = re.search(r'(\d+年|[^、。]+時代|[^、。]+期)', line)
            if period_match:
                castle['築城年代'] = period_match.group(1)
        
        # Lords/builders
        if '城主' in line or '築城者' in line or '氏' in line:
            lords = line.replace('城主：', '').replace('築城者：', '').strip()
            if lords and '氏' in lords:
                castle['城主・築城者'] = lords
    
    return castle

def scrape_prefecture_castles(prefecture_jp, prefecture_en):
    """Scrape all castles for a given prefecture"""
    all_castles = []
    page = 1
    base_url = f"https://cmeg.jp/w/castles/{quote(prefecture_jp)}"
    
    while True:
        # Construct URL with pagination
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}?page={page}"
        
        print(f"  Fetching page {page}: {url}")
        content = get_page(url)
        
        if not content:
            print(f"  Failed to fetch page {page}")
            break
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find castle entries - they're usually in article or div elements
        castle_elements = soup.select('article.castle-item') or \
                         soup.select('div.castle-entry') or \
                         soup.select('div.castle') or \
                         soup.select('li.castle')
        
        # If no specific castle elements, try to find them in the main content
        if not castle_elements:
            main_content = soup.find('main') or soup.find('div', {'class': 'content'}) or soup.find('div', {'id': 'content'})
            if main_content:
                # Look for castle entries in various formats
                castle_elements = main_content.find_all('div', recursive=True)
                castle_elements = [elem for elem in castle_elements if 
                                 elem.find('h3') or elem.find('h4') or 
                                 (elem.get_text() and '城' in elem.get_text())]
        
        if not castle_elements:
            print(f"  No castle elements found on page {page}")
            break
        
        # Extract castle data
        page_castles = []
        for elem in castle_elements:
            castle = extract_castle_info(elem)
            if castle['城名']:  # Only add if we found a castle name
                castle['都道府県'] = prefecture_jp
                page_castles.append(castle)
        
        if not page_castles:
            print(f"  No valid castles found on page {page}")
            break
        
        all_castles.extend(page_castles)
        print(f"  Found {len(page_castles)} castles on page {page}")
        
        # Check for next page
        next_link = soup.find('a', text=re.compile(r'次|Next|→|»'))
        if not next_link or 'disabled' in next_link.get('class', []):
            # Also check for page numbers
            page_links = soup.find_all('a', href=re.compile(r'\?page=\d+'))
            current_page_nums = [int(re.search(r'page=(\d+)', link.get('href', '')).group(1)) 
                               for link in page_links 
                               if re.search(r'page=(\d+)', link.get('href', ''))]
            if current_page_nums and max(current_page_nums) > page:
                page += 1
                time.sleep(2)
                continue
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
        print(f"Loaded {len(existing)} existing castles")
    except Exception as e:
        print(f"Could not load existing data: {e}")
    return existing

def main():
    """Main function to orchestrate the scraping"""
    print("Castle Data Collection from cmeg.jp")
    print("=" * 50)
    
    # Load existing data
    all_castles = load_existing_data()
    next_id = len(all_castles) + 1
    
    # Process each prefecture
    for prefecture_jp, prefecture_en in PREFECTURES:
        if prefecture_jp in ALREADY_COLLECTED:
            print(f"\nSkipping {prefecture_jp} - already collected")
            continue
        
        print(f"\n{'='*50}")
        print(f"Processing {prefecture_jp} ({prefecture_en})")
        print(f"{'='*50}")
        
        # Scrape castles for this prefecture
        prefecture_castles = scrape_prefecture_castles(prefecture_jp, prefecture_en)
        
        # Assign IDs
        for castle in prefecture_castles:
            if not castle['ID']:
                castle['ID'] = str(next_id)
                next_id += 1
        
        all_castles.extend(prefecture_castles)
        print(f"Total castles for {prefecture_jp}: {len(prefecture_castles)}")
        
        # Save progress after each prefecture
        save_data(all_castles)
        
        time.sleep(3)  # Longer pause between prefectures
    
    # Final summary
    print_summary(all_castles)

def save_data(castles):
    """Save castle data to CSV and JSON"""
    # Save to CSV
    csv_filename = 'all_japan_castles.csv'
    with open(csv_filename, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['ID', '都道府県', '城名', '読み方', '種類', '所在地', '築城年代', '城主・築城者', '別名', '備考']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(castles)
    print(f"  Saved {len(castles)} castles to {csv_filename}")
    
    # Save to JSON
    json_filename = 'all_japan_castles.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(castles, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {json_filename}")

def print_summary(castles):
    """Print summary statistics"""
    print(f"\n{'='*50}")
    print("FINAL SUMMARY")
    print(f"{'='*50}")
    print(f"Total castles collected: {len(castles)}")
    
    # Count by prefecture
    prefecture_counts = {}
    for castle in castles:
        pref = castle['都道府県']
        prefecture_counts[pref] = prefecture_counts.get(pref, 0) + 1
    
    print("\nCastles by Prefecture:")
    for pref, count in sorted(prefecture_counts.items()):
        print(f"  {pref}: {count}")

if __name__ == "__main__":
    main()