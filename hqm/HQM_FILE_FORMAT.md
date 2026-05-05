# HQM `.hqm` ファイル仕様メモ

このメモは `HQM/src/main/java/hardcorequesting` 配下の実装から読み取った、Hardcore Questing Mode の `quests.hqm` バイナリ形式の概要です。主な根拠は `network/FileHelper.java`、`network/DataReader.java`、`network/DataWriter.java`、`network/DataBitHelper.java`、`quests/Quest.java` です。

## 前提

- 標準ファイル名は `quests.hqm`。
- `Quest.init(path)` では `path + "quests.hqm"` を読み書きする。
- ファイル先頭にマジック文字列はない。
- 先頭 1 byte は `FileVersion` の enum ordinal。
- 現行実装の最新バージョンは `COMMAND_REWARDS`。ordinal は `23`。
- 保存時は既存ファイルを `quests.hqm-backup` にコピーしてから書き込む。

## ビットストリーム

`.hqm` は byte 境界の固定構造ではなく、`DataWriter.writeData(data, bitCount)` で詰め込まれるビットストリームです。

- 数値は指定ビット幅の下位ビットだけが保存される。
- ビットは LSB first で書かれる。つまり、値の下位ビットから現在 byte の空き位置へ詰める。
- 読み込みも同じ順序で `DataReader.readData(bitCount)` が復元する。
- 最後に余った bit は `writeFinalBits()` で 1 byte として書き出される。
- 符号付き整数として扱いたい値も、保存上はそのまま下位ビット列になる。読み側は `int` として受け取るため、32 bit 幅以外は基本的に非負値として扱われる。

## 共通プリミティブ

| 型 | 保存形式 |
| --- | --- |
| boolean | 1 bit。`true = 1`, `false = 0` |
| byte | 8 bit |
| short相当 | 16 bit |
| int相当 | 32 bit |
| string | 先に長さを指定ビット幅で保存し、その後に文字列 byte を 8 bit ずつ保存。長さ 0 は `null` |
| NBT | 存在フラグ boolean、存在する場合は 15 bit 長さ + gzip 圧縮 NBT byte列 |
| Item | `NO_ITEM_IDS` 以降は registry name の string。旧版は 16 bit 数値 ID を読むだけで無視 |
| ItemStack | Item、必要なら stack size 16 bit、damage 16 bit、NBT |

文字列は `String.getBytes()` / `new String(bytes)` で処理されており、明示 charset は指定されていません。ツール側で再実装する場合は、対象環境と同じ文字コードを意識する必要があります。

## 主なビット幅

`DataBitHelper` で定義されている代表値です。

| 名前 | bit数 | 用途 |
| --- | ---: | --- |
| `QUEST_DESCRIPTION_LENGTH` | 16 | クエスト本文、セット説明、コマンド報酬 |
| `QUEST_NAME_LENGTH` | 5 | クエスト名、タスク名、評判名など。最大 31 byte |
| `NAME_LENGTH` | 5 | Mob名、Location名 |
| `MOB_ID_LENGTH` | 10 | Mob ID |
| `PASS_CODE` | 7 | lock.txt のコード |
| `QUEST_SETS` | 5 | クエストセット数/ID |
| `QUESTS` | 10 | クエスト数/ID |
| `TASKS` | 4 | タスク数/ID |
| `TASK_TYPE` | 4 | タスク種別 |
| `REWARDS` | 3 | 報酬数 |
| `REPUTATION` | 8 | 評判 ID/数 |
| `REPUTATION_VALUE` | 32 | 評判値 |
| `GROUP_COUNT` | 10 | 報酬バッググループ数/ID |
| `TIER_COUNT` | 7 | バッグ tier 数/ID |
| `WORLD_COORDINATE` | 32 | 座標、dimension、半径 |

旧版では一部の bit 数が変わります。例として、`SETS` より前の `QUESTS` は 7 bit、`REPEATABLE_QUESTS` より前の `PLAYERS` は 10 bit、`REPUTATION_KILL` より前の `TASK_TYPE` は 3 bit です。

## ファイル全体の保存順

