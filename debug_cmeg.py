#!/usr/bin/env python3
"""Debug script to understand cmeg.jp structure"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def debug_page(url):
    """Fetch and analyze page structure"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")
        print(f"Title: {soup.title.string if soup.title else 'No title'}")
        print("\n" + "="*50 + "\n")
        
        # Find main content area
        main_areas = ['main', 'article', 'content', 'container', 'wrapper']
        for area in main_areas:
            elem = soup.find(area) or soup.find('div', {'class': area}) or soup.find('div', {'id': area})
            if elem:
                print(f"Found {area} element")
                
        # Look for castle-related elements
        print("\nSearching for castle elements...")
        
        # Find all links containing castle IDs
        castle_links = soup.find_all('a', href=lambda x: x and '/castles/' in x)
        print(f"Found {len(castle_links)} castle links")
        
        if castle_links:
            for i, link in enumerate(castle_links[:5]):  # Show first 5
                print(f"  {i+1}. {link.get_text(strip=True)} - {link.get('href')}")
        
        # Look for list items or divs containing 城
        castle_items = soup.find_all(text=lambda x: x and '城' in x)
        print(f"\nFound {len(castle_items)} elements containing '城'")
        
        # Save HTML for manual inspection
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\nFull HTML saved to debug_page.html")
        
    except Exception as e:
        print(f"Error: {e}")

# Test with Fukushima
url = f"https://cmeg.jp/w/castles/{quote('福島県')}"
debug_page(url)