# -*- coding: utf-8 -*-
"""
Free providers:
  - Backgrounds: Pollinations.ai (Flux). A free key (enter.pollinations.ai) removes the watermark and the
    45 s rate limit; without a key it still works, slower, and the watermark strip is cropped.
  - Voices: edge-tts (Microsoft neural voices) with exact per-word timings for lip sync and subtitles.
Keys are read from environment variables or from the repo's secrets/ folder.
"""
import asyncio
import io
import logging
import os
import re
import time
import urllib.parse
from pathlib import Path

log = logging.getLogger("toonshorts")
REPO = Path(__file__).resolve().parent.parent


def secret(name, env=None):
    """Read secrets/<name> or an environment variable."""
    v = os.environ.get(env or "", "").strip() if env else ""
    arq = REPO / "secrets" / name
    if not v and arq.exists():
        v = arq.read_text(encoding="utf-8").strip()
    return v


_ULTIMA_CHAMADA = [0.0]


def chave_pollinations(raiz=None):
    return secret("pollinations_key.txt", "POLLINATIONS_API_KEY")


def gerar_cenario(prompt, destino, seed, largura=768, altura=1344, intervalo=16, tentativas=5):
    import requests
    from PIL import Image
    prompt = re.sub(r"\s+", " ", prompt).strip()[:1400]
    chave = chave_pollinations()
    headers = {"User-Agent": "toon-shorts-factory/1.0"}
    if chave:
        # com chave: endpoint novo, sem marca d'agua e sem a espera de 45 s
        url = "https://gen.pollinations.ai/image/" + urllib.parse.quote(prompt, safe="")
        headers["Authorization"] = f"Bearer {chave}"
        intervalo = 3
    else:
        url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt, safe="")
    params = {"width": largura, "height": altura, "model": "flux", "nologo": "true",
              "seed": seed, "enhance": "false", "private": "true"}
    ultimo = None
    for t in range(tentativas):
        espera = intervalo - (time.time() - _ULTIMA_CHAMADA[0])
        if espera > 0:
            time.sleep(espera)
        _ULTIMA_CHAMADA[0] = time.time()
        try:
            r = requests.get(url, params=params, timeout=180, headers=headers)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                im = Image.open(io.BytesIO(r.content)).convert("RGB")
                # corta o rodape onde o servico gratuito coloca a marca d'agua (sem chave)
                corte = 0 if chave else int(im.height * 0.075)
                im = im.crop((0, 0, im.width, im.height - corte))
                im.save(destino)
                return destino
            ultimo = f"HTTP {r.status_code}: {r.text[:200]}"
        except Exception as e:
            ultimo = str(e)[:200]
        log.warning("Pollinations failed (attempt %d): %s", t + 1, ultimo)
        time.sleep(30 if "FREE_LIMIT" in str(ultimo) else 20 * (t + 1))
        params["seed"] = seed + t + 1
    raise RuntimeError(f"Pollinations unavailable: {ultimo}")


def locucao_edge(texto, destino_mp3, voz="en-US-AndrewNeural", velocidade="+6%", tom="+0Hz"):
    import edge_tts
    palavras = []

    async def _run():
        try:
            com = edge_tts.Communicate(texto, voz, rate=velocidade, pitch=tom, boundary="WordBoundary")
        except TypeError:
            com = edge_tts.Communicate(texto, voz, rate=velocidade, pitch=tom)
        with open(destino_mp3, "wb") as f:
            async for chunk in com.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    ini = chunk["offset"] / 1e7
                    fim = ini + chunk["duration"] / 1e7
                    palavras.append((ini, fim, chunk["text"]))

    for tentativa in range(4):
        palavras.clear()
        try:
            asyncio.run(_run())
            return palavras
        except Exception as e:  # o servico as vezes devolve "No audio was received" sem motivo
            if tentativa == 3:
                raise
            log.warning("edge-tts failed (%s), retrying...", str(e)[:80])
            time.sleep(3 * (tentativa + 1))


def alinhar_pontuacao(palavras, texto):
    """edge-tts devolve palavras sem pontuacao; devolve a pontuacao do texto original para as legendas."""
    tokens = texto.split()
    saida, j = [], 0
    for ini, fim, w in palavras:
        limpa = re.sub(r"\W", "", w.lower())
        rotulo = w
        for k in range(j, min(j + 4, len(tokens))):
            if re.sub(r"\W", "", tokens[k].lower()).startswith(limpa[:4]) and limpa:
                rotulo = tokens[k]
                j = k + 1
                break
        saida.append((ini, fim, rotulo))
    return saida
