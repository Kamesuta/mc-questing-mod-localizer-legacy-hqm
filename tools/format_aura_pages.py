#!/usr/bin/env python3
"""
Aura-Cascade の `aura.page.*` 向けに、本文へ自動で `<br>` を挿入するツール。
"""

from __future__ import annotations

import argparse
from pathlib import Path


# 日本語は空白で区切られないため、句読点や空白の直後を優先して改行候補にする。
BREAKABLE_CHARS = set(" 　、。，．！？!?：:；;）)]｝}」』】〉》・")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aura-Cascade の lang ファイルに `<br>` を自動挿入します。"
    )
    parser.add_argument("path", type=Path, help="対象の .lang ファイル")
    parser.add_argument(
        "--prefix",
        default="aura.page.",
        help="整形対象のキー接頭辞。既定値: aura.page.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=13,
        help="1 行に入れる表示文字数。色コードや `<br>` は数えません。既定値: 13",
    )
    parser.add_argument(
        "--ascii-width",
        type=float,
        default=0.6,
        help="ASCII 文字 1 文字の表示幅。既定値: 0.6",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="ファイルを直接更新します。指定しない場合は標準出力へ結果を出します。",
    )
    parser.add_argument(
        "--normalize-existing-breaks",
        action="store_true",
        help="既存の `<br>` をいったん畳んでから再整形します。",
    )
    parser.add_argument(
        "--separator",
        default="<br>",
        help="折り返し位置に挿入する区切り文字列。既定値: <br>",
    )
    return parser.parse_args()


def is_format_code(text: str, index: int) -> bool:
    # `&1` や `&o` などの Minecraft 書式コードは見た目の幅を消費しない。
    return text[index] == "&" and index + 1 < len(text)


def is_ascii_word_char(char: str) -> bool:
    # 英単語や数字は途中で折ると見た目が悪いので、連続部分を 1 トークンとして扱う。
    return char.isascii() and (char.isalnum() or char in "_-'/.:")


def tokenize(text: str, ascii_width: float) -> list[tuple[str, float, bool]]:
    # 戻り値:
    # - token_text: 実際に出力する文字列
    # - visible_width: 表示幅として数える長さ
    # - breakable_after: このトークンの直後で改行しやすいか
    tokens: list[tuple[str, float, bool]] = []
    i = 0

    while i < len(text):
        if is_format_code(text, i):
            tokens.append((text[i : i + 2], 0, False))
            i += 2
            continue

        char = text[i]
        if is_ascii_word_char(char):
            j = i + 1
            while j < len(text) and is_ascii_word_char(text[j]):
                j += 1
            token = text[i:j]
            tokens.append((token, len(token) * ascii_width, False))
            i = j
            continue

        char_width = ascii_width if char.isascii() else 1.0
        tokens.append((char, char_width, char in BREAKABLE_CHARS))
        i += 1

    return tokens


def previous_visible_char(text: str, index: int) -> str:
    i = index - 1
    while i >= 0:
        if i > 0 and text[i - 1] == "&":
            i -= 2
            continue
        return text[i]
    return ""


def next_visible_char(text: str, index: int) -> str:
    i = index
    while i < len(text):
        if is_format_code(text, i):
            i += 2
            continue
        return text[i]
    return ""


def collapse_existing_breaks(value: str) -> str:
    # 既存の `<br>` を全面的に信用せず、単語連結だけ壊さない形で一旦畳む。
    parts: list[str] = []
    i = 0

    while i < len(value):
        if value.startswith("<br>", i):
            prev_char = previous_visible_char(value, i)
            next_char = next_visible_char(value, i + 4)

            # 英単語の途中だけは単純連結し、英単語どうしの境目らしい場所だけ空白を戻す。
            if prev_char and next_char and is_ascii_word_char(prev_char) and is_ascii_word_char(next_char):
                if prev_char.islower() and next_char.isupper():
                    parts.append(" ")
                elif prev_char.isalpha() and next_char.isalpha():
                    parts.append("")
                else:
                    parts.append(" ")

            i += 4
            continue

        parts.append(value[i])
        i += 1

    return "".join(parts)