現行版の `quests.hqm` は概ね次の順序です。

1. `fileVersion` 8 bit
2. `passCode` string(`PASS_CODE`)
3. メイン説明 string(`QUEST_DESCRIPTION_LENGTH`)
4. クエストセット一覧
5. 評判一覧
6. クエスト一覧
7. 報酬バッグ tier 一覧
8. 報酬バッグ group 一覧
9. 最終 byte の余り bit

## クエストセット一覧

1. set 数 `QUEST_SETS`
2. 各 set:
   - name string(`QUEST_NAME_LENGTH`)
   - description string(`QUEST_DESCRIPTION_LENGTH`)
   - reputation bar 数 `BYTE`
   - reputation bar データ `INT` を個数分

`REPUTATION_BARS` より古いファイルには reputation bar はありません。

## 評判一覧

`REPUTATION` 以降のバージョンで保存されます。

1. reputation 数 `REPUTATION`
2. 各 reputation:
   - id `REPUTATION`
   - name string(`QUEST_NAME_LENGTH`)
   - neutral marker name string(`QUEST_NAME_LENGTH`)
   - marker 数 `REPUTATION_MARKER`
   - 各 marker:
     - name string(`QUEST_NAME_LENGTH`)
     - value `REPUTATION_VALUE`

## クエスト一覧

1. quest スロット数 `QUESTS`
2. id `0..count-1` の順に:
   - exists boolean
   - exists が false の場合、その id は空き
   - exists が true の場合、以下を保存

クエスト本体:

1. name string(`QUEST_NAME_LENGTH`)
2. description string(`QUEST_DESCRIPTION_LENGTH`)
3. GUI x `QUEST_POS_X`
4. GUI y `QUEST_POS_Y`
5. big icon boolean
6. set id `QUEST_SETS`
7. icon 有無 boolean、あれば ItemStack(sizeなし)
8. prerequisite 有無 boolean、あれば count `QUESTS` + quest id `QUESTS` の配列
9. option link 有無 boolean、あれば count `QUESTS` + quest id `QUESTS` の配列
10. repeat info
11. trigger type `TRIGGER_TYPE`、必要なら trigger task count `TASKS`
12. modified parent requirement 有無 boolean、あれば parent requirement count `QUESTS`
13. task 数 `TASKS` + task 配列
14. 通常アイテム報酬
15. 選択式アイテム報酬
16. コマンド報酬
17. 評判報酬

## Repeat / Trigger

Repeat:

1. repeat type `REPEAT_TYPE`
2. repeat type が時間を使う場合、合計時間 `HOURS`

Trigger:

- `TRIGGER_TYPE` の ordinal を保存。
- trigger type が task count を使う場合のみ `TASKS` を追加保存。

## タスク共通部

各タスクは次の共通ヘッダーを持ちます。

1. task type `TASK_TYPE`
2. task title string(`QUEST_NAME_LENGTH`)
3. task long description string(`QUEST_DESCRIPTION_LENGTH`)
4. task type ごとの payload

task type の ordinal は `Quest.TaskType` の順序です。

| ordinal | ID | クラス |
| ---: | --- | --- |
| 0 | `consume` | `QuestTaskItemsConsume` |
| 1 | `craft` | `QuestTaskItemsCrafting` |
| 2 | `location` | `QuestTaskLocation` |
| 3 | `consumeQDS` | `QuestTaskItemsConsumeQDS` |
| 4 | `detect` | `QuestTaskItemsDetect` |
| 5 | `kill` | `QuestTaskMob` |
| 6 | `death` | `QuestTaskDeath` |
| 7 | `reputation` | `QuestTaskReputationTarget` |
| 8 | `reputationKill` | `QuestTaskReputationKill` |

## タスク payload

### Item 系タスク

`consume`、`craft`、`consumeQDS`、`detect` は `QuestTaskItems` の保存形式を使います。

1. item/fluid 要求数 `TASK_ITEM_COUNT`
2. 各要求:
   - isItem boolean
   - isItem の場合:
     - Item
     - damage `SHORT`
     - NBT
     - required amount `TASK_REQUIREMENT`
     - precision string(`ITEM_PRECISION`)
   - fluid の場合:
     - FluidStack を NBT として保存

