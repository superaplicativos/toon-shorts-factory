# -*- coding: utf-8 -*-
"""
One episode = pick a topic -> fetch facts -> write a verified script -> voices -> animate -> upload -> log.

Everything niche-specific lives in channels/<slug>/channel.json (+ topics.json). See docs/channel-config.md.
"""
import datetime as dt
import json
import logging
import random
import re
import shutil
import sys
import time
from pathlib import Path

from . import animation, characters, free_ai

log = logging.getLogger("toonshorts")
REPO = free_ai.REPO
UA = {"User-Agent": "toon-shorts-factory/1.0 (https://github.com/superaplicativos/toon-shorts-factory)"}

BASE_RULES = [
    "The FIRST line is the hook: 9 words max. A shocking fact, an impossible-sounding question or a contradiction. "
    "Start mid-action: no greetings, no 'hey guys', no channel name.",
    "Every fact must be concrete (a number, a name, a vivid comparison).",
    "Escalate: the best fact comes last. Keep a curiosity gap between lines.",
    "The last line loops back to the first line OR asks viewers a question to answer in the comments.",
    "Short spoken sentences, natural for the target language. Humor comes from the characters' personalities.",
    "No gore, no tragedy-as-entertainment, no hate, no politics, no sexual content, nothing scary for kids.",
    "Never give financial, medical or legal advice and never present a character as a real expert.",
]


# ════════════════════════════════════════════════════════════════════
# Small helpers
# ════════════════════════════════════════════════════════════════════
def read_json(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(p, data):
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ffmpeg_bin(name="ffmpeg"):
    local = REPO / "tools" / "ffmpeg" / "bin" / (name + ".exe")
    return str(local) if local.exists() else (shutil.which(name) or name)


def setup_log(folder=None):
    log.handlers.clear()
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(fmt)
    log.addHandler(h)
    if folder:
        fh = logging.FileHandler(Path(folder) / "run.log", encoding="utf-8")
        fh.setFormatter(fmt)
        log.addHandler(fh)


def count_words(t):
    return len(re.findall(r"[\w']+", t))


class Channel:
    def __init__(self, slug):
        self.dir = REPO / "channels" / slug
        if not (self.dir / "channel.json").exists():
            raise SystemExit(f"Channel not found: {self.dir / 'channel.json'}")
        self.slug = slug
        self.cfg = read_json(self.dir / "channel.json", {})
        self.history_file = self.dir / "history.json"
        characters.register_cast(self.cfg["cast"])
        self.people = [c for c, v in self.cfg["cast"].items() if not v.get("look", {}).get("pet")]
        self.video = {"resolution": [1080, 1920], "fps": 30, "lines": [8, 12], "words": [65, 105],
                      "max_words_per_line": 16, **self.cfg.get("video", {})}

    @property
    def lang(self):
        return self.cfg.get("language", "en")


# ════════════════════════════════════════════════════════════════════
# Topic + facts
# ════════════════════════════════════════════════════════════════════
def pick(ch, hist, rng):
    topics = read_json(ch.dir / "topics.json", [])
    if not topics:
        raise SystemExit("topics.json is empty. Add topics (Wikipedia article titles if source is wikipedia).")
    recent = {v["topic"] for v in hist["videos"][-ch.cfg.get("no_repeat_last", 150):]}
    free = [t for t in topics if t not in recent] or topics
    last = [v.get("format") for v in hist["videos"][-2:]]
    formats = {k: v for k, v in ch.cfg["formats"].items() if k not in last} or ch.cfg["formats"]
    weights = ch.cfg.get("format_weights", {})
    fmt = rng.choices(list(formats), weights=[weights.get(f, 1.0) for f in formats])[0]
    return rng.choice(free), fmt


def wikipedia(title, lang="en"):
    import requests
    r = requests.get(f"https://{lang}.wikipedia.org/w/api.php", timeout=30, headers=UA, params={
        "action": "query", "prop": "extracts|info", "explaintext": 1, "redirects": 1, "inprop": "url",
        "titles": title.replace("_", " "), "format": "json"})
    r.raise_for_status()
    page = next(iter(r.json()["query"]["pages"].values()))
    text = page.get("extract", "") or ""
    text = re.split(r"\n== (See also|References|External links|Notes|Further reading|Ver também|Referências|"
                    r"Ligações externas|Notas|Bibliografia|Véase también|Referencias|Enlaces externos) ==", text)[0]
    text = re.sub(r"\n{2,}", "\n", text)
    if len(text) < 1500:
        raise RuntimeError(f"Not enough Wikipedia text for {title}")
    return {"title": page.get("title", title), "url": page.get("fullurl", ""), "text": text[:16000]}


def youtube_searches(ch, topic):
    import requests
    out = []
    for pattern in ch.cfg.get("seo_seeds", ["{topic}"]):
        try:
            r = requests.get("https://suggestqueries.google.com/complete/search", timeout=15,
                             headers={"User-Agent": "Mozilla/5.0"},
                             params={"client": "firefox", "ds": "yt", "hl": ch.lang, "q": pattern.format(topic=topic)})
            out += r.json()[1][:6]
        except Exception:
            pass
    return list(dict.fromkeys(out))[:15]


# ════════════════════════════════════════════════════════════════════
# Script
# ════════════════════════════════════════════════════════════════════
def llm(ch, prompt):
    import requests
    msgs = [{"role": "system", "content": "You are a top YouTube Shorts writer. Reply ONLY with valid JSON."},
            {"role": "user", "content": prompt}]
    errors = []
    for provider in ch.cfg.get("text_providers", ["pollinations"]):
        if provider == "deepseek" and free_ai.secret("deepseek_key.txt", "DEEPSEEK_API_KEY"):
            try:
                r = requests.post("https://api.deepseek.com/chat/completions", timeout=180,
                                  headers={"Authorization": f"Bearer {free_ai.secret('deepseek_key.txt', 'DEEPSEEK_API_KEY')}"},
                                  json={"model": "deepseek-chat", "temperature": 1.0, "messages": msgs,
                                        "response_format": {"type": "json_object"}})
                r.raise_for_status()
                return extract_json(r.json()["choices"][0]["message"]["content"]), "deepseek"
            except Exception as e:
                errors.append(f"deepseek: {str(e)[:100]}")
        if provider == "pollinations":
            key = free_ai.chave_pollinations()
            targets = []
            if key:
                targets.append(("https://gen.pollinations.ai/v1/chat/completions", {"Authorization": f"Bearer {key}"},
                                ch.cfg.get("text_model", "openai-large")))
            targets.append(("https://text.pollinations.ai/openai", {}, "openai"))
            for url, hdr, model in targets:
                for _ in range(2):
                    try:
                        r = requests.post(url, timeout=240, headers={**UA, **hdr},
                                          json={"model": model, "messages": msgs, "temperature": 0.9,
                                                "response_format": {"type": "json_object"}})
                        r.raise_for_status()
                        return extract_json(r.json()["choices"][0]["message"]["content"]), "pollinations"
                    except Exception as e:
                        errors.append(f"{url}: {str(e)[:120]}")
                        time.sleep(6)
    raise RuntimeError(" | ".join(errors) or "no text provider configured")


def extract_json(text):
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text[text.find("{"): text.rfind("}") + 1])


