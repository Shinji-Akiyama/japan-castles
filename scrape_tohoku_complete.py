#!/usr/bin/env python3
"""
Scrape complete data for Tohoku prefectures
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import re
from urllib.parse import quote

# Tohoku prefectures to scrape
TOHOKU_PREFECTURES = [
    ('青森県', 'Aomori'),
    ('岩手県', 'Iwate'),
    ('宮城県', 'Miyagi'),
    ('秋田県', 'Akita'),
    ('山形県', 'Yamagata'),
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
        text = link.get_text(strip=True)
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
    
    resultboxes = soup.find_all('div', class_='resultbox')
    
    for resultbox in resultboxes:
        castle = extract_castle_from_resultbox(resultbox, prefecture_jp)
        if castle['城名']:
            castles.append(castle)
    
    print(f"    Found {len(castles)} castles")
    return castles

def scrape_prefecture_castles(prefecture_jp, prefecture_en):
    """Scrape all castles for a given prefecture with pagination"""
    all_castles = []
    page = 1
    base_url = f"https://cmeg.jp/w/castles/{quote(prefecture_jp)}"
    
    while True:
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}/{page}"
        
        page_castles = scrape_prefecture_page(url, prefecture_jp)
        
        if not page_castles:
            break
        
        all_castles.extend(page_castles)
        
        if len(page_castles) < 30:
            break
        
        page += 1
        time.sleep(2)
    
    return all_castles

def main():
    """Main function"""
    print("Tohoku Prefecture Castle Data Collection")
    print("=" * 50)
    
    tohoku_castles = []
    
    # Process each Tohoku prefecture
    for prefecture_jp, prefecture_en in TOHOKU_PREFECTURES:
        print(f"\n{'='*50}")
        print(f"Processing {prefecture_jp} ({prefecture_en})")
        
        prefecture_castles = scrape_prefecture_castles(prefecture_jp, prefecture_en)
        tohoku_castles.extend(prefecture_castles)
        
        print(f"Total castles for {prefecture_jp}: {len(prefecture_castles)}")
        time.sleep(3)
    
    # Save Tohoku data separately
    with open('tohoku_castles_complete.csv', 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['ID', '都道府県', '城名', '読み方', '種類', '所在地', '築城年代', '城主・築城者', '別名', '備考']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tohoku_castles)
    
    print(f"\n{'='*50}")
    print(f"Total Tohoku castles collected: {len(tohoku_castles)}")
    print(f"Saved to tohoku_castles_complete.csv")
    
    # Summary by prefecture
    prefecture_counts = {}
    for castle in tohoku_castles:
        pref = castle['都道府県']
        prefecture_counts[pref] = prefecture_counts.get(pref, 0) + 1
    
    print("\nCastles by Prefecture:")
    for pref, count in sorted(prefecture_counts.items()):
        print(f"  {pref}: {count}")

if __name__ == "__main__":
    main()