`CUSTOM_PRECISION_TYPES` より古いファイルでは precision は string ではなく旧 2 bit enum として読みます。

### Location タスク

1. location 数 `TASK_LOCATION_COUNT`
2. 各 location:
   - icon 有無 boolean、あれば Item + damage `SHORT` + NBT
   - name string(`NAME_LENGTH`)
   - x `WORLD_COORDINATE`
   - y `WORLD_COORDINATE`
   - z `WORLD_COORDINATE`
   - radius `WORLD_COORDINATE`
   - visibility `LOCATION_VISIBILITY`
   - dimension `WORLD_COORDINATE`

### Kill タスク

1. mob 条件数 `TASK_MOB_COUNT`
2. 各 mob:
   - icon 有無 boolean、あれば Item + damage `SHORT` + NBT
   - name string(`NAME_LENGTH`)
   - mob id string(`MOB_ID_LENGTH`)
   - kill count `KILL_COUNT`
   - exact boolean

### Death タスク

- required deaths `DEATHS`

### Reputation タスク

1. setting 数 `REPUTATION_SETTING`
2. 各 setting:
   - reputation id `REPUTATION`
   - lower marker 有無 boolean、あれば marker id `REPUTATION_MARKER`
   - upper marker 有無 boolean、あれば marker id `REPUTATION_MARKER`
   - inverted boolean

### Reputation Kill タスク

`QuestTaskReputation` の payload の後に、追加で:

- required kills `DEATHS`

## 報酬

アイテム報酬と選択式アイテム報酬は同じ形式です。

1. reward 配列有無 boolean
2. 有る場合:
   - non-null 報酬数 `REWARDS`
   - ItemStack(sizeあり) を個数分

コマンド報酬:

1. コマンド有無 boolean
2. 有る場合:
   - count `REWARDS`
   - command string(`QUEST_DESCRIPTION_LENGTH`) を個数分

評判報酬:

1. count `REPUTATION_REWARD`
2. 各報酬:
   - reputation id `REPUTATION`
   - value `REPUTATION_VALUE`

## 報酬バッグ tier

1. tier 数 `TIER_COUNT`
2. 各 tier:
   - name string(`QUEST_NAME_LENGTH`)
   - color ordinal `COLOR`
   - `BagTier.values().length` 個の weight `WEIGHT`

## 報酬バッグ group

1. group 数 `GROUP_COUNT`
2. 各 group:
   - group id `GROUP_COUNT`
   - name string(`QUEST_NAME_LENGTH`)
   - tier id `TIER_COUNT`
   - item 数 `GROUP_ITEMS`
   - ItemStack(sizeあり) を個数分
   - limit 有無 boolean
   - limit がある場合 `LIMIT`

## 翻訳対象になりやすい文字列

ローカライズ用途で抽出する候補は次の通りです。

- メイン説明
- クエストセット名、クエストセット説明
- 評判名、neutral marker 名、marker 名
- クエスト名、クエスト説明
- タスク名、タスク説明
- Location タスクの location name
- Kill タスクの mob 表示名
- 報酬バッグ tier 名
- 報酬バッグ group 名
- コマンド報酬は文字列だが、コマンド構文なので通常は翻訳しない方が安全

## 実装時の注意

- 文字列長は byte 長で制限されます。特に `QUEST_NAME_LENGTH` は 5 bit なので最大 31 byte です。日本語は 1 文字が複数 byte になるため、切り詰め時に文字境界を壊さない処理が必要です。
- null 文字列と空文字列はどちらも長さ 0 として保存され、読み込み結果は `null` になります。
- bit 単位で連続しているため、フィールドを 1 つ読み間違えると以降すべてがずれます。
- 旧版互換の分岐が多いため、必ず先頭の `FileVersion` を読んでからビット幅と存在フィールドを切り替える必要があります。
- ItemStack と FluidStack は Minecraft/Forge の registry と NBT 実装に依存します。翻訳ツールで文字列だけを置換する場合も、未解析 byte を壊さず保持する設計が必要です。
