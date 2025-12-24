#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import re

url = 'https://abema.tv/video/title/26-249'

print("フェッチ中:", url)
req = urllib.request.Request(
    url,
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
)

response = urllib.request.urlopen(req)
content = response.read().decode('utf-8')

print("\n" + "="*80)
print("瑠璃の宝石 - 話数タイトル抽出結果")
print("="*80 + "\n")

# JSON-LDからcaptionを探す
episode_list = []

for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
    json_script = match.group(1)

    # captionに話数情報があるものを探す
    if 'caption' in json_script:
        caption_match = re.search(r'"caption"\s*:\s*"([^"]+)"', json_script)
        if caption_match:
            caption = caption_match.group(1)

            # 瑠璃の宝石のエピソードかを確認
            if '瑠璃の宝石' in caption and '第' in caption and '話' in caption:
                # 話数とタイトルを抽出
                episode_match = re.search(r'瑠璃の宝石\s+第(\d+)話\s+(.+?)(?:のサムネイル)?$', caption)

                if episode_match:
                    episode_num = int(episode_match.group(1))
                    title = episode_match.group(2)

                    # URLを探す
                    url_match = re.search(r'"url"\s*:\s*"([^"]+)"', json_script)
                    thumbnail_url = url_match.group(1) if url_match else ''

                    # エピソードIDを抽出
                    episode_id_match = re.search(r'/programs/(26-249_s1_p\d+)/', thumbnail_url)
                    episode_id = episode_id_match.group(1) if episode_id_match else f'26-249_s1_p{episode_num}'

                    episode_list.append({
                        'episode_num': episode_num,
                        'title': title,
                        'url': f'https://abema.tv/video/episode/{episode_id}',
                        'thumbnail': thumbnail_url
                    })

# ソート
episode_list.sort(key=lambda x: x['episode_num'])

# 結果表示
if episode_list:
    print("クイックサマリ:")
    print("-"*80)
    for ep in episode_list:
        print(f"第{ep['episode_num']:2d}話: {ep['title']}")
    print("\n")

    print("詳細情報:")
    print("="*80 + "\n")

    for ep in episode_list:
        print(f"第{ep['episode_num']}話\t{ep['title']}")
        print("-"*80)
        print(f"URL:\t\t{ep['url']}")
        print(f"サムネイル:\t{ep['thumbnail']}")
        print("あらすじ:\t(個別ページから取得可能)")
        print("="*80 + "\n")

    print(f"合計 {len(episode_list)} 話の情報を抽出しました\n")

    # ファイルに保存
    with open('/home/kench/workspace/abm_pgmdesc/episodes_list.txt', 'w', encoding='utf-8') as f:
        f.write("瑠璃の宝石 - 全話数タイトルリスト\n")
        f.write("="*80 + "\n\n")

        for ep in episode_list:
            f.write(f"第{ep['episode_num']:2d}話: {ep['title']:<25} {ep['url']}\n")

        f.write(f"\n合計 {len(episode_list)} 話\n")

    print("episodes_list.txt に保存しました！")

else:
    print("エピソード情報が見つかりませんでした")
    print("HTML構造が変更されている可能性があります")