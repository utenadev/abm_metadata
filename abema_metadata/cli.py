# -*- coding: utf-8 -*-
"""
Command-line interface for AbemaTV metadata extraction
"""

import argparse
import yaml
import sys
from .extractor import AbemaMetadataExtractor
from .models import SeriesMetadata


def main():
    parser = argparse.ArgumentParser(
        description='AbemaTVから動画ファイル用メタ情報を抽出',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'url',
        help='AbemaTVのアニメ/ドラマページURL'
    )

    parser.add_argument(
        '-o', '--output',
        default='metadata.yaml',
        help='出力YAMLファイル名 (デフォルト: metadata.yaml)'
    )

    parser.add_argument(
        '--no-synopsis',
        action='store_true',
        help='あらすじを取得しない（高速処理）'
    )

    args = parser.parse_args()

    try:
        # メタ情報抽出
        extractor = AbemaMetadataExtractor()
        metadata = extractor.extract_all_metadata(args.url, not args.no_synopsis)

        # YAML出力
        output_data = {
            'series_title': metadata.title,
            'source_url': metadata.source_url,
            'extraction_date': metadata.extraction_date,
            'total_episodes': len(metadata.episodes),
            'episodes': [
                {
                    'episode_number': ep.number,
                    'title': ep.title,
                    'synopsis': ep.synopsis or 'あらすじなし'
                }
                for ep in metadata.episodes
            ]
        }

        # ファイルに保存
        with open(args.output, 'w', encoding='utf-8') as f:
            yaml.dump(
                output_data,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
                width=120
            )

        print(f"メタ情報の抽出が完了しました: {args.output}")
        print(f"シリーズ: {metadata.title}")
        print(f"エピソード数: {len(metadata.episodes)}")
        print(f"あらすじ: {'含む' if not args.no_synopsis else '含まない'}")

    except KeyboardInterrupt:
        print("\n処理が中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()