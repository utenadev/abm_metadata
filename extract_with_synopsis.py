#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import re
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
        for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
            json_script = match.group(1)
            if 'description' in json_script:
                desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', json_script)
                if desc_match:
                    description = desc_match.group(1)
                    description = description.replace('\\n', '\n')
                    description = description.encode('utf-8').decode('unicode_escape') if '\\u' in description else description
                    return description
    except Exception as e:
        pass
    return None

# メイン処理
url = 'https://abema.tv/video/title/26-249'

series_title = '瑠璃の宝石'

print("フェッチ中:", url)
content = fetch_page(url)

print("\nエピソード情報を抽出しています...")

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
if episode_list:
    print(f"\nあらすじを取得しています...")

    for ep in episode_list:
        synopsis = fetch_synopsis(ep['url'])
        ep['synopsis'] = synopsis if synopsis else "取得できませんでした"
        print(f"  第{ep['episode_num']}話: 完了")

    # テキストファイルに出力
    with open('/home/kench/workspace/abm_pgmdesc/episodes_with_synopsis.txt', 'w', encoding='utf-8') as f:
        f.write("瑠璃の宝石 - 全話数タイトル・あらすじリスト\n")
        f.write("="*80 + "\n\n")

        for ep in episode_list:
            f.write(f"第{ep['episode_num']:2d}話: {ep['title']}\n")
            f.write(f"URL: {ep['url']}\n\n")
            f.write(f"あらすじ:\n{ep['synopsis']}\n\n")
            f.write("="*80 + "\n\n")

        f.write(f"合計 {len(episode_list)} 話\n")

    print(f"\n合計 {len(episode_list)} 話の情報を抽出し、episodes_with_synopsis.txt に保存しました！")
else:
    print("エピソード情報が見つかりませんでした")