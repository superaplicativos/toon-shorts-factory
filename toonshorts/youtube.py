# -*- coding: utf-8 -*-
"""YouTube Data API v3: OAuth per channel + resumable Shorts upload + view counts."""
import os
import time
from pathlib import Path

from .free_ai import REPO

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]


def _paths(channel_dir):
    token = Path(channel_dir) / ".secrets" / "youtube_token.json"
    client = Path(channel_dir) / ".secrets" / "client_secret.json"
    if not client.exists():
        client = REPO / "secrets" / "client_secret.json"  # one Google Cloud app can serve many channels
    return token, client


def credentials(channel_dir):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    token, _ = _paths(channel_dir)
    if not token.exists():
        raise RuntimeError(f"Channel not authorized yet. Run: python -m toonshorts authorize {Path(channel_dir).name}")
    cred = Credentials.from_authorized_user_file(str(token), SCOPES)
    if cred.expired and cred.refresh_token:
        cred.refresh(Request())
        token.write_text(cred.to_json(), encoding="utf-8")
    return cred


def authorize(channel_dir, port=8765, paste=False):
    """Opens Google's consent screen. Pick the BRAND ACCOUNT of the channel you want to post to.

    paste=True is for when the browser cannot reach localhost (remote PCs, some embedded browsers):
    copy the full address of the page that fails to load (http://localhost:...?code=...) and paste it here.
    """
    from google_auth_oauthlib.flow import InstalledAppFlow
    token, client = _paths(channel_dir)
    if not client.exists():
        raise RuntimeError(f"Missing OAuth client file. Put it at {client} (see docs/youtube-setup.md)")
    flow = InstalledAppFlow.from_client_secrets_file(str(client), SCOPES)
    if paste:
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")  # the redirect is http://localhost
        flow.redirect_uri = f"http://localhost:{port}/"
        url, _ = flow.authorization_url(prompt="consent", access_type="offline")
        print("\n1) Open this link, choose the channel and allow access:\n\n" + url)
        print("\n2) The browser will end on a page that does not load (localhost). Copy its FULL address.")
        resposta = input("\nPaste the address here: ").strip()
        flow.fetch_token(authorization_response=resposta)
        cred = flow.credentials
    else:
        cred = flow.run_local_server(port=port, prompt="consent", access_type="offline")
    token.parent.mkdir(parents=True, exist_ok=True)
    token.write_text(cred.to_json(), encoding="utf-8")
    yt = service(channel_dir)
    itens = yt.channels().list(part="snippet", mine=True).execute().get("items", [])
    return itens[0]["snippet"]["title"] if itens else None


def service(channel_dir):
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=credentials(channel_dir), cache_discovery=False)


def _limit_tags(tags, limit=480):
    out, total = [], 0
    for t in tags:
        t = str(t).replace("#", "").replace("<", "").replace(">", "").strip()
        if not t or t in out:
            continue
        cost = len(t) + (2 if " " in t else 0) + 1
        if total + cost > limit:
            break
        out.append(t)
        total += cost
    return out


def upload(channel_dir, video, title, description, tags, cfg):
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    yt = service(channel_dir)
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "tags": _limit_tags(list(tags) + cfg.get("fixed_tags", [])),
            "categoryId": str(cfg.get("category_id", "24")),
            "defaultLanguage": cfg.get("language", "en"),
            "defaultAudioLanguage": cfg.get("language", "en"),
        },
        "status": {
            "privacyStatus": cfg.get("privacy", "public"),
            "selfDeclaredMadeForKids": bool(cfg.get("made_for_kids", False)),
            "containsSyntheticMedia": bool(cfg.get("synthetic_media", False)),
            "embeddable": True,
        },
    }
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media,
                             notifySubscribers=bool(cfg.get("notify_subscribers", True)))
    resp, tries = None, 0
    while resp is None:
        try:
            _, resp = req.next_chunk()
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and tries < 6:
                tries += 1
                time.sleep(2 ** tries)
                continue
            raise
        except (ConnectionError, TimeoutError, OSError):
            if tries < 6:
                tries += 1
                time.sleep(2 ** tries)
                continue
            raise
    return resp["id"]


def view_counts(channel_dir, ids):
    if not ids:
        return {}
    yt = service(channel_dir)
    out = {}
    for i in range(0, len(ids), 50):
        res = yt.videos().list(part="statistics", id=",".join(ids[i:i + 50])).execute()
        out.update({v["id"]: int(v["statistics"].get("viewCount", 0)) for v in res.get("items", [])})
    return out
