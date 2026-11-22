# secrets/ (never committed)

| File | What | Required |
|---|---|---|
| `client_secret.json` | OAuth client (Desktop app) from Google Cloud, see `docs/youtube-setup.md` | yes, to upload |
| `pollinations_key.txt` | Free key from https://enter.pollinations.ai (no watermark, no 45 s wait) | recommended |
| `deepseek_key.txt` | Optional paid fallback for script writing | no |

Environment variables also work: `POLLINATIONS_API_KEY`, `DEEPSEEK_API_KEY`.
Each channel keeps its own YouTube token in `channels/<slug>/.secrets/youtube_token.json`.
