#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import re
import json
import yaml

def fetch_page(url):
    """ページを取得して内容を返す"""
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    response = urllib.request.urlopen(req)
    return response.read().decode('utf-8')

def fetch_synopsis(episode_url):
    """エピソードページからあらすじを取得"""
    try:
        content = fetch_page(episode_url)

        # JSON-LDからdescriptionを探す
        json_ld_matches = re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL)
        for match in json_ld_matches:
            json_script = match.group(1)

            # descriptionがあるJSONを探す
            if 'description' in json_script:
                desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', json_script)
                if desc_match:
                    description = desc_match.group(1)
                    # JSONエスケープを処理
                    description = description.replace('\\n', '\n')
                    description = description.replace('\\u', '\\u')
                    description = description.encode('utf-8').decode('unicode_escape') if '\\u' in description else description
                    return description
    except Exception as e:
        pass
    return None

def extract_series_info(content):
    """シリーズ情報を抽出"""
    series_info = {
        'title': '瑠璃の宝石',
        'title_en': 'Ruri no Houseki',
        'url': 'https://abema.tv/video/title/26-249'
    }

    # BreadcrumbListから情報を取得
    for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
        json_script = match.group(1)

        if '"@type":"BreadcrumbList"' in json_script:
            # アニメタイトルを抽出
            if '"name":"' in json_script:
                name_match = re.findall(r'"name":"([^"]+)"', json_script)
                for name in name_match:
                    if '瑠璃の宝石' in name:
                        series_info['title'] = name
                        break

    return series_info

# メイン処理
url = 'https://abema.tv/video/title/26-249'
print("フェッチ中:", url)

content = fetch_page(url)

print("\nエピソード情報を抽出しています...")

# シリーズ情報
series_info = extract_series_info(content)

# エピソード情報を抽出
episode_list = []

for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
    json_script = match.group(1)

    if 'caption' in json_script:
        caption_match = re.search(r'"caption"\s*:\s*"([^"]+)"', json_script)
        if caption_match:
            caption = caption_match.group(1)

            if '瑠璃の宝石' in caption and '第' in caption and '話' in caption:
                episode_match = re.search(r'瑠璃の宝石\s+第(\d+)話\s+(.+?)(?:のサムネイル)?$', caption)

                if episode_match:
                    episode_num = int(episode_match.group(1))
                    title = episode_match.group(2)

                    url_match = re.search(r'"url"\s*:\s*"([^"]+)"', json_script)
                    thumbnail_url = url_match.group(1) if url_match else ''

                    episode_id_match = re.search(r'/programs/(26-249_s1_p\d+)/', thumbnail_url)
                    episode_id = episode_id_match.group(1) if episode_id_match else f'26-249_s1_p{episode_num}'

                    episode_url = f'https://abema.tv/video/episode/{episode_id}'

                    episode_list.append({
                        'episode_num': episode_num,
                        'title': title,
                        'url': episode_url,
                        'thumbnail': thumbnail_url,
                        'synopsis': None
                    })

# ソート
episode_list.sort(key=lambda x: x['episode_num'])

# あらすじ取得
print(f"\nあらすじを取得しています...")

for ep in episode_list:
    synopsis = fetch_synopsis(ep['url'])
    ep['synopsis'] = synopsis if synopsis else "取得できませんでした"
    print(f"  第{ep['episode_num']}話: 完了")

# YAML形式で出力
yaml_data = {
    'series_title': series_info['title'],
    'series_title_en': series_info['title_en'],
    'source_url': series_info['url'],
    'scraping_date': '2025-12-24',
    'episodes': []
}

for ep in episode_list:
    episode_data = {
        'episode_number': ep['episode_num'],
        'title': ep['title'],
        'url': ep['url'],
        'synopsis': ep['synopsis']
    }
    yaml_data['episodes'].append(episode_data)

# YAMLとして出力
yaml_output = yaml.dump(yaml_data, allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2, width=120)

print("\n" + "="*80)
print("YAML形式出力")
print("="*80)
print(yaml_output)

# ファイルに保存
with open('/home/kench/workspace/abm_pgmdesc/episodes_output.yaml', 'w', encoding='utf-8') as f:
    f.write("# 瑠璃の宝石 - アニメ情報\n")
    f.write("# データソース: https://abema.tv/video/title/26-249\n")
    f.write("# 取得日時: 2025-12-24\n\n")
    f.write(yaml_output)

print("\n" + "="*80)
print(f"合計 {len(episode_list)} 話の情報を抽出しました")
print("episodes_output.yaml に保存しました！")