def build_prompt(ch, source, fmt, searches, fix=""):
    c, v = ch.cfg, ch.video
    cast = "\n".join(f"- {cid}: {info['role']}" for cid, info in c["cast"].items())
    rules = "\n".join(f"{i + 1}. {r}" for i, r in enumerate(BASE_RULES + c.get("extra_rules", [])))
    fonte = (f"FACT SOURCE (the ONLY source of facts you may use; never invent numbers, dates or claims):\n<<<\n"
             f"{source['text'][:9000]}\n>>>" if source.get("text") else
             "Use only well-established, verifiable facts. If unsure about a fact, leave it out.")
    hide = c.get("hide_topic_in_title_formats", [])
    return f"""Write ONE vertical YouTube Short ({c.get('target_seconds', '35 to 45')} seconds) for the animated channel "{c['channel_name']}".
Channel niche: {c['niche']}
Audience: {c.get('audience', 'general audience')}
Language of ALL spoken lines, title, description and tags: {c.get('language_name', ch.lang)}

THE CAST (recurring, keep their personalities):
{cast}

TOPIC OF THE EPISODE: {source['title']}
FORMAT OF THIS EPISODE: {c['formats'][fmt]}

{fonte}

Real YouTube searches people type about this topic (use the words that fit, for SEO): {', '.join(searches) or 'n/a'}

RULES
{rules}

STRUCTURE
- 3 to 5 scenes. Each scene: "background" = short ENGLISH description of a real, recognizable setting for this topic
  (no people, no text); "cast" = 2 or 3 ids from {', '.join(c['cast'])}; "lines" = list of {{"who": ID, "text": spoken line}}.
- {v['lines'][0]} to {v['lines'][1]} lines total, max {v['max_words_per_line']} words each, {v['words'][0]} to {v['words'][1]} words total.

Also return:
- "title": max 55 characters, curiosity-driven, includes the topic{' EXCEPT in this format (do not reveal it)' if fmt in hide else ''}. No false clickbait. One emoji max at the end.
- "hook_text": 2 to 5 words in CAPS shown on screen during the first 3 seconds.
- "source_sentences": list of the exact sentences (copied word for word from the FACT SOURCE) behind every fact.
- "description": 2 short sentences summarizing the episode + one question for the comments.
- "tags": 12 SEO tags. "hashtags": 3 hashtags.

Return JSON exactly like:
{{"title": "", "hook_text": "", "scenes": [{{"background": "", "cast": [], "lines": [{{"who": "", "text": ""}}]}}], "source_sentences": [""], "description": "", "tags": [""], "hashtags": [""]}}
{fix}"""


