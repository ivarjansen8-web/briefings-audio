# briefings-audio

Spoken versions of my daily dashboard briefings, refreshed every morning at 08:41 (Amsterdam) by a scheduled Claude task. Each file is the full briefing as plain text (links, source citations, Markdown and emoji removed) for an Apple Shortcut to read aloud ("Get Contents of URL" → "Get Text from Input" → "Speak Text").

| Briefing | Link |
|---|---|
| Daily news | https://raw.githubusercontent.com/ivarjansen8-web/briefings-audio/main/news.txt |
| Middle East | https://raw.githubusercontent.com/ivarjansen8-web/briefings-audio/main/mena.txt |
| Government | https://raw.githubusercontent.com/ivarjansen8-web/briefings-audio/main/govt.txt |
| Classics | https://raw.githubusercontent.com/ivarjansen8-web/briefings-audio/main/classics.txt |

Briefings you add yourself on the dashboard get their own file, `<id>.txt`; the dashboard shows each briefing's link.

`speak.py` does the conversion: `python3 speak.py OUT_DIR briefing.json ...`
