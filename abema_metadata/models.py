# -*- coding: utf-8 -*-
"""
Data models for AbemaTV metadata extraction
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class EpisodeMetadata:
    """エピソードのメタ情報"""
    number: int
    title: str
    synopsis: Optional[str] = None
    url: Optional[str] = None


@dataclass
class SeriesMetadata:
    """シリーズのメタ情報"""
    title: str
    source_url: str
    extraction_date: str
    episodes: List[EpisodeMetadata]