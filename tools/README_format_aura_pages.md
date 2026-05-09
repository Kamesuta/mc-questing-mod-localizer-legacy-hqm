# Lexicon 改行整形ツール

`format_aura_pages.py` は、Minecraft の `.lang` ファイル内にある説明文テキストへ、自動で改行用の区切りを挿入するツールです。

主な用途:

- Aura-Cascade の説明書 (`aura.page.*`)
- Botania の Lexica Botania (`botania.page.*`)

## 背景

一部の Mod の説明書は、日本語のように空白を使わない文章をうまく折り返せません。

このツールは、本文中に区切りを追加して、ゲーム内で自然に折り返されやすくするためのものです。

現在のおすすめ設定は、`<br>` ではなく半角スペースを入れる方法です。

理由:

- `<br>` を使う実装では、Mod 側によっては空行が 1 行余計に入る
- 半角スペースなら空行にならず、折り返し候補として機能する

## 対象ファイル

今回使っている対象ファイルの例:

```text
C:\Users\Kamesuta\AppData\Roaming\PrismLauncher\instances\Simply Magic Pack\minecraft\resources\pack_locale\lang\ja_JP.lang
```

## 基本構文

```powershell
python tools\format_aura_pages.py "<lang file path>" --prefix "<key prefix>" --in-place --normalize-existing-breaks --separator " "
```

## よく使うオプション

- `--prefix`
  - 整形対象のキー接頭辞を指定します
  - 例: `aura.page.` / `botania.page.`
- `--in-place`
  - ファイルを直接上書きします
- `--normalize-existing-breaks`
  - 既存の `<br>` を一度たたんでから再整形します
  - 過去に何度か整形したファイルへ再実行するときに便利です
- `--separator " "`
  - 改行記号の代わりに半角スペースを入れます
  - 現在のおすすめ設定です
- `--width 13`
  - 1 行に収めたい基準幅です
- `--ascii-width 0.6`
  - 英数字を日本語より細く見積もるための係数です

## Aura-Cascade に使う

Aura-Cascade の説明書本文は `aura.page.*` に入っています。

実行例:

```powershell
python tools\format_aura_pages.py "C:\Users\Kamesuta\AppData\Roaming\PrismLauncher\instances\Simply Magic Pack\minecraft\resources\pack_locale\lang\ja_JP.lang" --prefix "aura.page." --in-place --normalize-existing-breaks --separator " "
```

## Botania に使う

Lexica Botania の本文は `botania.page.*` に入っています。

実行例:

```powershell
python tools\format_aura_pages.py "C:\Users\Kamesuta\AppData\Roaming\PrismLauncher\instances\Simply Magic Pack\minecraft\resources\pack_locale\lang\ja_JP.lang" --prefix "botania.page." --in-place --normalize-existing-breaks --separator " "
```

## `<br>` を使いたい場合

もし Mod 側の実装が `<br>` で自然に 1 行改行されるタイプなら、区切りを `<br>` にできます。

```powershell
python tools\format_aura_pages.py "C:\Users\Kamesuta\AppData\Roaming\PrismLauncher\instances\Simply Magic Pack\minecraft\resources\pack_locale\lang\ja_JP.lang" --prefix "aura.page." --in-place --normalize-existing-breaks --separator "<br>"
```

ただし、Aura-Cascade では `<br>` が段落区切り扱いになり、空行が増える挙動を確認しています。

## 再整形の注意

- すでに何度も整形済みの文は、英単語の途中分割などが完全には戻らない場合があります
- いちばん綺麗に仕上げたい場合は、元の未整形 `ja_JP.lang` に戻してから実行してください
- 整形後はゲーム内で辞書を開き、見た目を確認してください

## 補足

このツール名は最初 Aura-Cascade 用として作ったため `format_aura_pages.py` ですが、実際には `--prefix` を変えることで Botania にも使えます。