def _norm(t):
    return re.sub(r"[^\w ]", " ", t.lower())


def unverified(sentences, source_text):
    """Each cited sentence must match a real sentence of the source (>= 70% of its words)."""
    pool = [set(_norm(f).split()) for f in re.split(r"(?<=[.!?])\s+|\n", source_text) if len(f) > 20]
    bad = []
    for s in sentences:
        words = set(_norm(s).split())
        if len(words) < 4:
            continue
        if max((len(words & p) / len(words) for p in pool), default=0) < 0.7:
            bad.append(s[:80])
    return bad


def validate(ch, r, fmt, topic, source):
    v, problems = ch.video, []
    scenes = r.get("scenes") or []
    lines = [l for s in scenes for l in s.get("lines", [])]
    n = sum(count_words(str(l.get("text", ""))) for l in lines)
    if not 2 <= len(scenes) <= 6:
        problems.append(f"use 3 to 5 scenes (got {len(scenes)})")
    if not v["lines"][0] - 1 <= len(lines) <= v["lines"][1] + 2:
        problems.append(f"use {v['lines'][0]} to {v['lines'][1]} lines (got {len(lines)})")
    if not v["words"][0] - 10 <= n <= v["words"][1] + 15:
        problems.append(f"total words must be {v['words'][0]}-{v['words'][1]} (got {n})")
    if not r.get("title"):
        problems.append("missing title")
    if lines and count_words(lines[0].get("text", "")) > 11:
        problems.append("the first line (hook) must have 9 words max")
    if fmt in ch.cfg.get("hide_topic_in_title_formats", []) and topic.split("(")[0].replace("_", " ").strip().lower() in r.get("title", "").lower():
        problems.append("this format's title must not reveal the topic")
    if source.get("text"):
        if len(r.get("source_sentences") or []) < 2:
            problems.append("source_sentences must list the source sentences you used")
        bad = unverified(r.get("source_sentences") or [], source["text"])
        if bad:
            problems.append("these source_sentences are not word-for-word from the source; use only real source "
                            "sentences: " + " | ".join(bad[:3]))
    return problems


def to_animation(ch, r):
    """Normalize the LLM JSON into the structure the animation engine expects."""
    valid = set(ch.cfg["cast"])
    scenes = []
    for s in r["scenes"]:
        ids = [str(p).upper() for p in s.get("cast", []) if str(p).upper() in valid]
        falas = []
        for l in s.get("lines", []):
            who = str(l.get("who", "")).upper().strip()
            if who not in valid:
                who = ch.people[0]
            text = re.sub(r"\s*[—–]\s*", ", ", re.sub(r"\s+", " ", str(l.get("text", "")))).strip()
            if text:
                falas.append({"quem": who, "fala": text})
                if who not in ids:
                    ids.append(who)
        for base in ch.people[:2]:
            if base not in ids and len([i for i in ids if i in ch.people]) < 2:
                ids.insert(0, base)
        if falas:
            scenes.append({"cenario_en": s.get("background", "a colorful open place"), "personagens": ids[:3], "falas": falas})
    r["title"] = re.sub(r"\s*[—–]\s*", " - ", r["title"].strip())[:70]
    r["cenas"] = scenes
    return r


