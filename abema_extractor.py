#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AbemaTV メタ情報抽出ツール - メインスクリプト

AbemaTVのアニメやドラマのページから、タイトル、エピソード情報、あらすじなどを抽出し、
動画ファイルのメタデータ更新等に利用可能な形式で保存します。
"""

from abema_metadata.cli import main

if __name__ == '__main__':
    main()