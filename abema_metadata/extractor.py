# -*- coding: utf-8 -*-
"""
Core extraction functionality for AbemaTV metadata
"""

import urllib.request
import re
from typing import Optional, List
from datetime import datetime
from .models import SeriesMetadata, EpisodeMetadata


class AbemaMetadataExtractor:
    """AbemaTVからメタ情報を抽出するコアクラス"""

    def __init__(self, user_agent: Optional[str] = None):
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    def fetch_page(self, url: str) -> str:
        """ウェブページを取得"""
        req = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')

    def extract_series_title(self, content: str) -> str:
        """シリーズタイトルを抽出"""
        for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
            json_script = match.group(1)
            if '"@type":"BreadcrumbList"' in json_script:
                name_matches = re.findall(r'"name":"([^"]+)"', json_script)
                for name in name_matches:
                    if name not in ['ホーム', 'アニメ', 'ドラマ'] and len(name) > 3:
                        return name
        return "不明なシリーズ"

    def extract_episodes(self, content: str, series_url: str) -> List[EpisodeMetadata]:
        """エピソード情報を抽出"""
        episodes = []

        for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
            json_script = match.group(1)

            if 'caption' in json_script:
                caption_match = re.search(r'"caption"\s*:\s*"([^"]+)"', json_script)
                if caption_match:
                    caption = caption_match.group(1)

                    # 話数・タイトルを抽出（汎用パターン）
                    if '第' in caption and '話' in caption:
                        title_match = re.search(r'(?:[\w\s]+)?第(\d+)話\s*(.+?)(?:のサムネイル)?$', caption)
                        if title_match:
                            episode_num = int(title_match.group(1))
                            title = title_match.group(2)

                            # URLを抽出
                            url_match = re.search(r'"url"\s*:\s*"([^"]+)"', json_script)
                            thumbnail_url = url_match.group(1) if url_match else ''

                            # エピソードIDを生成
                            episode_id = self._generate_episode_id(thumbnail_url, series_url, episode_num)

                            episodes.append(EpisodeMetadata(
                                number=episode_num,
                                title=title,
                                url=f'https://abema.tv/video/episode/{episode_id}' if episode_id else None
                            ))

        return sorted(episodes, key=lambda x: x.number)

    def _generate_episode_id(self, thumbnail_url: str, series_url: str, episode_num: int) -> Optional[str]:
        """エピソードIDを生成"""
        # URLからシリーズIDを抽出
        series_id_match = re.search(r'/title/([^/]+)', series_url)
        series_id = series_id_match.group(1) if series_id_match else None

        if not series_id:
            return None

        return f'{series_id}_s1_p{episode_num}'

    def fetch_synopsis(self, episode_url: str) -> Optional[str]:
        """あらすじを取得"""
        try:
            content = self.fetch_page(episode_url)
            for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
                json_script = match.group(1)
                if 'description' in json_script:
                    desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', json_script)
                    if desc_match:
                        description = desc_match.group(1)
                        description = description.replace('\\n', '\n')
                        return description.encode('utf-8').decode('unicode_escape') if '\\u' in description else description
        except Exception:
            return None

    def extract_all_metadata(self, url: str, include_synopsis: bool = True) -> SeriesMetadata:
        """全メタ情報を抽出"""
        content = self.fetch_page(url)
        series_title = self.extract_series_title(content)
        episodes = self.extract_episodes(content, url)

        # あらすじを取得（オプション）
        if include_synopsis:
            for episode in episodes:
                if episode.url:
                    episode.synopsis = self.fetch_synopsis(episode.url)

        return SeriesMetadata(
            title=series_title,
            source_url=url,
            extraction_date=datetime.now().strftime('%Y-%m-%d'),
            episodes=episodes
        )