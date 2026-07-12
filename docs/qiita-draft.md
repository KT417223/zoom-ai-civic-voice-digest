# 自治体の音声広報を多言語ダイジェスト化する設計をZoom AI Servicesで考えてみた

## はじめに

自治体のWebサイトには、「声の広報」や「市報音声版」として、広報誌の内容を音声で公開しているページがあります。

音声版はアクセシビリティの面でとても重要です。一方で、あとから必要な情報だけを探したり、申込期限や対象者だけを拾ったり、日本語が得意ではない住民向けに多言語で把握したりするには、まだ少し手間があります。

そこで今回は、自治体の音声広報を題材にして、Zoom AI Servicesを使った多言語ダイジェスト化の設計を考えてみます。

最初は、公開されているMP3 URLをそのままZoom AI Servicesに渡して、

```text
音声URL → 文字起こし → 要約 → 翻訳 → 多言語ダイジェスト
```

という流れを作るつもりでした。

ただ、仕様を確認しながら進めると、Zoom側が任意の既存音声ファイルや公開MP3 URLを直接受け取って文字起こしできるとは限らない、という点が見えてきました。

そこで本記事では、入口の音声処理をいったん切り離し、**文字起こし済みテキストを入力として、要約・翻訳・構造化出力を行う設計**に寄せます。

この形にしておくと、既存音声を直接食わせられない場合でも記事と実装が折れません。Zoom会議やZoom録画由来の文字起こしが使える場合にも、同じ後段処理を再利用できます。

## この記事でやること

この記事では、以下を扱います。

- 自治体の音声広報を多言語ダイジェスト化するユースケースを整理する
- 既存音声ファイルを直接扱う前提を避け、文字起こし済みテキスト入力に切り替える
- `--transcript-file` を主軸にしたCLIの設計を作る
- 日本語ダイジェスト、英語ダイジェスト、JSON出力の形を決める
- 実API接続前でも確認できるドライランを用意する

逆に、この記事では以下はやりません。

- 自治体が公開している音声ファイルを再配布する
- 広報本文や全文文字起こしを丸ごと転載する
- Zoom AI Servicesが任意のMP3 URLを直接文字起こしできる、と断定する
- 自治体公式の出力であるかのように見せる

## 題材にする公開音声

調査候補として、以下のような自治体の公開音声ページを見ています。

- 藤沢市「声の広報ふじさわ」
- 小平市「市報音声版『声のたより』」
- 所沢市「広報ところざわ 音声版」
- 立川市「広報たちかわ（PDF版）・声の広報（音声版）」

本記事では、自治体がWeb上で公開している音声版広報を技術検証の題材として参照します。音声ファイル自体の再配布は行わず、元ページへのリンク、処理手順、APIの出力設計を中心に紹介します。各コンテンツの利用条件は、各自治体サイトの利用規約に従ってください。

## 最初に考えた構成

最初に考えた構成は、かなり素直なものでした。

```text
公開MP3 URL
→ Scribeで文字起こし
→ Summarizerで重要なお知らせを抽出
→ Translatorで英語に翻訳
→ Markdown / JSONで出力
```

自治体の音声広報には、住民に必要な情報がたくさん含まれています。

- イベント案内
- 申込期限
- 給付金や制度の案内
- 防災情報
- 子育て、高齢者、福祉関連のお知らせ
- 問い合わせ先

これらを音声のまま聞くのではなく、要点だけ構造化できれば便利です。

ただし、この構成には前提があります。

それは、Zoom AI Servicesが「任意の既存音声ファイル」または「公開MP3 URL」を入力として受け取れることです。

ここが怪しい場合、記事全体が崩れます。

## 設計を変えた理由

Zoomは会議、録画、文字起こし、要約と相性のよいサービスです。一方で、既存のMP3ファイルを汎用の音声認識APIとしてアップロードする使い方ができるかは、実装前に確認が必要です。

そこで、アーキテクチャ上の境界を次のように切り直しました。

```text
音声を文字にする部分
→ 入力アダプタとして分離する

文字起こし済みテキストを要約・翻訳する部分
→ 今回の主役にする
```

つまり、CLIの主入力を `--audio-url` ではなく、`--transcript-file` に寄せます。

```text
文字起こし済みテキスト
→ 重要なお知らせを抽出
→ 英語に翻訳
→ Markdown / JSONで出力
```

こうすると、次のようなメリットがあります。

