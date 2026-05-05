# HQM ローカライズ対応 設計方針

対象は Hardcore Questing Mode 1.7.10 の `quests.hqm` です。この文書は、既存の Minecraft Questing Mod Localizer に HQM 対応を追加するための調査結果と実装方針をまとめます。

## 調査対象

- 既存アプリ:
  - `src/converter.py`
  - `src/translator.py`
  - `src/utils.py`
  - `pages/1_ftbq.py`
  - `pages/2_ftbq_new.py`
  - `pages/3_bqm.py`
  - `app.py`
- HQM 実装:
  - `hqm/HQM/src/main/java/hardcorequesting/network/DataReader.java`
  - `hqm/HQM/src/main/java/hardcorequesting/network/DataWriter.java`
  - `hqm/HQM/src/main/java/hardcorequesting/network/DataBitHelper.java`
  - `hqm/HQM/src/main/java/hardcorequesting/FileVersion.java`
  - `hqm/HQM/src/main/java/hardcorequesting/quests/Quest.java`
  - `hqm/HQM/src/main/java/hardcorequesting/quests/QuestTask*.java`
- サンプル:
  - `hqm/sample_hqm/quests.hqm`

## 既存ツールの構造

既存ツールは大きく 2 系統です。

1. クエストファイルを「翻訳キーを埋め込んだファイル」に変換し、言語ファイルを生成する方式
   - FTB Quests 旧形式: `.snbt` + `.json`
   - Better Questing: `DefaultQuests.json` + `.lang`
2. 既に分離済みの言語ファイルだけを翻訳する方式
   - FTB Quests 1.21+: `xx_xx.snbt`
   - Translation Fixer

`BaseQuestConverter` は `read()` でクエストファイルを読み、`_convert()` で文字列を抽出しつつ元ファイルを置換する前提です。FTB/BQM は JSON/SNBT なので値の置換が容易ですが、HQM は bit 単位の独自バイナリなので専用の読み書き層が必要です。

## HQM で既存方式をそのまま使えない理由

HQM には `Translator.translate()` を通る文字列と、通らない文字列が混在しています。

- `Quest.getName()` は raw name を返すだけ。
- `Quest.getDescription()` も raw description を返すだけ。
- `QuestSet.getName()` / `QuestSet.getDescription()` も raw 文字列。
- `QuestTask.getDescription()` / `QuestTask.getLongDescription()` は `Translator.translate()` を通す。
- `Reputation`、バッグ tier/group、Location/Mob 表示名も用途により raw 表示が中心。

そのため、既存のようにクエスト名を `modpack.quest.name` のようなキーへ置換して `.lang` に翻訳を入れても、HQM のクエスト名はキー文字列そのものが表示されます。HQM 対応の第一段階では、キー化ではなく「翻訳済み文字列を `.hqm` に直接書き戻す」方式を採用します。

## サンプル確認結果

`hqm/sample_hqm/quests.hqm` を簡易 bit reader で確認しました。

| 項目 | 結果 |
| --- | ---: |
| ファイルサイズ | 147,050 bytes |
| `FileVersion` | 22 (`CUSTOM_PRECISION_TYPES`) |
| command reward | なし。`COMMAND_REWARDS` は version 23 以降 |
| quest set 数 | 8 |
| quest スロット数 | 418 |
| 実在 quest 数 | 221 |
| reputation 数 | 0 |
| item reward 数 | 303 |
| task 種別 | detect 217、craft 9、kill 9、consume 33、location 4 |

メイン説明、quest set 名/説明、quest 名/説明、task 名/説明は問題なく抽出候補として読めました。サンプルは version 22 なので、実装では version 23 だけでなく version 22 を最初から対応対象にします。

## 対応方針

### 基本方針

HQM は専用バイナリパーサ/ライタを実装し、翻訳済み `quests.hqm` を出力します。

- 入力:
  - `quests.hqm`
  - 任意で既存の抽出 JSON
- 出力:
  - 翻訳済み `quests.hqm`
  - source language JSON
  - target language JSON
- 既存の `TranslationManager` は JSON 辞書の翻訳に流用する。
- `.lang` へのキー化は初期対応では行わない。

### UI 方針

新規ページを追加します。

