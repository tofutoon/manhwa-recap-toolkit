# Edge TTS voice list

`edge-tts-voices-2026-11-01.json` lists the voices of Microsoft Edge's online "Read aloud" text-to-speech service.

- **Date:** 2026-11-01.
- **Count:** 322 voices across 142 locales.
- **How it was made:** `pip install edge-tts` (version 7.3.1) in a fresh virtual environment, then `edge_tts.list_voices()`, the same call behind `edge-tts --list-voices`. Each voice keeps five fields: `name`, `locale`, `gender`, `category` and `personality`.

This is a dated snapshot. Microsoft adds, renames and removes voices over time, so run `edge-tts --list-voices` for the current list.

The voices belong to a Microsoft online service, not to this repo. Whether you may use the audio commercially depends on Microsoft's terms, not on this repo's MIT license.

Example: list the English (US) male voices.

```bash
python -c "import json; d=json.load(open('data/edge-tts-voices-2026-11-01.json')); print([v['name'] for v in d['voices'] if v['locale']=='en-US' and v['gender']=='Male'])"
```
