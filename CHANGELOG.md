# Changelog

## 1.0.1 (2026-11-24)
* Fix: on Windows, ffmpeg 9 hung forever in the final pass when audio filters ran next to the `ass` subtitle filter. Gain and limiter now run in Python (`tratar_audio`), the final command only pads audio, and each attempt has a timeout with a fallback variant.
* Correção: no Windows, o ffmpeg 9 travava no passo final quando filtros de áudio rodavam junto com a legenda `ass`. Ganho e limitador agora rodam em Python, o comando final só completa o áudio com silêncio e cada tentativa tem tempo limite com variante de reserva.

## 1.0.0 (2026-11-22)
* First public release, extracted from two production channels (Turma da Aventura, World Tour Toons).
* Niche-agnostic `channel.json`, code-drawn cast, Wikipedia fact check, rotating formats.
* Two-pass Windows-safe render, edge-tts retries, `authorize --paste`.
* Claude skill `toon-shorts-channel`.
