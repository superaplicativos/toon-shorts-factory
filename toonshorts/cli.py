# -*- coding: utf-8 -*-
"""
toon-shorts-factory command line.

  python -m toonshorts list
  python -m toonshorts new <slug> [--from world-tour-toons]
  python -m toonshorts cast <slug>                 renders channels/<slug>/cast_preview.png
  python -m toonshorts check <slug>                checks tools, keys and YouTube authorization
  python -m toonshorts authorize <slug> [--paste]  connects the YouTube channel (once)
  python -m toonshorts preview <slug>              makes one video WITHOUT uploading
  python -m toonshorts pilot <slug>                makes one video and uploads it as PRIVATE
  python -m toonshorts run <slug>                  daily job: makes and publishes (respects videos_per_day)
  python -m toonshorts schedule <slug>             creates the daily tasks (Windows) or prints crontab lines
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import pipeline
from .free_ai import REPO, secret


def _channels():
    return sorted(p.parent.name for p in (REPO / "channels").glob("*/channel.json"))


def cmd_list(_):
    for c in _channels():
        cfg = pipeline.read_json(REPO / "channels" / c / "channel.json", {})
        print(f"{c:28} {cfg.get('channel_name', '')}  [{cfg.get('language', '')}]  {cfg.get('niche', '')[:60]}")


def cmd_new(args):
    slug = args[0]
    base = args[args.index("--from") + 1] if "--from" in args else "_template"
    src, dst = REPO / "channels" / base, REPO / "channels" / slug
    if dst.exists():
        raise SystemExit(f"{dst} already exists")
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("output", ".secrets", ".cache", "history.json", "*.png"))
    print(f"Created {dst}. Edit channel.json and topics.json (or ask Claude with the skill to do it for you).")


def cmd_cast(args):
    from PIL import Image, ImageDraw
    ch = pipeline.Channel(args[0])
    from . import characters
    sprites = []
    for cid in ch.cfg["cast"]:
        sprites.append((cid, characters.desenhar(cid, False, False, 0, 0)))
        sprites.append((cid, characters.desenhar(cid, True, False, 1, 1)))
    W = sum(s.width for _, s in sprites) + 20 * len(sprites)
    H = max(s.height for _, s in sprites) + 70
    im = Image.new("RGBA", (W, H), (205, 230, 250, 255))
    d = ImageDraw.Draw(im)
    x = 10
    for cid, s in sprites:
        im.alpha_composite(s, (x, H - 60 - s.height))
        d.text((x + s.width // 2 - 20, H - 45), cid, fill=(20, 20, 20))
        x += s.width + 20
    out = ch.dir / "cast_preview.png"
    im.convert("RGB").save(out)
    print("Saved", out)


def cmd_check(args):
    ok = True
    for mod in ("edge_tts", "PIL", "requests", "googleapiclient", "google_auth_oauthlib"):
        try:
            __import__(mod)
        except Exception:
            print("MISSING python package:", mod, "(run setup again)")
            ok = False
    ff = pipeline.ffmpeg_bin()
    if not (Path(ff).exists() or shutil.which(ff)):
        print("MISSING ffmpeg")
        ok = False
    print("Pollinations key:", "yes" if secret("pollinations_key.txt", "POLLINATIONS_API_KEY") else
          "no (works, but slower and with a 45 s wait per image; get a free key at enter.pollinations.ai)")
    if not (REPO / "secrets" / "client_secret.json").exists():
        print("MISSING secrets/client_secret.json (see docs/youtube-setup.md)")
        ok = False
    if args:
        try:
            from . import youtube
            t = youtube.service(REPO / "channels" / args[0]).channels().list(part="snippet", mine=True).execute()
            print("YouTube channel connected:", t["items"][0]["snippet"]["title"])
        except Exception as e:
            print("YouTube not connected yet:", str(e)[:150])
            ok = False
    print("All good." if ok else "Fix the items above.")
    return ok


def cmd_authorize(args):
    from . import youtube
    name = youtube.authorize(REPO / "channels" / args[0], paste="--paste" in args)
    print(f"\nOK! Connected to channel: {name}")


def cmd_run(args, upload=True, private=False, force=False):
    pipeline.run(args[0], upload=upload, private=private or "--private" in args, force=force or "--force" in args)


def cmd_schedule(args):
    slug = args[0]
    cfg = pipeline.read_json(REPO / "channels" / slug / "channel.json", {})
    times = cfg.get("schedule", ["14:10", "20:10"])
    py = Path(sys.executable)
    if os.name == "nt":
        bat = REPO / f"run_{slug}.bat"
        bat.write_text(f'@echo off\r\ncd /d "{REPO}"\r\nset PYTHONUTF8=1\r\n"{py}" -m toonshorts run {slug}\r\n', encoding="ascii")
        for i, t in enumerate(times, 1):
            subprocess.run(["schtasks", "/Create", "/F", "/SC", "DAILY", "/ST", t, "/TN", f"ToonShorts_{slug}_{i}",
                            "/TR", f'"{bat}"'], check=False)
        print(f"Daily tasks created at {', '.join(times)} (local time). The PC must be on at those times.")
    else:
        print("Add these lines with `crontab -e`:")
        for t in times:
            h, m = t.split(":")
            print(f"{int(m)} {int(h)} * * * cd {REPO} && {py} -m toonshorts run {slug} >> {REPO}/channels/{slug}/cron.log 2>&1")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("PYTHONUTF8", "1")
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd, args = argv[0], argv[1:]
    needs_slug = {"cast", "authorize", "preview", "pilot", "run", "schedule", "new"}
    if cmd in needs_slug and not args:
        raise SystemExit(f"Usage: python -m toonshorts {cmd} <channel-slug>. Channels: {', '.join(_channels())}")
    table = {
        "list": cmd_list, "new": cmd_new, "cast": cmd_cast, "check": cmd_check, "authorize": cmd_authorize,
        "schedule": cmd_schedule,
        "preview": lambda a: cmd_run(a, upload=False, force=True),
        "pilot": lambda a: cmd_run(a, private=True, force=True),
        "run": cmd_run,
    }
    if cmd not in table:
        raise SystemExit(__doc__)
    try:
        r = table[cmd](args)
        if cmd == "check" and r is False:
            sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception:
        pipeline.log.exception("Failed")
        sys.exit(1)
