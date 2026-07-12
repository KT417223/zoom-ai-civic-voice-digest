# 自治体の音声広報を多言語ダイジェスト化する設計をZoom AI Servicesで考えてみた

## はじめに

自治体のサイトを見ていると、「声の広報」や「市報音声版」として、広報誌の内容を音声で公開しているページがあります。

これ、アクセシビリティの取り組みとしてかなり大事だと思っています。広報誌の内容を読むのが難しい人にも情報が届くし、耳で聞ける形になっているのはありがたいです。

一方で、開発者目線で見ると、もう少し扱いやすくできそうな余地もあります。

たとえば、

- 申込期限だけ知りたい
- 自分が対象者かだけ確認したい
- 長い音声から重要なお知らせだけ拾いたい
- 日本語が得意ではない住民向けに英語で概要を出したい

こういうニーズはありそうです。

そこで最初は、自治体が公開している音声広報のMP3をZoom AI Servicesに渡して、

```text
公開MP3
→ 文字起こし
→ 要約
→ 翻訳
→ 多言語ダイジェスト
```

という流れを作れないか考えていました。

ただ、調べながら進めるうちに、少し前提が怪しくなってきました。

Zoom AI Servicesが、任意の既存MP3ファイルや公開音声URLをそのまま受け取って文字起こしできるとは限らないんですよね。Zoomは会議や録画、そこで生成される文字起こし・要約とは相性が良さそうですが、「汎用の音声ファイル文字起こしAPI」として使えるかは別問題です。

なので今回は、いったん音声入力の部分を切り離して、**文字起こし済みテキストを入力にして多言語ダイジェストを作る設計**に寄せることにしました。

## 今回の落としどころ

当初の理想はこうでした。

```text
公開音声URL
→ Zoom AI Servicesで文字起こし
→ 要約
→ 翻訳
→ Markdown / JSONで出力
```

でも、この構成は「Zoom側が任意の公開MP3を直接扱える」ことが前提になります。

ここが崩れると、記事も実装も丸ごと崩れます。よくあるやつです。気持ちよく作り始めたあとに、入口のAPI仕様で急ブレーキがかかるパターン。

そこで、今回のPoCでは境界をこう切りました。

```text
文字起こし済みテキスト
→ 重要なお知らせを抽出
→ 英語に翻訳
→ Markdown / JSONで出力
```

音声を文字にする部分は、あとから差し替えられる入力アダプタとして扱います。

この形なら、次のどれでも後段の処理を使い回せます。

- Zoom会議やZoom録画から得られた文字起こし
- 別手段で作成した文字起こし
- 将来、Zoom側で既存音声ファイルを扱えると確認できた場合の音声入力

つまり、今回の主役は「音声ファイルをどう食わせるか」ではなく、**文字起こし済みの広報情報を、住民向けに読みやすく整える部分**です。

## 題材にする公開音声

候補として、以下のような自治体の公開音声ページを見ています。

- 藤沢市「声の広報ふじさわ」
- 小平市「市報音声版『声のたより』」
- 所沢市「広報ところざわ 音声版」
- 立川市「広報たちかわ（PDF版）・声の広報（音声版）」

ただし、この記事では音声ファイルそのものは再配布しません。広報本文や全文文字起こしも丸ごと載せません。

扱いとしては、あくまで「公開されている音声版広報を技術検証の題材として参照する」です。記事に載せる場合も、元ページへのリンク、処理の考え方、短い出力例に留めます。

このあたりは地味ですが、自治体情報を扱うならかなり大事なところだと思っています。

## 作るもの

今回作るCLIのイメージはこんな感じです。

```powershell
civic-voice-digest `
  --transcript-file "transcripts/sample.txt" `
  --source-title "声の広報サンプル" `
  --source-url "https://example.com/source-page" `
  --target-language "en" `
  --dry-run `
  --output-dir "outputs/sample"
```

`--transcript-file` に文字起こし済みテキストを渡します。

`--dry-run` を付けると、外部APIを呼ばずにサンプルの `digest.json` と `digest.md` を生成します。実API接続前でも、出力形式や記事での見せ方を確認できるようにしておきます。

将来、既存音声URLを扱えることが確認できたら、以下のような入力も追加できます。

```powershell
civic-voice-digest `
  --audio-url "https://example.com/sample.mp3" `
  --source-title "声の広報サンプル" `
  --source-url "https://example.com/source-page" `
  --target-language "en" `
  --output-dir "outputs/sample"
```

ただし、今の主軸は `--transcript-file` です。

## 出力イメージ

出力は、最終的に以下の2形式にします。

```text
outputs/sample/
├── digest.json
└── digest.md
```

JSONは、あとから別システムで扱いやすいように構造化します。

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

ポイントは `confidence_notes` を持たせていることです。

自治体情報は、ふわっと要約できればOKというものではありません。施設名、制度名、申込期限、対象者を間違えると普通に困ります。

なので、「AIが出したから完成」ではなく、人間が確認すべき箇所を明示できる形にしています。

## 実装メモ

まず、入力を表すデータ構造を用意します。

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

`audio_url` は残していますが、必須にはしていません。

`transcript` を受け取れるようにしておけば、音声入力に依存せず、要約・翻訳・出力形式の検証を先に進められます。

次に、出力側です。

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

この形にしておくと、あとからAPIレスポンスの形が変わっても、最終的なJSON/Markdownの形は安定させやすいです。

## ドライランしてみる

実API接続前に、まずドライランで出力を確認します。

```powershell
civic-voice-digest `
  --transcript-file "transcripts/sample.txt" `
  --source-title "声の広報サンプル" `
  --target-language "en" `
  --dry-run `
  --output-dir "outputs/sample"
```

