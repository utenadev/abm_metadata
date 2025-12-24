#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AbemaTV Episode Extractor
Usage:
    python3 abema_extractor.py [-h] [--url URL] [--output OUTPUT]
"""

import urllib.request
import re
import yaml
import argparse
import sys

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

def extract_episodes(url, output='episodes_output.yaml', fetch_synopsis_flag=True):
    """AbemaTVページからエピソード情報を抽出"""

    print(f"フェッチ中: {url}")

    content = fetch_page(url)

    # シリーズタイトルを抽出
    series_title = "アニメ・ドラマ"
    for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
        json_script = match.group(1)
        if '"@type":"BreadcrumbList"' in json_script:
            if '"name":"' in json_script:
                name_matches = re.findall(r'"name":"([^"]+)"', json_script)
                for name in name_matches:
                    if name not in ['ホーム', 'アニメ', 'ドラマ'] and len(name) > 5:
                        series_title = name
                        break

    print(f"\nシリーズタイトル: {series_title}")
    print("エピソード情報を抽出しています...\n")

    # エピソード情報を抽出
    episode_list = []

    for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
        json_script = match.group(1)

        if 'caption' in json_script:
            caption_match = re.search(r'"caption"\s*:\s*"([^"]+)"', json_script)
            if caption_match:
                caption = caption_match.group(1)

                # 話数・タイトルを抽出（より一般的なパターン）
                if '第' in caption and '話' in caption:
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

                        if not episode_id:
                            series_id_match = re.search(r'/title/([^/]+)', url)
                            series_id = series_id_match.group(1) if series_id_match else 'unknown'
                            episode_id = f'{series_id}_s1_p{episode_num}'

                        episode_url = f'https://abema.tv/video/episode/{episode_id}'

                        episode_list.append({
                            'episode_num': episode_num,
                            'title': title,
                            'url': episode_url,
                            'thumbnail': thumbnail_url
                        })

    # ソート
    episode_list.sort(key=lambda x: x['episode_num'])

    if not episode_list:
        print("エピソード情報が見つかりませんでした")
        return

    print(f"エピソード数: {len(episode_list)}")

    # あらすじ取得
    synopsis_count = 0
    if fetch_synopsis_flag:
        print("\nあらすじを取得しています...")
        for ep in episode_list[:50]:  # 最大50話
            synopsis = fetch_synopsis(ep['url'])
            ep['synopsis'] = synopsis if synopsis else "(取得できませんでした)"
            synopsis_count += 1
            print(f"  第{ep['episode_num']}話: 完了")
            if synopsis_count >= 50:
                break
    else:
        for ep in episode_list:
            ep['synopsis'] = "(skip)"

    # YAML出力
    yaml_data = {
        'series_title': series_title,
        'source_url': url,
        'total_episodes': len(episode_list),
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

    # ファイルに保存
    with open(output, 'w', encoding='utf-8') as f:
        f.write(f"# {series_title} - AbemaTV エピソード情報\n")
        f.write(f"# データソース: {url}\n")
        f.write(f"# 取得日時: 2025-12-24\n\n")
        f.write(yaml_output)

    print(f"\n{'='*80}")
    print(f"完了しました！")
    print(f"出力ファイル: {output}")
    print(f"合計 {len(episode_list)} 話、あらすじ {synopsis_count if fetch_synopsis_flag else 'skipping'} 個")

def main():
    parser = argparse.ArgumentParser(
        description='AbemaTVのアニメ・ドラマページから話数タイトルとあらすじを抽出します',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python3 abema_extractor.py --url https://abema.tv/video/title/26-249
  python3 abema_extractor.py --url https://abema.tv/video/title/189-85 --output output.yaml
  python3 abema_extractor.py --url https://abema.tv/video/title/26-249 --no-synopsis
        """
    )

    parser.add_argument('--url', '-u',
        dest='url',
        default='https://abema.tv/video/title/26-249',
        help='AbemaTVのアニメ・ドラマのURL (デフォルト: 瑠璃の宝石)')

    parser.add_argument('--output', '-o',
        dest='output',
        default='episodes_output.yaml',
        help='出力ファイル名 (デフォルト: episodes_output.yaml)')

    parser.add_argument('--no-synopsis',
        dest='no_synopsis',
        action='store_true',
        help='あらすじを取得しない（高速処理）')

    args = parser.parse_args()

    try:
        extract_episodes(args.url, args.output, not args.no_synopsis)
    except KeyboardInterrupt:
        print("\n中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()