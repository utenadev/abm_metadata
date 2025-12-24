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

url = 'https://abema.tv/video/title/189-85'
print("テスティングフェッチ中:", url)

content = fetch_page(url)

print("\n" + "="*80)
print("テスト - 話数タイトル・あらすじ抽出")
print("="*80 + "\n")

# シリーズタイトルを抽出
series_title = "不明"
for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
    json_script = match.group(1)
    if '"@type":"BreadcrumbList"' in json_script:
        if '"name":"' in json_script:
            name_matches = re.findall(r'"name":"([^"]+)"', json_script)
            for name in name_matches:
                if name not in ['ホーム', 'アニメ'] and len(name) > 5:
                    series_title = name
                    break

print(f"シリーズタイトル: {series_title}\n")

# エピソード情報を抽出
episode_list = []

for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
    json_script = match.group(1)

    if 'caption' in json_script:
        caption_match = re.search(r'"caption"\s*:\s*"([^"]+)"', json_script)
        if caption_match:
            caption = caption_match.group(1)

            # 話数・タイトルを抽出
            if '第' in caption and '話' in caption:
                # より一般的なパターンに対応
                title_match = re.search(r'(?:[\w\s]+)?第(\d+)話\s*(.+?)(?:のサムネイル)?$', caption)

                if title_match:
                    episode_num = int(title_match.group(1))
                    title = title_match.group(2)

                    url_match = re.search(r'"url"\s*:\s*"([^"]+)"', json_script)
                    thumbnail_url = url_match.group(1) if url_match else ''

                    # エピソードIDを抽出
                    episode_id = None
                    if '/programs/' in thumbnail_url:
                        ep_id_match = re.search(r'/programs/([^/]+)/', thumbnail_url)
                        episode_id = ep_id_match.group(1) if ep_id_match else None

                    if not episode_id and series_title != "不明":
                        episode_id = f'189-85_s1_p{episode_num}'

                    episode_url = f'https://abema.tv/video/episode/{episode_id}' if episode_id else None

                    if episode_url:
                        episode_list.append({
                            'episode_num': episode_num,
                            'title': title,
                            'url': episode_url,
                            'thumbnail': thumbnail_url
                        })

# ソート
episode_list.sort(key=lambda x: x['episode_num'])

if episode_list:
    print(f"エピソード数: {len(episode_list)}\n")

    # サマリ
    print("サマリ:")
    print("-"*80)
    for ep in episode_list[:10]:  # 最初の10話
        print(f"第{ep['episode_num']:2d}話: {ep['title']}")

    if len(episode_list) > 10:
        print(f"... and {len(episode_list) - 10} more episodes")

    # YAML出力
    yaml_data = {
        'series_title': series_title,
        'source_url': url,
        'total_episodes': len(episode_list),
        'episodes': episode_list[:50]  # 最大50話
    }

    output_file = '/home/kench/workspace/abm_pgmdesc/test_output.yaml'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# {series_title} - テスト結果\n")
        f.write(f"# データソース: {url}\n\n")
        f.write(yaml.dump(yaml_data, allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2, width=120))

    print("\n" + "="*80)
    print(f"test_output.yaml に保存しました！ (合計 {len(episode_list)} 話)")
else:
    print("エピソード情報が見つかりませんでした")