Markdown出力は、記事に貼りやすい形にします。

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

ここでは本物の自治体情報っぽく見せすぎないようにしています。ドライランはドライランです。

## Zoom AI Servicesをどこで使う想定か

今回の設計では、Zoom AI Servicesを「任意の音声ファイルを何でも文字起こしする入口」として固定しません。

むしろ、以下のように考えています。

```text
Zoom会議・録画・文字起こしなど、Zoom側で得られるテキスト
または
別手段で用意した文字起こしテキスト

→ 要約
→ 翻訳
→ 住民向けダイジェスト化
```

既存音声ファイルを直接処理できることが確認できたら、入力アダプタとして `audio_url` やファイルアップロードを追加します。

できない場合でも、`--transcript-file` を主軸にしておけば、要約・翻訳・構造化出力の検証は続けられます。

この分け方にしておくと、Zoom会議や録画由来の文字起こしにも、自治体が公開している音声広報の文字起こしにも、同じ後段処理を使えます。

## 評価するときに見るところ

自治体広報を扱うなら、単に「それっぽくまとまった」だけでは足りません。

見るべきところはこのあたりです。

| 観点 | 見ること |
| --- | --- |
| 固有名詞 | 地名、施設名、制度名を正しく拾えるか |
| 日付・期限 | 申込期限、開催日、配布期間を落とさないか |
| 対象者 | 子育て世帯、高齢者、市内在住者などを抽出できるか |
| 手続き | 申請方法、必要書類、問い合わせ先を整理できるか |
| 翻訳品質 | 自治体情報として自然で誤解の少ない英語になっているか |
| 安全性 | 音声や全文文字起こしを不必要に再配布していないか |
| 再利用性 | 他自治体の広報にも同じ形を使えるか |

特に、期限と対象者は人間が最後に確認する前提にしたほうがよさそうです。

自治体のお知らせで「対象者が違いました」「期限が違いました」は洒落にならないので、ここはAI任せにしない設計にします。

## やってみて思ったこと

最初はもっと単純に、「公開MP3を渡して、文字起こしして、要約して、翻訳して終わり」と考えていました。

でも実際に仕様を見ながら考えると、入口の前提を固めないまま進めるのは危ないです。

そこで、音声入力と後段処理を分けました。

```text
音声を文字にする部分
→ サービス仕様に合わせて差し替え可能にする

文字起こし済みテキストを住民向けに整える部分
→ 今回のPoCの中心にする
```

少し遠回りに見えますが、実装としてはこちらのほうが折れにくいです。

外部APIを使うときは、やりたいことをそのまま一枚岩で作るより、怪しい前提を早めに分離しておくほうが後で助かります。今回もまさにそれでした。

## 今後やること

次はこのあたりを進めます。

1. Zoom AI Servicesの公式仕様を確認し、任意音声ファイルを扱えるかを確定する
2. `.env.example` に必要な環境変数を具体化する
3. `--transcript-file` 入力で要約・翻訳APIにつなぐ
4. `digest.json` と `digest.md` の実出力を作る
5. 実際の自治体公開ページを参照し、短い出力例だけ記事に載せる
6. 固有名詞、期限、対象者の確認結果を記録する

## まとめ

自治体の音声広報を多言語ダイジェスト化するアイデアは、住民向け情報アクセス、多言語対応、アクセシビリティの面でけっこう実用性がありそうです。

ただし、既存音声ファイルをZoom AI Servicesに直接渡せるかどうかは、実装前に確認が必要です。

今回はその前提に依存しすぎないように、音声入力をいったん切り離し、文字起こし済みテキストを入力として、要約・翻訳・構造化出力を行う設計にしました。

この形なら、既存MP3を直接処理できなくても、Zoom会議や録画由来の文字起こし、または別手段で用意した文字起こしテキストを使って、多言語ダイジェスト化の検証を進められます。

AIに全部を任せるというより、自治体広報を探しやすく、読みやすく、多言語で届きやすくするための補助線として使う。今回のPoCは、その入口として進めています。

## 参考リンク

- Zoom Developer Docs: https://developers.zoom.us/docs/
- Zoom API Reference: https://developers.zoom.us/docs/api/rest/reference/zoom-api/methods/
- 藤沢市「声の広報ふじさわ」: https://www.city.fujisawa.kanagawa.jp/kouhou/shise/koho/kohofujisawa/koe/podcast.html
- 小平市「市報音声版『声のたより』」: https://www.city.kodaira.tokyo.jp/shihou-voice/
- 所沢市「広報ところざわ 音声版」: https://www.city.tokorozawa.saitama.jp/tokoronews/koho/onsei/index.html
- 立川市「広報たちかわ（PDF版）・声の広報（音声版）」: https://www.city.tachikawa.lg.jp/shisei/koho/1005488/1005547/index.html