- 既存音声ファイルをZoomに直接渡せなくても検証できる
- Zoom会議や録画から得た文字起こしにも流用できる
- 要約・翻訳・出力形式を先に固められる
- Qiita記事に載せるサンプルを安全に作れる
- 音声ファイルや全文文字起こしの再配布を避けやすい

これは「逃げ」というより、外部APIの仕様に合わせて責務を分ける設計です。音声入力に依存しすぎない形にしておくと、後からScribe連携を足す場合にも壊れにくくなります。

## 作るCLI

今回のCLIは、以下のような使い方を想定します。

```powershell
civic-voice-digest `
  --transcript-file "transcripts/sample.txt" `
  --source-title "声の広報サンプル" `
  --source-url "https://example.com/source-page" `
  --target-language "en" `
  --dry-run `
  --output-dir "outputs/sample"
```

`--transcript-file` には、文字起こし済みテキストを渡します。

`--dry-run` を付けると、外部APIを呼ばずにサンプルの `digest.json` と `digest.md` を生成します。実API接続前でも、出力形式や記事に載せる見せ方を確認できます。

将来的に既存音声URLを扱えることが確認できた場合は、以下のような入力も残しておきます。

```powershell
civic-voice-digest `
  --audio-url "https://example.com/sample.mp3" `
  --source-title "声の広報サンプル" `
  --source-url "https://example.com/source-page" `
  --target-language "en" `
  --dry-run `
  --output-dir "outputs/sample"
```

ただし、この記事の主軸は `--transcript-file` です。

## データ構造

出力は、以下のような構造を想定します。

```json
{
  "source_title": "声の広報サンプル",
  "source_url": "https://example.com/source-page",
  "audio_url": null,
  "transcript_excerpt": "記事に載せられる短い抜粋または自作サンプル",
  "digest": {
    "language": "ja",
    "summary": "住民向けのお知らせを短く整理したサマリ",
    "notices": [
      {
        "title": "子育て世帯向けのお知らせ",
        "audience": "子育て世帯",
        "deadline": "7月31日",
        "procedure": "オンラインまたは窓口で申請",
        "confidence_notes": "期限と制度名は元ページで確認する"
      }
    ]
  },
  "translation": {
    "language": "en",
    "summary": "English digest for residents",
    "notices": []
  },
  "attribution_note": "音声ファイル自体は再配布せず、元ページへのリンクを示す"
}
```

ポイントは、`confidence_notes` を持たせていることです。

自治体情報では、施設名、制度名、申込期限、対象者を間違えると困ります。AIの出力をそのまま信じるのではなく、人間がどこを確認すべきかを出力に含める設計にしています。

## 実装の骨組み

まず、入力リクエストを表すデータ構造を用意します。

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class DigestRequest:
    audio_url: str | None
    source_title: str
    source_url: str | None = None
    transcript: str | None = None
    target_language: str = "en"
```

`audio_url` は残していますが、必須にはしていません。`transcript` を受け取れるようにすることで、音声入力に依存せず後段の検証を進められます。

次に、ダイジェストの出力構造を定義します。

```python
@dataclass(frozen=True)
class Notice:
    title: str
    audience: str | None
    deadline: str | None
    procedure: str | None
    confidence_notes: str


@dataclass(frozen=True)
class Digest:
    language: str
    summary: str
    notices: list[Notice]


@dataclass(frozen=True)
class DigestResult:
    source_title: str
    source_url: str | None
    audio_url: str | None
    transcript_excerpt: str | None
    digest: Digest
    translation: Digest
    attribution_note: str
```

この形にしておくと、APIのレスポンスが多少変わっても、最終的な出力形式は安定させやすいです。

## ドライラン出力

実API接続前は、ドライランでサンプル出力を生成します。

```powershell
civic-voice-digest `
  --transcript-file "transcripts/sample.txt" `
  --source-title "声の広報サンプル" `
  --target-language "en" `
  --dry-run `
  --output-dir "outputs/sample"
```

生成するファイルは以下です。

```text
outputs/sample/
├── digest.json
└── digest.md
```

Markdown出力は、記事にそのまま貼りやすい形にします。

```md
# 声の広報サンプル

## Source

- Page: https://example.com/source-page
- Audio: -

## Japanese Digest

声の広報サンプルを題材に、住民向けのお知らせを短く整理したサンプルです。

### 子育て世帯向けのお知らせ

- Audience: 子育て世帯
- Deadline: 実音声から抽出予定
- Procedure: 申請方法や必要書類をSummarizer APIで抽出予定
- Notes: これはドライラン用のサンプルです。実記事では実API出力を確認します。
```

ここで大事なのは、ドライラン出力を本物の自治体情報として扱わないことです。記事に載せる場合も、サンプルであることを明記します。

