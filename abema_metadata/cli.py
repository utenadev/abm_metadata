# -*- coding: utf-8 -*-
"""
AbemaTV メタ情報抽出ツールのコマンドラインインターフェース
"""

import argparse
import yaml
import sys
from .extractor import AbemaMetadataExtractor


def main():
    """メインのエントリーポイント"""
    parser = argparse.ArgumentParser(
        description='AbemaTVからシリーズ情報を抽出し、YAML形式で出力します。',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'url',
        help='AbemaTVのシリーズページURL (例: https://abema.tv/video/title/189-85)'
    )

    parser.add_argument(
        '-o', '--output',
        default='episodes_output.yaml',
        help='出力先YAMLファイル名 (デフォルト: episodes_output.yaml)'
    )

    parser.add_argument(
        '--no-synopsis',
        action='store_true',
        help='あらすじの取得をスキップ（高速に取得したい場合）'
    )

    args = parser.parse_args()

    try:
        # メタ情報抽出の実行
        print(f"抽出を開始します: {args.url}")
        extractor = AbemaMetadataExtractor()
        metadata = extractor.extract_all_metadata(args.url, not args.no_synopsis)

        # 出力用データの構築
        output_data = {
            'series_title': metadata.title,
            'source_url': metadata.source_url,
            'extraction_date': metadata.extraction_date,
            'total_episodes': len(metadata.episodes),
            'episodes': [
                {
                    'episode_number': ep.number,
                    'title': ep.title,
                    'synopsis': ep.synopsis or 'あらすじなし',
                    'url': ep.url
                }
                for ep in metadata.episodes
            ]
        }

        # YAMLファイルとして保存
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

        print(f"\nメタ情報の抽出が正常に完了しました: {args.output}")
        print(f"シリーズ名: {metadata.title}")
        print(f"総話数    : {len(metadata.episodes)}")
        print(f"あらすじ  : {'取得済み' if not args.no_synopsis else 'なし'}")

    except KeyboardInterrupt:
        print("\nユーザーによって中断されました。")
        sys.exit(1)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()