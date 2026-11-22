# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Render stuck at "Animating... 0%" or after "Adding voices and subtitles" on Windows | ffmpeg one-pass pipe or `loudnorm` hang on some Windows builds | Already fixed (two-pass render, `-nostdin`, `volume+alimiter`). If you edit `animation.py`, keep that design. |
| `No audio was received` from edge-tts | transient service error | retried automatically 4 times; if a voice keeps failing, set `voice_fallbacks` |
| `Script rejected: ... not word-for-word from the source` | the LLM paraphrased its citations | normal, it retries up to 4 times; if it keeps failing, that topic's article is too thin, remove it |
| `Wikipedia without enough text` | short article | the run skips to another topic; clean `topics.json` |
| `403 access_denied` on Google | app in Testing mode, wrong account, or brand account blocked | publish the app to Production, choose the right channel |
| Consent finished but terminal still waiting | browser could not open localhost | `toonshorts authorize <slug> --paste` |
| Uploads appear private | unverified API project | see docs/youtube-setup.md |
| `quotaExceeded` | more than ~6 uploads/day on one Google project | use a second project or request more quota |
| Backgrounds look plain / sky only | Pollinations failed, code-drawn fallback used | add the free Pollinations key; check the run log |
| Selecting text in the Windows console pauses the run | QuickEdit mode | press Esc in the window |
| Files in `output/` | every episode keeps `run.log`, `state.json`, `script.json`, `legendas.ass`, `narracao.wav`, `video_final.mp4` | delete old folders whenever you want |