## この設計でZoom AI Servicesをどう使うか

この設計では、Zoom AI Servicesを「任意の音声ファイルを何でも文字起こしする入口」として固定しません。

代わりに、以下のように位置づけます。

```text
Zoom会議・録画・文字起こしなど、Zoom側で得られるテキスト
または
別手段で用意した文字起こしテキスト

→ 要約
→ 翻訳
→ 住民向けダイジェスト化
```

既存音声ファイルを直接処理できることが確認できたら、入力アダプタとして `audio_url` やファイルアップロードを追加すればよいです。

できない場合でも、`transcript-file` 入力を主軸にしておけば、要約・翻訳・構造化出力の検証は続けられます。

## 評価観点

自治体広報を扱う場合、単に「それっぽく要約できた」だけでは不十分です。

以下の観点で確認します。

| 観点 | 見ること |
| --- | --- |
| 固有名詞 | 地名、施設名、制度名を正しく拾えるか |
| 日付・期限 | 申込期限、開催日、配布期間を落とさないか |
| 対象者 | 子育て世帯、高齢者、市内在住者などを抽出できるか |
| 手続き | 申請方法、必要書類、問い合わせ先を整理できるか |
| 翻訳品質 | 自治体情報として自然で誤解の少ない英語になっているか |
| 安全性 | 音声や全文文字起こしを不必要に再配布していないか |
| 再利用性 | 他自治体の広報にも同じ形を使えるか |

特に、期限と対象者は人間が最終確認する前提にします。ここはAI任せにしないほうがよいです。

## 記事としての落としどころ

この記事のポイントは、Zoom AI Servicesに何でもやらせることではありません。

むしろ、外部サービスの仕様に合わせて、入力と後段処理の境界を切ることです。

```text
音声を文字にする部分
→ サービス仕様に合わせて差し替え可能にする

文字起こし済みテキストを住民向けに整える部分
→ 今回のPoCの中心にする
```

この分け方にしておけば、次のような展開ができます。

- Zoom会議や録画由来の文字起こしを使う
- 既存音声の文字起こしだけ別手段で用意する
- Scribeが既存音声に対応していると確認できたら入力アダプタを追加する
- 要約・翻訳・JSON出力の部分はそのまま使い回す

最初に考えた「公開MP3をそのまま食わせる」構成より少し遠回りに見えますが、記事としても実装としてもこちらのほうが折れにくいです。

## 今後やること

次にやることは以下です。

1. Zoom AI Servicesの公式仕様を確認し、任意音声ファイルを扱えるかを確定する
2. `.env.example` に必要な環境変数を具体化する
3. `--transcript-file` 入力で要約・翻訳APIにつなぐ
4. `digest.json` と `digest.md` の実出力を作る
5. 実際の自治体公開ページを参照し、短い出力例だけ記事に載せる
6. 固有名詞、期限、対象者の確認結果を記録する

## まとめ

自治体の音声広報を多言語ダイジェスト化するアイデアは、住民向け情報アクセス、多言語対応、アクセシビリティの観点で実用性があります。

一方で、既存音声ファイルをZoom AI Servicesに直接渡せるかどうかは、実装前に確認が必要です。

そこで今回は、音声入力をいったん切り離し、文字起こし済みテキストを入力として、要約・翻訳・構造化出力を行う設計にしました。

この設計なら、既存MP3を直接処理できなくても、Zoom会議や録画由来の文字起こし、または別手段で用意した文字起こしテキストを使って、多言語ダイジェスト化の検証を進められます。

AIに全部を任せるというより、自治体広報を探しやすく、読みやすく、多言語で届きやすくするための補助線として使う。今回のPoCは、そのための入口として進めていきます。

## 参考リンク

- Zoom Developer Docs: https://developers.zoom.us/docs/
- Zoom API Reference: https://developers.zoom.us/docs/api/rest/reference/zoom-api/methods/
- 藤沢市「声の広報ふじさわ」: https://www.city.fujisawa.kanagawa.jp/kouhou/shise/koho/kohofujisawa/koe/podcast.html
- 小平市「市報音声版『声のたより』」: https://www.city.kodaira.tokyo.jp/shihou-voice/
- 所沢市「広報ところざわ 音声版」: https://www.city.tokorozawa.saitama.jp/tokoronews/koho/onsei/index.html
- 立川市「広報たちかわ（PDF版）・声の広報（音声版）」: https://www.city.tachikawa.lg.jp/shisei/koho/1005488/1005547/index.html
