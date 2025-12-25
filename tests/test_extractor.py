# -*- coding: utf-8 -*-
"""
Basic tests for the metadata extractor
"""

import pytest
from abema_metadata.extractor import AbemaMetadataExtractor
from abema_metadata.models import SeriesMetadata, EpisodeMetadata


def test_extractor_initialization():
    """Test that extractor initializes correctly"""
    extractor = AbemaMetadataExtractor()
    assert extractor.user_agent is not None
    assert isinstance(extractor.user_agent, str)


def test_extractor_with_custom_user_agent():
    """Test extractor with custom user agent"""
    custom_ua = "CustomUserAgent/1.0"
    extractor = AbemaMetadataExtractor(user_agent=custom_ua)
    assert extractor.user_agent == custom_ua


def test_data_models():
    """Test that data models work correctly"""
    # Test EpisodeMetadata
    episode = EpisodeMetadata(
        number=1,
        title="Test Episode",
        synopsis="This is a test",
        url="https://example.com/episode/1"
    )
    assert episode.number == 1
    assert episode.title == "Test Episode"
    assert episode.synopsis == "This is a test"
    assert episode.url == "https://example.com/episode/1"

    # Test SeriesMetadata
    series = SeriesMetadata(
        title="Test Series",
        source_url="https://example.com/series",
        extraction_date="2024-02-20",
        episodes=[episode]
    )
    assert series.title == "Test Series"
    assert series.source_url == "https://example.com/series"
    assert series.extraction_date == "2024-02-20"
    assert len(series.episodes) == 1
    assert series.episodes[0] == episode


def test_fetch_page_basic():
    """Test basic page fetching functionality"""
    extractor = AbemaMetadataExtractor()
    
    # Test with a known URL (this might fail in CI, but should work locally)
    try:
        content = extractor.fetch_page("https://abema.tv/video/title/26-249")
        assert content is not None
        assert isinstance(content, str)
        assert len(content) > 0
    except Exception as e:
        # If network is unavailable, we can't test this
        pytest.skip(f"Network unavailable: {e}")


def test_extract_series_title_with_mock():
    """Test series title extraction with mock data"""
    extractor = AbemaMetadataExtractor()
    
    # Mock HTML content with series title
    mock_content = '''
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "ホーム"
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "アニメ"
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": "テストシリーズ"
            }
        ]
    }
    </script>
    '''
    
    title = extractor.extract_series_title(mock_content)
    assert title == "テストシリーズ"


def test_extract_episodes_with_mock():
    """Test episode extraction with mock data"""
    extractor = AbemaMetadataExtractor()
    
    # Mock HTML content with episode data
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
    """Test episode ID generation"""
    extractor = AbemaMetadataExtractor()
    
    # Test with valid series URL
    episode_id = extractor._generate_episode_id(
        "https://abema.tv/video/programs/test-1",
        "https://abema.tv/video/title/test-series",
        1
    )
    assert episode_id == "test-series_s1_p1"
    
    # Test with invalid series URL
    episode_id = extractor._generate_episode_id(
        "https://abema.tv/video/programs/test-1",
        "https://invalid.url",
        1
    )
    assert episode_id is None