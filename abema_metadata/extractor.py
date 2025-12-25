# -*- coding: utf-8 -*-
"""
Core extraction functionality for AbemaTV metadata
"""

import urllib.request
import urllib.error
import re
import time
from typing import Optional, List
from datetime import datetime
from .models import SeriesMetadata, EpisodeMetadata


class AbemaExtractorError(Exception):
    """Abema抽出処理に関連するベース例外クラス"""
    pass


class NetworkError(AbemaExtractorError):
    """ネットワーク通信に関連するエラー"""
    pass


class InvalidURLError(AbemaExtractorError):
    """無効なURLまたは見つからないページのエラー"""
    pass


class AbemaMetadataExtractor:
    """AbemaTVからメタ情報を抽出するコアクラス"""

    def __init__(self, user_agent: Optional[str] = None):
        """初期化

        Args:
            user_agent: 使用するユーザーエージェント文字列。省略時はデフォルトを使用。
        """
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    def fetch_page(self, url: str, retries: int = 3) -> str:
        """指定されたURLのウェブページを取得します（リトライ機能付き）。

        Args:
            url: 取得対象のURL
            retries: 通信失敗時の最大リトライ回数

        Returns:
            HTMLコンテンツ文字列

        Raises:
            InvalidURLError: URLが無効、またはページが存在しない(404)場合
            NetworkError: 通信エラーが解決しない場合
        """
        if not url.startswith('https://abema.tv/'):
            raise InvalidURLError(f"無効なURL形式です。'https://abema.tv/' で始まるURLを指定してください: {url}")

        last_exception = None

        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
                with urllib.request.urlopen(req) as response:
                    return response.read().decode('utf-8')

            except urllib.error.HTTPError as e:
                if e.code == 404:
                    raise InvalidURLError(f"指定されたページが見つかりません (404 Not Found): {url}")
                # 404以外はサーバーエラー等の可能性があるためリトライ対象
                last_exception = e
                if attempt < retries - 1:
                    print(f"サーバーエラー (HTTP {e.code})。2秒後にリトライします ({attempt + 1}/{retries})...")
                    time.sleep(2)

            except urllib.error.URLError as e:
                last_exception = e
                if attempt < retries - 1:
                    print(f"通信エラー。2秒後にリトライします ({attempt + 1}/{retries})...")
                    time.sleep(2)
            except Exception as e:
                # その他の予期せぬエラー
                last_exception = e
                break

        raise NetworkError(f"ページの取得に失敗しました。ネットワーク接続を確認してください: {last_exception}")

    def extract_series_title(self, content: str) -> str:
        """HTMLコンテンツからシリーズタイトルを抽出します。

        Args:
            content: ページのHTMLソースコード

        Returns:
            抽出されたシリーズタイトル。見つからない場合は「不明なシリーズ」。
        """
        # application/ld+json スクリプトタグをすべて検索
        for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
            json_script = match.group(1)
            
            # BreadcrumbList タイプが含まれているか確認（スペースを許容する正規表現を使用）
            if re.search(r'"@type"\s*:\s*"BreadcrumbList"', json_script):
                # 日本語を含む名前を抽出
                name_matches = re.findall(r'"name"\s*:\s*"([^"]+)"', json_script)
                for name in name_matches:
                    # 一般的なナビゲーション項目を除外し、ある程度の長さがあるものをタイトルとみなす
                    if name not in ['ホーム', 'アニメ', 'ドラマ', '詳細'] and len(name) > 2:
                        return name
        return "不明なシリーズ"

    def extract_episodes(self, content: str, series_url: str) -> List[EpisodeMetadata]:
        """HTMLコンテンツから各エピソードの情報を抽出します。

        Args:
            content: ページのHTMLソースコード
            series_url: シリーズのベースURL（ID抽出用）

        Returns:
            EpisodeMetadataのリスト（話数順にソート済み）
        """
        episodes = []

        # application/ld+json スクリプトタグをすべて検索
        for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
            json_script = match.group(1)

            # キャプション情報が含まれているか確認
            if '"caption"' in json_script:
                caption_match = re.search(r'"caption"\s*:\s*"([^"]+)"', json_script)
                if caption_match:
                    caption = caption_match.group(1)

                    # 話数とタイトルを抽出（例: "第1話 タイトル" または "第1話 タイトルのサムネイル"）
                    if '第' in caption and '話' in caption:
                        # 非欲張りマッチングを使用して、サムネイルなどの余計な文言を除去
                        title_match = re.search(r'(?:.*?)第(\d+)話\s*(.+?)(?:\s*のサムネイル)?$', caption)
                        if title_match:
                            episode_num = int(title_match.group(1))
                            title = title_match.group(2).strip()

                            # URL（サムネイルURL）を抽出
                            url_match = re.search(r'"url"\s*:\s*"([^"]+)"', json_script)
                            thumbnail_url = url_match.group(1) if url_match else ''

                            # エピソードIDと個別ページのURLを生成
                            episode_id = self._generate_episode_id(thumbnail_url, series_url, episode_num)

                            episodes.append(EpisodeMetadata(
                                number=episode_num,
                                title=title,
                                url=f'https://abema.tv/video/episode/{episode_id}' if episode_id else None
                            ))

        return sorted(episodes, key=lambda x: x.number)

    def _generate_episode_id(self, thumbnail_url: str, series_url: str, episode_num: int) -> Optional[str]:
        """シリーズURLと話数からエピソードIDを推測生成します。

        Args:
            thumbnail_url: サムネイル画像のURL
            series_url: シリーズのURL
            episode_num: 話数

        Returns:
            生成されたエピソードID（例: 189-85_s1_p1）。生成できない場合は None。
        """
        # URLからシリーズID（例: 189-85）を抽出
        series_id_match = re.search(r'/title/([^/?#]+)', series_url)
        series_id = series_id_match.group(1) if series_id_match else None

        if not series_id:
            return None

        # 標準的なパターン（シリーズID + _s1_p + 話数）で生成
        return f'{series_id}_s1_p{episode_num}'

    def fetch_synopsis(self, episode_url: str) -> Optional[str]:
        """個別エピソードページからあらすじを取得します。

        Args:
            episode_url: エピソードのURL

        Returns:
            あらすじ文字列。取得失敗時は None。
        """
        try:
            content = self.fetch_page(episode_url, retries=1) # あらすじ取得失敗は致命的ではないのでリトライ少なめ
            for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL):
                json_script = match.group(1)
                
                # description フィールドを探す
                if '"description"' in json_script:
                    desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', json_script)
                    if desc_match:
                        description = desc_match.group(1)
                        # エスケープされた文字を処理
                        description = description.replace('\\n', '\n')
                        if '\\u' in description:
                            try:
                                return description.encode('utf-8').decode('unicode_escape')
                            except Exception:
                                pass
                        return description
        except Exception:
            return None
        return None

    def extract_all_metadata(self, url: str, include_synopsis: bool = True) -> SeriesMetadata:
        """シリーズURLからすべてのメタデータを抽出します。

        Args:
            url: シリーズのURL
            include_synopsis: 各話のあらすじを取得するかどうか

        Returns:
            抽出された全データを含む SeriesMetadata オブジェクト
            
        Raises:
            InvalidURLError: URLが無効な場合
            NetworkError: 通信エラーの場合
        """
        content = self.fetch_page(url)
        series_title = self.extract_series_title(content)
        episodes = self.extract_episodes(content, url)

        # 必要に応じて各話のあらすじを取得
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
