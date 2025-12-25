# -*- coding: utf-8 -*-
"""
AbemaTVのメタ情報抽出に使用するデータモデル定義
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EpisodeMetadata:
    """各エピソードのメタ情報を保持するクラス"""
    number: int                 # 話数
    title: str                 # サブタイトル
    synopsis: Optional[str] = None  # あらすじ
    url: Optional[str] = None       # エピソードの個別URL


@dataclass
class SeriesMetadata:
    """シリーズ全体のメタ情報を保持するクラス"""
    title: str                          # シリーズタイトル
    source_url: str                     # 抽出元のシリーズURL
    extraction_date: str                # 抽出実施日 (YYYY-MM-DD)
    episodes: List[EpisodeMetadata] = field(default_factory=list)  # 全エピソードのリスト