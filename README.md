# AbemaTV メタ情報抽出ツール (AbemaTV Metadata Extractor)

AbemaTVのアニメ・ドラマページから動画ファイル用のメタ情報（シリーズタイトル、話数、サブタイトル、あらすじ）を抽出し、構造化されたYAML形式で保存するPythonツールです。

## 特徴

- **自動抽出**: ページ内のJSON-LDデータを解析し、正確なエピソード情報を取得します。
- **正規表現ベース**: 重いブラウザ自動化ライブラリ（Selenium等）を必要とせず、軽量・高速に動作します。
- **YAML出力**: 動画管理ソフトやスクリプトで利用しやすいYAML形式でデータを出力します。
- **堅牢な設計**: クリーンなモジュール構造（`abema_metadata` パッケージ）とテストスイートを備えています。
- **エラーハンドリング**: ネットワークエラー時の自動リトライ機能や、分かりやすいエラーメッセージ表示機能を搭載しています。

## セットアップ

### 前提条件

- Python 3.7 以上
- `pip`（Pythonパッケージマネージャー）

### インストール

1. リポジトリをクローンまたはダウンロードします。
2. 必要な依存パッケージをインストールします：

```bash
pip install -r requirements.txt
```

**主な依存パッケージ:**
- `PyYAML`: YAMLファイルの出力に使用
- `pytest`: テスト実行に使用（開発時）

## 使用方法

メインのエントリーポイントは `abema_extractor.py` です。

### 基本的な実行

対象のAbemaTVシリーズURLを指定して実行します。

```bash
python3 abema_extractor.py https://abema.tv/video/title/189-85
```

### オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|-------|------|-----------|
| `url` | (なし) | 対象のAbemaTVシリーズURL | (必須) |
| `--output` | `-o` | 出力するYAMLファイル名 | `episodes_output.yaml` |
| `--no-synopsis` | (なし) | あらすじの取得をスキップ（高速モード） | `False` |
| `--help` | `-h` | ヘルプメッセージを表示 | - |

### 実行例

```bash
# 特定のファイル名で出力
python3 abema_extractor.py https://abema.tv/video/title/189-85 -o my_anime.yaml

# あらすじをスキップして高速にタイトルのみ取得
python3 abema_extractor.py https://abema.tv/video/title/189-85 --no-synopsis
```

## 出力データ形式 (YAML)

抽出されたデータは以下のような形式で保存されます：

```yaml
series_title: 機械じかけのマリー
source_url: https://abema.tv/video/title/189-85
extraction_date: '2025-12-25'
total_episodes: 11
episodes:
- episode_number: 1
  title: 完璧なメイドロボ？
  synopsis: あらすじの内容がここに入ります...
  url: https://abema.tv/video/episode/189-85_s1_p1
- episode_number: 2
  title: 偽りの心
  synopsis: ...
  url: https://abema.tv/video/episode/189-85_s1_p2
```

## プロジェクト構造

```
.
├── abema_extractor.py    # メインのエントリーポイント
├── abema_metadata/       # コアモジュールパッケージ
│   ├── __init__.py
│   ├── cli.py            # CLIインターフェース
│   ├── extractor.py      # 抽出ロジック（正規表現解析）
│   └── models.py         # データモデル定義
├── tests/                # テストスイート
│   └── test_extractor.py
└── requirements.txt      # 依存パッケージリスト
```

## 開発とテスト

### テストの実行

```bash
pytest tests/test_extractor.py
```

## ライセンス

MIT License

## 免責事項

このツールは個人利用および研究目的を想定しています。AbemaTVの利用規約に従って使用してください。サイト構造の変更により、抽出が正しく行えなくなる可能性があります。