- `pages/5_hqm.py`
- `app.py` の navigation に `Hardcore Questing Mode` セクションを追加
- アップロード対象は単一の `quests.hqm`
- 既存の 3 タスク構成は少し変更する
  - Convert + Translate: 抽出して翻訳し、翻訳済み `.hqm` を出力
  - Convert only: 抽出 JSON のみ出力し、`.hqm` は原文のまま必要なら再出力
  - Apply existing translation: source/target JSON を使って `.hqm` に適用

FTB/BQM の「言語ファイルがあるか」質問は HQM には合いません。HQM ページでは「既存の抽出/翻訳 JSON を持っているか」に置き換えます。

## 実装モジュール案

### `src/hqm_binary.py`

HQM 専用の低レベル読み書きとモデルを置きます。

主なクラス:

- `HQMBitReader`
  - `read_data(bit_count)`
  - `read_bool()`
  - `read_string(bit_helper)`
  - `read_nbt_bytes()`
  - `read_item_stack(use_size)`
- `HQMBitWriter`
  - `write_data(value, bit_count)`
  - `write_bool(value)`
  - `write_string(value, bit_helper)`
  - `write_nbt_bytes(raw)`
  - `write_item_stack(stack, use_size)`
- `HQMFile`
  - `version`
  - `pass_code`
  - `main_description`
  - `quest_sets`
  - `reputations`
  - `quests`
  - `tiers`
  - `groups`
  - `to_bytes()`
- `HQMTextEntry`
  - `key`
  - `value`
  - `max_bytes`
  - `path`
  - `kind`

日本語コメントは多めに入れます。特に bit 順序、version 分岐、文字列切り詰め、NBT raw byte 保持の箇所はコメント必須です。

### `src/converter.py`

`HQMQuestConverter` を追加します。

役割:

- `quests.hqm` を `HQMFile` に parse
- 翻訳対象文字列を `lang_dict` へ抽出
- 既存の target dict を受け取った場合は `.hqm` に翻訳済み文字列を直接適用
- 変換結果は `BytesIO` または `(quest_name, bytes)` として返す

既存の `BaseQuestConverter` は `quest_data` を JSON/SNBT として扱う前提が強いため、無理に完全継承させず、HQM 専用 manager を作る方が安全です。共通化する場合も、抽出/翻訳の辞書部分だけに留めます。

### `src/utils.py`

既存 `compress_quests()` は `.snbt` 固定です。HQM 用に別関数を追加します。

- `compress_named_files(files, dir, filename)`
  - `(filename, bytes)` の配列を zip 化
- または HQM は単一ファイルなので zip せず `quests.hqm` を直接 download する

初期対応では単一 `quests.hqm` の直接 download で十分です。

## 抽出キー設計

キーは安定性を重視して、配列順ではなく HQM 内 ID を含めます。

例:

```text
{modpack}.hqm.main.description
{modpack}.hqm.sets.{set_id}.name
{modpack}.hqm.sets.{set_id}.desc
{modpack}.hqm.quests.{quest_id}.name
{modpack}.hqm.quests.{quest_id}.desc
{modpack}.hqm.quests.{quest_id}.tasks.{task_id}.name
{modpack}.hqm.quests.{quest_id}.tasks.{task_id}.desc
{modpack}.hqm.quests.{quest_id}.tasks.{task_id}.locations.{location_id}.name
{modpack}.hqm.quests.{quest_id}.tasks.{task_id}.mobs.{mob_id}.name
{modpack}.hqm.tiers.{tier_id}.name
{modpack}.hqm.groups.{group_id}.name
```

`quest_id` は `.hqm` 内のスロット ID を使います。サンプルのように空きスロットがあるため、連番の抽出順をキーにすると再適用時にずれやすくなります。

## 翻訳対象

初期対応で抽出する文字列:

- メイン説明
- Quest set 名
- Quest set 説明
- Quest 名
- Quest 説明
- Task 名
- Task 説明
- Location task の location name
- Kill task の mob 表示名
- Reputation 名、neutral marker 名、marker 名
- Bag tier 名
- Bag group 名

初期対応で翻訳しない文字列:

- Item registry name
- Mob ID
- ItemPrecision ID
- コマンド報酬
- NBT 内部の文字列
- `lock.txt` 由来の pass code

コマンド報酬は `COMMAND_REWARDS` 以降に存在しますが、Minecraft コマンド構文を壊すリスクが高いため翻訳対象外にします。

## 文字列長と文字コード

HQM の string は「byte 長 + raw bytes」です。

