---
name: toon-shorts-channel
description: Build and launch an automated paper-cutout cartoon YouTube Shorts channel for any niche and language with the open-source toon-shorts-factory (free stack). Use when someone wants a faceless/animated Shorts channel, a talking-cartoon channel, or asks to set up, customize or debug toon-shorts-factory.
---

# Toon Shorts channel builder

You help a person go from "I want a channel about X" to two cartoon Shorts published per day, using
https://github.com/superaplicativos/toon-shorts-factory. Everything in the stack is free: Pollinations (text and
backgrounds), edge-tts (voices), Wikipedia (facts), ffmpeg, YouTube Data API.

Work in the person's language. Do the work yourself whenever you have a shell; only hand them the steps that need
their Google login (creating the YouTube channel, OAuth consent, Pollinations sign-up).

## 1. Get the code running

If the repo is not on their machine yet:

* Windows: `git clone https://github.com/superaplicativos/toon-shorts-factory` (or download the ZIP), then run
  `setup_windows.bat`. It installs Python, ffmpeg and packages inside the folder. Commands are `toonshorts <cmd>`
  from the repo folder.
* macOS/Linux: `./setup.sh` (needs python3 and ffmpeg), then `.venv/bin/python -m toonshorts <cmd>`.

Run `toonshorts check` and fix what it reports.

## 2. Interview (short, then decide)

Ask at most 3 questions, with a recommended default for each:

1. **Niche and promise**: what does every episode deliver? Push toward evergreen, fact-based, visual topics with
   endless supply (places, history, animals, science, food, space, sports history, inventions, myths).
2. **Language/market**: English pays several times more per view than most markets; their native language grows
   faster at first. Recommend English if they are comfortable with it.
3. **Tone/audience**: kids, teens, adults, all ages.

Steer away from niches that break monetization: finance/health/legal advice, news, politics, true crime, tragedy,
anything that needs a real person's likeness, or famous characters (copyright). Explain why in one line.

## 3. Design the channel

Create it with `toonshorts new <slug>` and then write `channels/<slug>/channel.json`
(reference: `docs/channel-config.md`, working examples in `channels/world-tour-toons` and
`channels/historia-em-1-minuto`).

* **Cast of 2 to 3 + optional pet.** Make the personalities contrast: one who guesses wrong or exaggerates, one who
  knows the facts, a sidekick with one-liners. Original names and looks only, never a copy of a known character.
  Pick distinct shirt colors, hair styles and props so each one is recognizable at a glance on a phone.
* **Voices**: different edge-tts voice or pitch per character (kids/pets +30 to +80Hz, older characters −20Hz).
* **4 to 6 formats** written as instructions to a writer (see examples). Mix "list of facts", "myth or fact",
  "guess what/where", "could you survive", "why is it like that", "versus". Give one format a mystery title
  (`hide_topic_in_title_formats`).
* **topics.json**: 200+ Wikipedia article titles in `wikipedia_lang`. Prefer articles that are long and full of
  numbers and oddities. If you can reach the web, spot-check that titles exist; the pipeline skips missing ones.
* **youtube**: category (19 travel, 27 education, 28 science, 24 entertainment), `made_for_kids` only if the
  audience really is children, fixed tags.
* Translate `description_footer` and `source_credit` into the channel language.

Then run `toonshorts cast <slug>` and show the person `cast_preview.png`. Iterate until they like the cast.

## 4. Keys (person does the sign-ins, you write the files)

Follow `docs/youtube-setup.md`:

* `secrets/pollinations_key.txt` from https://enter.pollinations.ai
* `secrets/client_secret.json`: Google Cloud project → enable YouTube Data API v3 → consent screen (External,
  **publish to Production**) → OAuth client **Desktop app** → download JSON.

Never print, log or commit keys. `secrets/` and `channels/*/.secrets/` are git-ignored.

## 5. Test, connect, pilot, schedule

1. `toonshorts preview <slug>`: makes one video without uploading. Open `output/<date>_N/video_final.mp4` (or extract
   a few frames with ffmpeg) and check: characters visible, mouths moving, subtitles readable, 30 to 45 s.
2. The person creates the YouTube channel (Settings → Add or manage your channels → Create a channel).
3. `toonshorts authorize <slug>` and the person picks that channel on Google's screen. "Google hasn't verified this
   app" → Advanced → Go to app (it is their own app). If the browser never returns, use `--paste`.
4. `toonshorts pilot <slug>` uploads as **private**. Ask them to review it in YouTube Studio.
5. `toonshorts schedule <slug>`: Windows Task Scheduler at the `schedule` times (PC must be on), or crontab lines.

## 6. Growth loop (tell them, briefly)

* Shorts RPM is tiny. The Partner Program needs 1,000 subs + 10M Shorts views in 90 days or 4,000 long-form watch
  hours (doubling for new applicants from Feb 1, 2027). Recommend a weekly long episode (8 to 10 min) written as
  its own story with the same cast, not a compilation.
* Every week: check `history.json` (views per topic and format), raise `format_weights` of winners, add topics like
  the top ones, retire weak formats, reply to comments.
* Keep the inauthentic-content defenses: recurring cast, real sourced facts, rotating formats, human review.

## Debugging

See `docs/troubleshooting.md`. Each episode folder has `run.log`, `state.json` (topic and source), `script.json`,
`ffmpeg_passo1.txt` / `ffmpeg_passo2.txt`. Re-running the same command resumes the unfinished episode of the day.
Do not reintroduce a one-pass ffmpeg render or `loudnorm`: both hang on some Windows builds.
