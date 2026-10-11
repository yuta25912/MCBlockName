"""blocks.json のチェックと整形。

  python3 .github/scripts/blocks.py check   # 中身のエラーだけ調べる（PR 用）
  python3 .github/scripts/blocks.py format  # エラーがなければ並べ替えて書き直す（main 用）
"""
import json
import re
import sys

PATH = "blocks.json"
FORMAT_VERSION = 1
KEY = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")
YOMI = re.compile(r"^[ぁ-ゖー]+$")
FIELDS = {"name", "yomi", "aliases"}


def no_duplicates(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError(f"キー {k} が2回出てきます")
        seen[k] = v
    return seen


def load():
    with open(PATH, encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=no_duplicates)


def validate(data):
    errors = []
    if data.get("formatVersion") != FORMAT_VERSION:
        errors.append(f"formatVersion は {FORMAT_VERSION} にしてください")
    extra = set(data) - {"formatVersion", "blocks"}
    if extra:
        errors.append(f"知らない項目があります: {', '.join(sorted(extra))}")
    blocks = data.get("blocks")
    if not isinstance(blocks, dict):
        return errors + ["blocks がオブジェクトではありません"]
    for key, e in blocks.items():
        where = f"{key}:"
        if not KEY.match(key):
            errors.append(f"{where} キーは小文字の名前空間付きID（例: minecraft:sand）にしてください")
        if not isinstance(e, dict):
            errors.append(f"{where} 中身がオブジェクトではありません")
            continue
        extra = set(e) - FIELDS
        if extra:
            errors.append(f"{where} 知らない項目があります: {', '.join(sorted(extra))}")
        if not isinstance(e.get("name"), str) or not e["name"].strip():
            errors.append(f"{where} name がありません")
        if not isinstance(e.get("yomi"), str) or not YOMI.match(e["yomi"]):
            errors.append(f"{where} yomi はひらがなと「ー」だけで書いてください")
        if "aliases" in e:
            a = e["aliases"]
            if not isinstance(a, list) or not a or not all(isinstance(s, str) and s.strip() for s in a):
                errors.append(f"{where} aliases は空でない文字列の配列にしてください")
            elif len(set(a)) != len(a):
                errors.append(f"{where} aliases に同じものが2回入っています")
    return errors


def dump(data):
    s = lambda v: json.dumps(v, ensure_ascii=False)
    blocks = data["blocks"]
    keys = sorted(blocks)
    lines = ["{", f'  "formatVersion": {data["formatVersion"]},', '  "blocks": {']
    for n, key in enumerate(keys):
        e = blocks[key]
        inner = [f'      "name": {s(e["name"])}', f'      "yomi": {s(e["yomi"])}']
        if "aliases" in e:
            inner.append(f'      "aliases": [{", ".join(s(a) for a in e["aliases"])}]')
        lines.append(f"    {s(key)}: {{")
        lines.append(",\n".join(inner))
        lines.append("    }" + ("," if n < len(keys) - 1 else ""))
    lines += ["  }", "}"]
    return "\n".join(lines) + "\n"


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    try:
        data = load()
    except ValueError as err:
        print(f"::error file={PATH}::JSON として読めません: {err}")
        return 1
    errors = validate(data)
    for err in errors:
        print(f"::error file={PATH}::{err}")
    if errors:
        return 1
    if mode == "format":
        with open(PATH, "w", encoding="utf-8") as f:
            f.write(dump(data))
    print(f"OK: {len(data['blocks'])} ブロック")
    return 0


if __name__ == "__main__":
    sys.exit(main())
