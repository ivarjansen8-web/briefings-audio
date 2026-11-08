#!/usr/bin/env python3
"""Turn a dashboard briefing (JSON with kind, date, title, body in Markdown)
into plain text for Siri to read aloud.

Nothing is shortened. Only what doesn't work when spoken is removed:
links and URLs, source citations, Markdown symbols, emoji and tables.

Usage: python3 speak.py OUT_DIR briefing1.json [briefing2.json ...]
Writes OUT_DIR/<kind>.txt for each briefing. A JSON file may also hold
an optional "name" field (e.g. a custom briefing's topic) used in the intro.
"""
import datetime
import json
import re
import sys

NAMES = {
    "news": "daily news briefing",
    "mena": "Middle East briefing",
    "govt": "government briefing",
    "classics": "classics report",
}

LINK = r"\[([^\]]*)\]\((?:[^()\s]|\([^()\s]*\))+\)"
URL = r"https?://\S+"
MONTHS = {"Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April",
          "Jun": "June", "Jul": "July", "Aug": "August", "Sep": "September",
          "Sept": "September", "Oct": "October", "Nov": "November", "Dec": "December"}
SEP = r"(?:\s*(?:[;,/]|and|via|per|see)\s*)"


def spoken_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.strftime('%A')}, {d.day} {d.strftime('%B')}"


def money(m):
    sym, num, unit = m.group(1), m.group(2), (m.group(3) or "").lower()
    cur = {"$": "dollars", "€": "euros", "£": "pounds"}[sym]
    unit = {"k": " thousand", "m": " million", "mn": " million", "b": " billion",
            "bn": " billion", "t": " trillion", "tn": " trillion"}.get(unit, "")
    return f"{num}{unit} {cur}"


def clean_inline(s):
    # parentheticals that only cite sources: "([Reuters](u); [AP](u))"
    s = re.sub(rf"\s*\(\s*(?:{LINK}{SEP}?)+\s*\)", "", s)
    # links trailing a sentence or bullet are citations: drop them
    s = re.sub(rf"(?:{SEP}?\s*{LINK})+\s*$", "", s)
    s = re.sub(rf"\s+—\s+(?:{LINK}{SEP}?)+\s*$", "", s)
    # any other link keeps its words
    s = re.sub(LINK, r"\1", s)
    s = re.sub(URL, "", s)
    s = re.sub(r"\*\*|__|`", "", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)(?<!\s)\*(?![\w*])", r"\1", s)
    s = re.sub(r"(?<![\w_])_(?!\s)([^_]+?)(?<!\s)_(?![\w_])", r"\1", s)
    s = re.sub(r"([$€£])\s?(\d[\d,]*(?:\.\d+)?)\s?(bn|mn|tn|[kKmMbBtT])?\b", money, s)
    s = re.sub(r"~\s?(?=\d)", "about ", s)
    s = re.sub(r"\be\.g\.,?", "for example", s)
    s = re.sub(r"\bi\.e\.,?", "that is", s)
    s = re.sub(r"\bvs\.?(?=\s)", "versus", s)
    s = re.sub(r"\s&\s", " and ", s)
    s = re.sub(r"(?<=\d)\s?[–-]\s?(?=\d)", " to ", s)
    for a, full in MONTHS.items():
        s = re.sub(rf"\b{a}(?=[.\s,;:)]|$)", full, s)
    s = re.sub(r"\s+→\s+", " to ", s)
    # emoji and pictographs (incl. flags and variation selectors)
    s = re.sub("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍\U0001F1E6-\U0001F1FF]", "", s)
    s = re.sub(r"\(\s*\)|\[\s*\]", "", s)
    s = re.sub(r"[ \t]{2,}", " ", s).strip()
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r"[,;:]\s*$", ".", s)
    return s


def end(s):
    return s if not s or s[-1] in ".!?…\"'”’)" else s + "."


def convert(md):
    out, para = [], []

    def flush():
        if para:
            out.append(" ".join(para))
            para.clear()

    for raw in md.replace("\r", "").split("\n"):
        line = raw.strip()
        if not line or re.fullmatch(r"[-*_=]{3,}", line):
            flush()
            continue
        if line.startswith("|"):  # tables don't read well aloud
            continue
        if re.match(r"^\**\s*sources?\s*:", line, re.I):  # "Sources: ..." lines
            continue
        line = re.sub(r"^>\s*", "", line)
        h = re.match(r"^#{1,6}\s+(.*)", line) or re.fullmatch(r"\*\*([^*]{1,120})\*\*:?", line)
        if h and not out and not para and re.search(r"20\d\d", h.group(1)) and re.search(r"briefing|report", h.group(1), re.I):
            continue  # the briefing's own dated title line repeats the intro
        if h:
            flush()
            t = clean_inline(h.group(1))
            if t and not t.lower().startswith("(no top title"):
                out.append(end(t))
            continue
        b = re.match(r"^(?:[-*+•]|\d+[.)])\s+(.*)", line)
        if b:
            flush()
            t = clean_inline(b.group(1))
            if t:
                out.append(end(t))
            continue
        t = clean_inline(line)
        if t:
            para.append(t)
    flush()
    return "\n\n".join(p for p in out if re.search(r"\w", p))


def main():
    out_dir, files = sys.argv[1], sys.argv[2:]
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).date().isoformat()
    try:
        from zoneinfo import ZoneInfo
        today = datetime.datetime.now(ZoneInfo("Europe/Amsterdam")).date().isoformat()
    except Exception:
        pass
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        kind, date = d["kind"], d.get("date") or today
        name = d.get("name") or NAMES.get(kind) or "briefing"
        if d.get("name") and "briefing" not in name.lower():
            name = f"briefing on {name}"
        if date == today:
            intro = f"Here is your {name} for {spoken_date(date)}."
        else:
            intro = f"Today's {name} has not been written yet. Here is the latest one, from {spoken_date(date)}."
        title = clean_inline(d.get("title") or "")
        body = convert(d.get("body") or "")
        first = body.split("\n\n", 1)[0] if body else ""
        parts = [intro]
        if title and title.lower() not in first.lower():
            parts.append(end(title))
        parts += [body, f"That's the end of your {name}. Sources are on your dashboard."]
        text = "\n\n".join(p for p in parts if p).strip() + "\n"
        with open(f"{out_dir}/{kind}.txt", "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"{kind}: {len(text.split())} words, briefing date {date}")


if __name__ == "__main__":
    main()
