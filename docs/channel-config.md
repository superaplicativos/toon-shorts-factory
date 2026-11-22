# channel.json reference

Each channel lives in `channels/<slug>/` with two files you edit:

* `channel.json`: who the channel is (niche, cast, formats, YouTube settings)
* `topics.json`: a list of topics. With `"topic_source": "wikipedia"` each item is a Wikipedia article title in
  `wikipedia_lang` (spaces or underscores, e.g. `"Mount_Everest"`). 150 to 300 topics is a healthy start.

## Top level

| Key | Example | Notes |
|---|---|---|
| `channel_name` | `"World Tour Toons"` | used in the prompt |
| `niche` | `"Travel and geography facts..."` | 1 to 2 sentences, the promise of every episode |
| `audience` | `"curious kids, teens and adults in the US"` | |
| `language` / `language_name` | `"en"` / `"American English"` | language of lines, title, tags |
| `topic_source` | `"wikipedia"` or `"list"` | `list` = no fact source, the LLM uses general knowledge (no fact check, riskier) |
| `wikipedia_lang` | `"en"`, `"pt"`, `"es"` | |
| `videos_per_day` | `2` | `run` stops after this many per day |
| `schedule` | `["14:10", "20:10"]` | local PC time used by `schedule` |
| `no_repeat_last` | `150` | a topic is not reused within the last N episodes |
| `text_providers` | `["pollinations"]` | add `"deepseek"` first if you have a DeepSeek key |
| `target_seconds` | `"35 to 45"` | |
| `video` | `{"lines": [8, 12], "words": [65, 105], "max_words_per_line": 16}` | length control |
| `cast` | see below | 2 or 3 people + optional pet works best |
| `formats` | `{"key": "description for the writer"}` | 3 to 6 formats, they rotate |
| `format_weights` | `{"weird_facts": 1.4}` | higher = more frequent |
| `hide_topic_in_title_formats` | `["guess_where"]` | for mystery formats |
| `extra_rules` | `["Skip wars..."]` | added to the built-in safety and virality rules |
| `seo_seeds` | `["{topic} facts", "why is {topic}"]` | YouTube autocomplete queries |
| `background_style` | text | optional, replaces the default paper-cutout background style |
| `subtitles` | `{"font": "Arial Black", "size": 82, "margin": 120, "words_per_block": 3}` | |
| `description_footer` | text | added to every description |
| `source_credit` | `'Facts source: Wikipedia, "{title}" ({url}), CC BY-SA 4.0.'` | translate it for your language |
| `voice_fallbacks` | `{"en-US-AvaNeural": "en-US-AriaNeural"}` | used if a voice is unavailable |
| `youtube` | `{"privacy": "public", "category_id": "19", "made_for_kids": false, "fixed_tags": [...]}` | categories: 19 Travel, 27 Education, 24 Entertainment, 28 Science & Tech, 22 People & Blogs |

## Cast

```json
"MILO": {
  "role": "energetic traveler with a camera, makes bold guesses that are often wrong",
  "voice": ["en-US-AndrewNeural", "+8%", "+10Hz"],
  "look": {"height": 620, "shirt": "#EB781E", "pants": "#3C5078", "shoes": "#F0F0F0",
           "hair_color": "#3C2819", "hair_style": "cap", "cap_color": "#1E6EC8", "prop": "camera"}
}
```

* IDs are UPPERCASE and short (the script uses them).
* `role` is the personality the writer follows. Contrast makes comedy: the clumsy guesser, the one who knows, the sidekick.
* `voice` = [edge-tts voice, rate, pitch]. Raise pitch (+30 to +80Hz) for kids and pets, lower it (-20Hz) for older characters.
  List voices with `edge-tts --list-voices`. Good picks: en-US-AndrewNeural, en-US-AvaNeural, en-US-AnaNeural (child),
  en-GB-RyanNeural, pt-BR-AntonioNeural, pt-BR-FranciscaNeural, es-MX-JorgeNeural, es-MX-DaliaNeural, fr-FR-HenriNeural, de-DE-KatjaNeural.

### look

| Key | Values |
|---|---|
| `height` | 520 (small kid) to 760 (tall adult) |
| `shirt`, `pants`, `shoes`, `hair_color`, `skin`, `cap_color`, `gloves` | hex colors; `"pants": null` shows bare legs |
| `hair_style` | `short`, `buns`, `messy`, `side_ponytail`, `cap`, `afro`, `bowl`, `wild`, `bald` |
| `prop` (left hand) | `phone`, `camera`, `map`, `notepad`, `plush`, `backpack`, `belt`, `none` |
| flags | `shorts`, `dress`, `lab_coat`, `earrings`, `glasses`, `goggles`, `blush`, `adult` (smaller head, adult proportions) |
| `shirt_print` | `circuit`, `dino`, `tech` |
| `pet` | `"parrot"` or `"dog"` (replaces the human body; keep the pet to max ~3 lines per episode) |

Run `toonshorts cast <slug>` after every change and look at `cast_preview.png`.

**Do not recreate famous characters** (TV, games, mascots). Original characters are what makes the channel yours and keeps it safe.
