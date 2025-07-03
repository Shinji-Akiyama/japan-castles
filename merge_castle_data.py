#!/usr/bin/env python3
"""
Merge all castle data into a single comprehensive CSV file
"""

import csv
import json

def load_csv_data(filename):
    """Load castle data from CSV file"""
    castles = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                castles.append(dict(row))
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    return castles

def main():
    print("Merging castle data...")
    
    # Load the main data (which has incomplete Tohoku data)
    main_castles = load_csv_data('all_japan_castles.csv')
    print(f"Loaded {len(main_castles)} castles from main file")
    
    # Load complete Tohoku data
    tohoku_castles = load_csv_data('tohoku_castles_complete.csv')
    print(f"Loaded {len(tohoku_castles)} Tohoku castles")
    
    # Remove old Tohoku entries from main data
    tohoku_prefectures = ['青森県', '岩手県', '宮城県', '秋田県', '山形県']
    filtered_castles = [c for c in main_castles if c['都道府県'] not in tohoku_prefectures]
    print(f"Filtered to {len(filtered_castles)} non-Tohoku castles")
    
    # Combine all data
    all_castles = tohoku_castles + filtered_castles
    
    # Re-assign IDs sequentially
    for i, castle in enumerate(all_castles, 1):
        castle['ID'] = str(i)
    
    # Sort by prefecture for better organization
    prefecture_order = [
        # Tohoku
        '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
        # Kanto
        '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
        # Chubu
        '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県', '静岡県', '愛知県',
        # Kinki
        '三重県', '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県',
        # Chugoku
        '鳥取県', '島根県', '岡山県', '広島県', '山口県',
        # Shikoku
        '徳島県', '香川県', '愛媛県', '高知県',
        # Kyushu/Okinawa
        '福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
    ]
    
    # Create prefecture index
    pref_index = {pref: i for i, pref in enumerate(prefecture_order)}
    
    # Sort castles
    all_castles.sort(key=lambda c: (pref_index.get(c['都道府県'], 999), c['城名']))
    
    # Re-assign IDs after sorting
    for i, castle in enumerate(all_castles, 1):
        castle['ID'] = str(i)
    
    # Save final comprehensive data
    fieldnames = ['ID', '都道府県', '城名', '読み方', '種類', '所在地', '築城年代', '城主・築城者', '別名', '備考']
    
    # Save as CSV
    with open('japan_castles_complete.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_castles)
    
    # Save as JSON
    with open('japan_castles_complete.json', 'w', encoding='utf-8') as f:
        json.dump(all_castles, f, ensure_ascii=False, indent=2)
    
    # Print final summary
    print(f"\n{'='*50}")
    print("FINAL COMPREHENSIVE CASTLE DATABASE")
    print(f"{'='*50}")
    print(f"Total castles: {len(all_castles)}")
    
    # Count by prefecture
    prefecture_counts = {}
    for castle in all_castles:
        pref = castle['都道府県']
        prefecture_counts[pref] = prefecture_counts.get(pref, 0) + 1
    
    print("\nCastles by Region:")
    
    regions = {
        'Tohoku': ['青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県'],
        'Kanto': ['茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県'],
        'Chubu': ['新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県', '静岡県', '愛知県'],
        'Kinki': ['三重県', '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県'],
        'Chugoku': ['鳥取県', '島根県', '岡山県', '広島県', '山口県'],
        'Shikoku': ['徳島県', '香川県', '愛媛県', '高知県'],
        'Kyushu/Okinawa': ['福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県']
    }
    
    for region, prefectures in regions.items():
        print(f"\n{region}:")
        region_total = 0
        for pref in prefectures:
            if pref in prefecture_counts:
                count = prefecture_counts[pref]
                region_total += count
                print(f"  {pref}: {count}")
        print(f"  Regional Total: {region_total}")
    
    print(f"\n{'='*50}")
    print(f"Files created:")
    print(f"  - japan_castles_complete.csv")
    print(f"  - japan_castles_complete.json")

if __name__ == "__main__":
    main()