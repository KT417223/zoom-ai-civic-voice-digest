# Implementation Plan

Qiita投稿に向けた実装の分解です。

## 方針

最初から全APIを完全実装するより、以下の順で小さく進めます。

1. APIなしで、入力と出力形式を固める
2. 既存文字起こしテキストを入力して、要約・翻訳の出力形を確認する
3. Zoom AI Services の公式仕様を確認し、環境変数とAPIクライアントを具体化する
4. ドライランでMarkdown / JSON の成果物を生成する
5. Summarizer / Translator をつなぐ
6. 音声入力アダプタが必要か判断する

重要: Scribe が任意の既存音声ファイルや公開MP3 URLを受け取れるとは限らない。公式仕様を確認するまでは、`--audio-url` は「将来の入力候補」、`--transcript-file` は「確実に検証を進めるための入力」として扱う。

## CLIの完成イメージ

```powershell
civic-voice-digest `
  --transcript-file "transcripts/sample.txt" `
  --source-title "声の広報サンプル" `
  --source-url "https://example.com/source-page" `
  --target-language "en" `
  --dry-run `
  --output-dir "outputs/sample"
```

将来、既存音声URLを扱えることが確認できた場合:

```powershell
civic-voice-digest `
  --audio-url "https://example.com/sample.mp3" `
  --source-title "声の広報サンプル" `
  --source-url "https://example.com/source-page" `
  --target-language "en" `
  --dry-run `
  --output-dir "outputs/sample"
```

## 予定するモジュール

- `config.py`: 環境変数と設定値
- `models.py`: 入出力データ構造
- `zoom_client.py`: Zoom AI Services APIクライアント
- `pipeline.py`: 処理フロー
- `renderers.py`: Markdown / JSON 出力
- `cli.py`: コマンドライン引数

## 出力ファイル

```text
outputs/<run-id>/
├── digest.json
├── digest.md
├── transcript_excerpt.md
└── run-metadata.json
```

実データはGit管理しない方針です。記事に載せる短い例だけ、必要に応じて `docs/experiment-log.md` に転記します。

## セキュリティと権利まわり

- `.env` はコミットしない
- 音声ファイルはコミットしない
- 全文文字起こしはコミットしない
- 記事では元ページへのリンクを明記する
- 出力例は短い抜粋または自前の要約結果に留める
- 自治体公式の見解に見える表現を避ける

## 次の実装タスク

1. Zoom AI Services のAPI仕様を確認する
2. `.env.example` を公式仕様に合わせて更新する
3. `models.py` を追加して出力JSONの型を固める
4. `renderers.py` を追加してMarkdown出力を作る
5. Summarizer / Translator API連携を追加する
6. 実出力を `docs/experiment-log.md` に記録する
