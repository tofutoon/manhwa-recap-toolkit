# Recap script prompt

A recap script is the narration a voice reads over the panels: chapter dialogue rewritten as a short third-person story. Raw speech bubbles are not a script, because they skip who is speaking, where the scene is and what just happened.

The prompt below works with ChatGPT, Gemini, Claude or any other chat model. Use the same prompt for every chapter, so the whole series sounds like one voice.

## The prompt

Replace the names, the word count and the style example with your own series.

```text
Rewrite this chapter as third-person narration for a voice track. Plain sentences, no headings, no lists.

Use only events and lines in the text below. Do not add scenes, motives or outcomes that are not in the text.

Spell these names exactly: Jin, Seo, Kael, the Black Gate.

Remove sound effects such as KRAAK or WHAM. Turn status windows into one short sentence.

About 800 words. Sentences under 20 words. Example style: Jin froze at the gate while Seo counted the guards.

Chapter text:
<paste the chapter text here, in panel order>
```

## The five rules

1. **Role and format.** "Rewrite this chapter as third-person narration for a voice track. Plain sentences, no headings, no lists."
2. **Source only.** "Use only events and lines in the text below. Do not add scenes, motives or outcomes that are not in the text."
3. **Glossary.** "Spell these names exactly: Jin, Seo, Kael, the Black Gate." Paste the same glossary for every chapter. Keep it in [name-glossary-template.md](name-glossary-template.md).
4. **Clean-up.** "Remove sound effects such as KRAAK or WHAM. Turn status windows into one short sentence."
5. **Length and style.** "About 800 words. Sentences under 20 words. Example style: Jin froze at the gate while Seo counted the guards."

At a narration pace of 150 words per minute, 800 words is about 5 minutes and 20 seconds of audio. To check the timing after you make subtitles, use `scripts/srt_tight_cues.py`.

## Worked example

Three panels: a status window, a shout and an explosion. The raw OCR text is:

```text
[Mana: 12] Run, Jin! KRAAK
```

Read aloud as it is, a voice says the word "KRAAK" and the number twelve with no context. The recap script for the same panels reads:

```text
Jin had twelve mana points left when Seo screamed at him to run, and the wall behind them gave way.
```

The script names the speakers, drops the sound effect and keeps the facts.

## Check the output

- Read the script beside the chapter pages. Mark any event you cannot point to on a panel, and cut it.
- Check every name against the glossary.
- Ask the model for a word count, then count yourself. Models miss length targets.

## The commentary must be yours

Let the model write the retelling. Then add two or three sentences in your own words at the end of each episode: what the chapter changed, which choice made sense, what you expect next.

YouTube's channel monetization policies treat mass-produced or repetitive videos as "inauthentic content". A model-written opinion repeats easily across channels, so do not let the model write your commentary. This is general information, not legal advice.

Source: [Manhwa recap script with AI: prompt template and examples](https://tofutoon.com/blog/manhwa-recap-script-ai-prompt?utm_source=github&utm_medium=readme&utm_campaign=recap_toolkit).
