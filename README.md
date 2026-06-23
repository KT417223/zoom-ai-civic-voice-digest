# Zoom AI Civic Voice Digest

自治体が公開している「声の広報」「市報音声版」を題材に、Zoom AI Services の Scribe / Summarizer / Translator API で多言語ダイジェストを作る検証プロジェクトです。

## コンセプト

自治体広報は生活に必要な情報が多く含まれていますが、音声版の内容をあとから検索したり、重要なお知らせだけ拾ったり、多言語で把握したりするには手間があります。

このプロジェクトでは、公開されている音声版広報を入力として、以下の流れを試します。

1. MP3音声を Scribe API で文字起こしする
2. Summarizer API で重要なお知らせ、対象者、期限、手続きを抽出する
3. Translator API で英語などに翻訳する
4. Markdown / JSON のダイジェストとして出力する

## 参考にする公開音声

検証候補:

- 小平市「市報音声版『声のたより』」
  - https://www.city.kodaira.tokyo.jp/shihou-voice/
- 藤沢市「声の広報ふじさわ」
  - https://www.city.fujisawa.kanagawa.jp/kouhou/shise/koho/kohofujisawa/koe/podcast.html
- 所沢市「広報ところざわ 音声版」
  - https://www.city.tokorozawa.saitama.jp/tokoronews/koho/onsei/index.html
- 立川市「広報たちかわ（PDF版）・声の広報（音声版）」
  - https://www.city.tachikawa.lg.jp/shisei/koho/1005488/1005547/index.html

音声ファイルそのものの再配布は行わず、元ページへのリンク、処理手順、API出力例を中心に紹介します。各コンテンツの利用条件は、各自治体サイトの利用規約に従ってください。

## 記事タイトル案

```text
自治体の「声の広報」をZoom AI Servicesで多言語ダイジェスト化してみた
```

## 評価観点

- 固有名詞: 地名、施設名、制度名を正しく拾えるか
- 日付・期限: 申込期限や開催日を落とさないか
- 対象者: 高齢者、子育て世帯、市内在住者などを抽出できるか
- 要約品質: 長い音声から必要な情報だけ読めるか
- コスト: 1ファイルあたりの処理時間と概算費用
- 再利用性: 他自治体の広報音声にも同じ流れを使えるか

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
Copy-Item .env.example .env
```

`.env` に Zoom AI Services の API キーを設定します。

## 使い方

現時点ではCLIの雛形のみです。実API接続はこれから実装します。

```powershell
civic-voice-digest --audio-url "https://example.com/sample.mp3" --source-title "声の広報サンプル"
```

## Qiita記事向けメモ

- 公開音声を「引用」ではなく「技術検証の題材として参照」と表現する
- 音声・広報本文の丸ごと転載は避ける
- 自治体名、ページ名、URL、確認日を明記する
- 出力例は短い抜粋または自前の要約結果に留める
- APIキー、取得した音声ファイル、全文文字起こしはコミットしない

## Codex向け引き継ぎ

別マシンや別スレッドのCodexで作業するときは、まず以下を読んでください。

- [docs/project-context.md](docs/project-context.md): これまでに決めたこと、方針、次にやること
- [docs/sources.md](docs/sources.md): 参照候補の公開音声ページ
- [docs/article-outline.md](docs/article-outline.md): Qiita記事の構成案
