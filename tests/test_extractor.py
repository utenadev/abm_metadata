# -*- coding: utf-8 -*-
"""
メタデータ抽出機能の基本テスト
"""

import pytest
from abema_metadata.extractor import AbemaMetadataExtractor, InvalidURLError
from abema_metadata.models import SeriesMetadata, EpisodeMetadata


def test_extractor_initialization():
    """エクストラクターの初期化テスト"""
    extractor = AbemaMetadataExtractor()
    assert extractor.user_agent is not None
    assert isinstance(extractor.user_agent, str)


def test_extractor_with_custom_user_agent():
    """カスタムユーザーエージェントを使用した初期化テスト"""
    custom_ua = "CustomUserAgent/1.0"
    extractor = AbemaMetadataExtractor(user_agent=custom_ua)
    assert extractor.user_agent == custom_ua


def test_data_models():
    """データモデルの動作テスト"""
    # EpisodeMetadata のテスト
    episode = EpisodeMetadata(
        number=1,
        title="テストエピソード",
        synopsis="これはテストです",
        url="https://example.com/episode/1"
    )
    assert episode.number == 1
    assert episode.title == "テストエピソード"
    assert episode.synopsis == "これはテストです"
    assert episode.url == "https://example.com/episode/1"

    # SeriesMetadata のテスト
    series = SeriesMetadata(
        title="テストシリーズ",
        source_url="https://example.com/series",
        extraction_date="2024-02-20",
        episodes=[episode]
    )
    assert series.title == "テストシリーズ"
    assert series.source_url == "https://example.com/series"
    assert series.extraction_date == "2024-02-20"
    assert len(series.episodes) == 1
    assert series.episodes[0] == episode


def test_invalid_url():
    """無効なURL形式のテスト"""
    extractor = AbemaMetadataExtractor()
    
    # abema.tv 以外のURL
    with pytest.raises(InvalidURLError) as excinfo:
        extractor.fetch_page("https://google.com")
    assert "無効なURL形式" in str(excinfo.value)

    # 不正なスキーム
    with pytest.raises(InvalidURLError):
        extractor.fetch_page("ftp://abema.tv/video/title/123")


def test_fetch_page_basic():
    """基本的なページ取得機能のテスト（ネットワーク環境に依存）"""
    extractor = AbemaMetadataExtractor()
    
    # 実際のURLでテスト（CI環境等で失敗する可能性があるためスキップ可能に）
    try:
        content = extractor.fetch_page("https://abema.tv/video/title/26-249")
        assert content is not None
        assert isinstance(content, str)
        assert len(content) > 0
    except Exception as e:
        pytest.skip(f"ネットワーク未接続またはアクセス不可: {e}")


def test_extract_series_title_with_mock():
    """モックデータを使用したシリーズタイトル抽出テスト"""
    extractor = AbemaMetadataExtractor()
    
    # シリーズタイトルを含むモックHTML（BreadcrumbList 構造）
    mock_content = '''
<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
        {
            "@type": "ListItem",
            "position": 1,
            "name": "ホーム",
            "item": "https://abema.tv/"
        },
        {
            "@type": "ListItem",
            "position": 2,
            "name": "アニメ",
            "item": "https://abema.tv/video/genre/anime"
        },
        {
            "@type": "ListItem",
            "position": 3,
            "name": "テストシリーズ",
            "item": "https://abema.tv/video/title/test-series"
        }
    ]
}
</script>
    '''
    
    title = extractor.extract_series_title(mock_content)
    assert title == "テストシリーズ"


def test_extract_episodes_with_mock():
    """モックデータを使用したエピソード抽出テスト"""
    extractor = AbemaMetadataExtractor()
    
    # エピソードデータを含むモックHTML
    mock_content = '''
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "ImageObject",
        "caption": "テストシリーズ 第1話 はじめての冒険のサムネイル",
        "url": "https://abema.tv/video/programs/test-1"
    }
    </script>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "ImageObject",
        "caption": "テストシリーズ 第2話 新しい出会い",
        "url": "https://abema.tv/video/programs/test-2"
    }
    </script>
    '''
    
    episodes = extractor.extract_episodes(mock_content, "https://abema.tv/video/title/test-series")
    assert len(episodes) == 2
    assert episodes[0].number == 1
    assert episodes[0].title == "はじめての冒険"
    assert episodes[1].number == 2
    assert episodes[1].title == "新しい出会い"


def test_generate_episode_id():
    """エピソードID生成のテスト"""
    extractor = AbemaMetadataExtractor()
    
    # 正当なシリーズURLの場合
    episode_id = extractor._generate_episode_id(
        "https://abema.tv/video/programs/test-1",
        "https://abema.tv/video/title/test-series",
        1
    )
    assert episode_id == "test-series_s1_p1"
    
    # 不正なシリーズURLの場合
    episode_id = extractor._generate_episode_id(
        "https://abema.tv/video/programs/test-1",
        "https://invalid.url",
        1
    )
    assert episode_id is None