def wrap_segment(text: str, width: float, ascii_width: float, separator: str) -> str:
    if width <= 0 or not text:
        return text

    lines: list[str] = []
    current: list[tuple[str, float, bool]] = []
    visible_count = 0.0
    last_breakable_token_index = -1

    for token_text, token_width, breakable_after in tokenize(text, ascii_width):
        current.append((token_text, token_width, breakable_after))
        visible_count += token_width

        if breakable_after:
            last_breakable_token_index = len(current)

        if visible_count > width:
            if last_breakable_token_index > 0:
                # 直近の自然な区切りで折り返す。
                line = join_tokens(current[:last_breakable_token_index]).rstrip(" 　")
                remainder_text = join_tokens(current[last_breakable_token_index:]).lstrip(" 　")
                lines.append(line)
                current = tokenize(remainder_text, ascii_width)
                visible_count = sum(token[1] for token in current)
                last_breakable_token_index = find_last_breakable(current)
            else:
                # 区切りがない場合のみ、トークン単位で機械的に折り返す。
                overflow = current.pop()
                lines.append(join_tokens(current))
                current = [overflow]
                visible_count = overflow[1]
                last_breakable_token_index = find_last_breakable(current)

    if current:
        lines.append(join_tokens(current).rstrip(" 　"))

    return separator.join(filter(None, lines))


def visible_length(text: str, ascii_width: float) -> float:
    length = 0.0
    i = 0
    while i < len(text):
        if is_format_code(text, i):
            i += 2
            continue
        length += ascii_width if text[i].isascii() else 1.0
        i += 1
    return length


def join_tokens(tokens: list[tuple[str, float, bool]]) -> str:
    return "".join(token[0] for token in tokens)


def find_last_breakable(tokens: list[tuple[str, float, bool]]) -> int:
    # 折り返し後の残り行に対して、改めて改行候補位置を計算する。
    last_breakable_index = -1
    for index, token in enumerate(tokens, start=1):
        if token[2]:
            last_breakable_index = index
    return last_breakable_index


def wrap_value(
    value: str,
    width: float,
    ascii_width: float,
    normalize_existing_breaks: bool,
    separator: str,
) -> str:
    # 既存の `<br>` を段落区切りとして尊重し、各段落だけを再整形する。
    if normalize_existing_breaks:
        return wrap_segment(collapse_existing_breaks(value), width, ascii_width, separator)

    segments = value.split("<br>")
    wrapped_segments = [wrap_segment(segment, width, ascii_width, separator) for segment in segments]
    return separator.join(wrapped_segments)


def format_lang_text(
    text: str,
    prefix: str,
    width: float,
    ascii_width: float,
    normalize_existing_breaks: bool,
    separator: str,
) -> str:
    lines = text.splitlines()
    formatted_lines: list[str] = []

    for line in lines:
        if "=" not in line:
            formatted_lines.append(line)
            continue

        key, value = line.split("=", 1)
        if not key.startswith(prefix):
            formatted_lines.append(line)
            continue

        # 既存の改行は一旦正規化し、13 文字幅基準で再計算する。
        normalized = value.replace("<BR>", "<br>")
        formatted_lines.append(
            f"{key}={wrap_value(normalized, width, ascii_width, normalize_existing_breaks, separator)}"
        )

    trailing_newline = "\n" if text.endswith("\n") else ""
    return "\n".join(formatted_lines) + trailing_newline


def main() -> None:
    args = parse_args()
    original = args.path.read_text(encoding="utf-8")
    formatted = format_lang_text(
        original,
        args.prefix,
        args.width,
        args.ascii_width,
        args.normalize_existing_breaks,
        args.separator,
    )

    if args.in_place:
        args.path.write_text(formatted, encoding="utf-8", newline="\n")
        return

    print(formatted, end="")


if __name__ == "__main__":
    main()