def write_script(ch, source, fmt, searches):
    fix = ""
    for attempt in range(4):
        r, provider = llm(ch, build_prompt(ch, source, fmt, searches, fix))
        problems = validate(ch, r, fmt, source["title"], source)
        if not problems:
            log.info("Script approved (%s, attempt %d).", provider, attempt + 1)
            return to_animation(ch, r)
        log.warning("Script rejected: %s", "; ".join(problems)[:400])
        fix = "\nYOUR PREVIOUS ATTEMPT WAS REJECTED. Fix this: " + "; ".join(problems)
    raise RuntimeError("Could not get an approved script in 4 attempts.")


# ════════════════════════════════════════════════════════════════════
# Subtitles (ASS karaoke, word by word)
# ════════════════════════════════════════════════════════════════════
def ass_time(s):
    h, rest = divmod(max(s, 0), 3600)
    m, s = divmod(rest, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def write_ass(ch, words, dest, hook):
    W, H = ch.video["resolution"]
    st = {"font": "Arial Black", "size": 82, "margin": 120, "words_per_block": 3,
          "highlight": "&H0000E1FF", **ch.cfg.get("subtitles", {})}
    blocks, cur = [], []
    for item in words:
        cur.append(item)
        if len(cur) >= st["words_per_block"] or re.search(r"[.!?,;:]$", item[2]):
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,{st['font']},104,{st['highlight']},{st['highlight']},&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,9,4,8,60,60,260,1
Style: Sub,{st['font']},{st['size']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,1,0,1,7,3,2,70,70,{st['margin']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def clean(t):
        return t.replace("{", "(").replace("}", ")").upper()

    out = []
    if hook.strip():
        out.append(r"Dialogue: 1,0:00:00.00,0:00:02.80,Hook,,0,0,0,,{\fad(0,250)\t(0,180,\fscx118\fscy118)"
                   r"\t(180,360,\fscx100\fscy100)}" + clean(hook.strip()))
    for bi, block in enumerate(blocks):
        end_block = block[-1][1] + 0.12
        if bi + 1 < len(blocks):
            end_block = min(max(end_block, block[-1][1]), blocks[bi + 1][0][0])
        for wi, (ini, fim, _) in enumerate(block):
            start = block[0][0] if wi == 0 else ini
            end = max(block[wi + 1][0] if wi + 1 < len(block) else end_block, start + 0.05)
            parts = [("{\\c" + st["highlight"] + "&\\fscx112\\fscy112}" + clean(w) + r"{\c&H00FFFFFF&\fscx100\fscy100}")
                     if wj == wi else clean(w) for wj, (_, _, w) in enumerate(block)]
            out.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Sub,,0,0,0,,{' '.join(parts)}")
    Path(dest).write_text(head + "\n".join(out) + "\n", encoding="utf-8-sig")


# ════════════════════════════════════════════════════════════════════
# Production + publishing
# ════════════════════════════════════════════════════════════════════
def voices(ch, folder):
    v = {cid: list(info["voice"]) for cid, info in ch.cfg["cast"].items()}
    v["NARRATOR"] = list(ch.cfg.get("narrator_voice", next(iter(v.values()))))
    fallback = ch.cfg.get("voice_fallbacks", {})
    for cid, (voice, rate, pitch) in list(v.items()):
        try:
            free_ai.locucao_edge("Hi.", folder / f"_t_{cid}.mp3", voice, rate, pitch)
        except Exception:
            if voice in fallback:
                v[cid][0] = fallback[voice]
                log.warning("Voice %s unavailable, using %s.", voice, fallback[voice])
        (folder / f"_t_{cid}.mp3").unlink(missing_ok=True)
    return v


def produce(ch, folder, script, rng):
    W, H = ch.video["resolution"]
    final = folder / "video_final.mp4"
    if final.exists() and final.stat().st_size > 200_000:
        return
    total, words = animation.gerar_audio_dialogo(script["cenas"], folder, ffmpeg_bin(), voices(ch, folder))
    log.info("Dialogue recorded: %d lines, %.1f s.", sum(len(c["falas"]) for c in script["cenas"]), total)
    write_ass(ch, words, folder / "legendas.ass", script.get("hook_text", ""))
    dur = animation.renderizar_cartoon(script["cenas"], total, folder, W, H, ch.video["fps"], ffmpeg_bin(), ch.dir, rng,
                                       cartao=None, usar_ia=True, estilo_cenario=ch.cfg.get("background_style"))
    log.info("Cartoon ready: %.1f s.", dur)


def description(ch, script, source):
    tags = " ".join(h if h.startswith("#") else "#" + h for h in script.get("hashtags", [])[:3])
    credit = ""
    if source.get("url"):
        credit = ch.cfg.get("source_credit", 'Facts source: Wikipedia, "{title}" ({url}), CC BY-SA 4.0.').format(**source)
    return "\n\n".join(x for x in [script.get("description", "").strip(), ch.cfg.get("description_footer", "").strip(),
                                    credit, f"{tags} #shorts"] if x)


def publish(ch, folder, script, source, private):
    from . import youtube
    marker = folder / "youtube.json"
    if marker.exists():
        return read_json(marker, {}).get("id")
    yt = dict(ch.cfg.get("youtube", {}))
    yt.setdefault("language", ch.lang)
    if private:
        yt["privacy"] = "private"
    title = script["title"].strip()
    if "#shorts" not in title.lower() and len(title) <= 90:
        title += " #shorts"
    vid = youtube.upload(ch.dir, folder / "video_final.mp4", title, description(ch, script, source),
                         script.get("tags", []), yt)
    write_json(marker, {"id": vid, "url": f"https://youtube.com/shorts/{vid}", "title": title})
    log.info("Published: https://youtube.com/shorts/%s", vid)
    return vid


def refresh_views(ch, hist):
    try:
        from . import youtube
        ids = [v["youtube_id"] for v in hist["videos"] if v.get("youtube_id")][-200:]
        stats = youtube.view_counts(ch.dir, ids)
        for v in hist["videos"]:
            if v.get("youtube_id") in stats:
                v["views"] = stats[v["youtube_id"]]
        top = sorted((v for v in hist["videos"] if v.get("views")), key=lambda v: -v["views"])[:5]
        if top:
            log.info("Top episodes: %s", ", ".join(f"{v['topic']} [{v.get('format')}] {v['views']}" for v in top))
    except Exception as e:
        log.warning("Could not read view counts: %s", str(e)[:150])


def run(slug, upload=True, private=False, force=False):
    ch = Channel(slug)
    setup_log()
    hist = read_json(ch.history_file, {"videos": []})
    today = dt.date.today().isoformat()
    done = [v for v in hist["videos"] if v["date"] == today]
    if len(done) >= ch.cfg.get("videos_per_day", 2) and not force:
        log.info("Daily quota already reached (%d videos).", len(done))
        return None
    n = 1
    while (ch.dir / "output" / f"{today}_{n}" / "youtube.json").exists() or \
            any(v.get("folder", "").endswith(f"{today}_{n}") for v in hist["videos"]):
        n += 1
    folder = ch.dir / "output" / f"{today}_{n}"
    folder.mkdir(parents=True, exist_ok=True)
    setup_log(folder)
    log.info("==== %s | %s | %s ====", ch.cfg["channel_name"], today, folder)
    if upload:
        refresh_views(ch, hist)
    rng = random.Random()
    state = read_json(folder / "state.json", {})
    if "source" not in state:
        skipped = set()
        for _ in range(6):
            topic, fmt = pick(ch, {"videos": hist["videos"] + [{"topic": t} for t in skipped]}, rng)
            try:
                if ch.cfg.get("topic_source", "wikipedia") == "wikipedia":
                    source = wikipedia(topic, ch.cfg.get("wikipedia_lang", ch.lang))
                else:
                    source = {"title": topic.replace("_", " "), "url": "", "text": ""}
                break
            except Exception as e:
                log.warning("Skipping %s: %s", topic, str(e)[:100])
                skipped.add(topic)
        else:
            raise RuntimeError("No usable topic (Wikipedia unreachable?)")
        state = {"topic": topic, "format": fmt, "source": source, "searches": youtube_searches(ch, source["title"])}
        write_json(folder / "state.json", state)
    log.info("Topic: %s | format: %s", state["source"]["title"], state["format"])
    script = read_json(folder / "script.json", None)
    if not script:
        script = write_script(ch, state["source"], state["format"], state["searches"])
        write_json(folder / "script.json", script)
    log.info("Title: %s", script["title"])
    produce(ch, folder, script, rng)
    vid = publish(ch, folder, script, state["source"], private) if upload else None
    hist["videos"].append({"date": today, "topic": state["topic"], "format": state["format"], "title": script["title"],
                           "folder": folder.relative_to(ch.dir).as_posix(), "youtube_id": vid})
    write_json(ch.history_file, hist)
    for junk in list(folder.glob("fala_*")) + [folder / "video_mudo.mp4"]:
        junk.unlink(missing_ok=True)
    log.info("==== Done: %s ====", folder / "video_final.mp4")
    return folder / "video_final.mp4"