- `QUEST_NAME_LENGTH` は 5 bit なので最大 31 bytes。
- `QUEST_DESCRIPTION_LENGTH` は 16 bit なので最大 65,535 bytes。
- `NAME_LENGTH` も 5 bit なので最大 31 bytes。
- Java 実装は `String.getBytes()` / `new String(bytes)` で charset 未指定。

Python 実装では、初期対応として UTF-8 を基本にします。ただし Java 1.7.10 実行環境の default charset と不一致になる可能性があります。

安全策:

- 読み込み時は UTF-8 を試し、失敗したら CP932、最後に ISO-8859-1 で decode。
- 書き込み時は UTF-8 を基本にする。
- byte 上限を超える場合は文字境界を守って切り詰める。
- 切り詰めた entry は UI に警告表示する。

特に quest/task name は 31 bytes 制限が厳しいため、日本語では 10 文字前後で切れる可能性があります。これを避けるため、名前系だけは翻訳しない/短く翻訳するオプションを後で追加できる設計にします。

## Version 対応

初期対応で必須:

- version 22: `CUSTOM_PRECISION_TYPES`
  - サンプルがこの形式。
  - command reward は存在しない。
- version 23: `COMMAND_REWARDS`
  - command reward block を読み飛ばす必要がある。

可能なら読み込みだけ対応:

- version 16 以降: `NO_ITEM_IDS`
  - Item が registry name になるため扱いやすい。

初期非対応:

- version 15 以前
  - 旧 numeric item ID が含まれ、現代環境での意味解決が難しい。
  - ただし raw skip は可能なので、需要があれば後で拡張する。

## バイナリ保存方針

完全な byte-for-byte 維持ではなく、「HQM が読める等価な `quests.hqm` を再シリアライズする」方針にします。

理由:

- string 長が変わると以後の bit offset がすべて変わる。
- 部分置換では後続 byte を単純コピーできない。
- DataWriter と同じ順序で全体を書き直す方が検証しやすい。

ただし、翻訳対象外の複雑な payload は意味を解釈しきらず raw 構造として保持します。

- NBT は圧縮済み byte列をそのまま保持。
- ItemStack は registry name、size、damage、NBT raw を保持。
- FluidStack は NBT raw を保持。
- ReputationBar の `INT` packed data はそのまま保持。
- Command reward は string として読むが、初期設定では変更しない。

## 検証方針

最低限の自動テスト:

1. サンプル `quests.hqm` を parse できる。
2. 何も変更せず serialize した `.hqm` を再 parse できる。
3. 抽出した文字列数が 0 でない。
4. 代表的な文字列を変更して serialize し、再 parse 後に変更後文字列が読める。
5. version 22 の command reward なし分岐で offset がずれない。

可能なら追加:

- serialize 後の主要件数が元ファイルと一致する。
- 31 byte 上限の文字列切り詰めが文字化けしない。
- 翻訳対象外の item registry name / NBT 長が保持される。

## 実装手順

1. `src/hqm_binary.py` に bit reader/writer と `DataBitHelper` 相当を実装する。
2. version 22/23 の `quests.hqm` parse/serialize を実装する。
3. `HQMFile.extract_text_entries()` と `HQMFile.apply_translations()` を実装する。
4. サンプルで round-trip テストを追加する。
5. `HQMQuestConverter` または専用 manager を追加する。
6. `pages/5_hqm.py` を追加する。
7. `app.py` navigation と `lang/en-US.json` / `lang/ko-KR.json` に文言を追加する。
8. 実ファイルをアップロードして、source JSON、target JSON、翻訳済み `quests.hqm` を出力できることを確認する。

## リスク

- HQM は文字列長制限が厳しく、日本語訳が欠けやすい。
- Java 側の default charset と Python 側の UTF-8 が一致しない環境では文字化けの可能性がある。
- version 21 以前の旧形式ファイルは分岐が増える。
- HQM 本体の一部表示は `Translator.translate()` を通るため、原文が偶然 lang key と一致する場合の挙動が変わる可能性がある。
- 再シリアライズ方式は元ファイルと完全同一 byte にはならない可能性がある。ただし HQM の reader が読める構造を維持することを優先する。

## 結論

HQM 対応は、既存 FTB/BQM の「クエストをキー化して外部 lang に逃がす」方式ではなく、`.hqm` 内の文字列を直接翻訳済みに差し替える専用フローとして実装します。既存の翻訳 API 呼び出し、言語選択、JSON 辞書管理は流用できますが、クエストファイルの読み書きは HQM 専用の bit-level parser/writer が必要です。
