# -*- coding: utf-8 -*-
"""
Cartoon engine (paper-cutout style).
- One voice per character (edge-tts, free) with word timings
- Lip sync from the word timings
- The speaker bounces and gestures; the others blink and look at the speaker
- Backgrounds from Pollinations (free) with a code-drawn fallback, cached by description
- Two-pass ffmpeg render (frames -> silent video, then subtitles + audio). The one-pass version
  and the loudnorm filter hang on some Windows ffmpeg builds, so they are avoided on purpose.
"""
import hashlib
import json
import logging
import math
import random
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from . import characters as pc
from . import free_ai as gerador_gratis

log = logging.getLogger("toonshorts")

VOZES_PADRAO = {"NARRATOR": ["en-US-AndrewNeural", "+4%", "+0Hz"]}
FALANTES_SEM_BOCA = {"NARRATOR"}
ESTILO_CENARIO = ("flat paper cutout cartoon background, construction paper animation look, simple bold shapes, "
                  "bright flat colors, subtle paper texture, TV cartoon, wide empty ground in the lower third, "
                  "no characters, no people, no animals, no text, no letters, vertical composition")


# ════════════════════════════════════════════════════════════════════
# Audio do dialogo
# ════════════════════════════════════════════════════════════════════
def _ler_wav(p):
    with wave.open(str(p), "rb") as w:
        return w.readframes(w.getnframes()), w.getframerate()


def gerar_audio_dialogo(cenas, pasta, ffmpeg, vozes=None, pausa=0.22):
    """Gera um wav por fala, junta tudo e devolve a linha do tempo com palavras em tempo global."""
    vozes = {**VOZES_PADRAO, **(vozes or {})}
    taxa = 24000
    pcm_total = bytearray()
    t = 0.25
    pcm_total += b"\x00\x00" * int(taxa * 0.25)
    palavras_globais = []
    for ci, cena in enumerate(cenas):
        cena["inicio"] = t
        for fi, fala in enumerate(cena["falas"]):
            quem = fala["quem"] if fala["quem"] in vozes else "NARRATOR"
            voz, vel, tom = vozes[quem]
            mp3 = pasta / f"fala_{ci:02d}_{fi:02d}.mp3"
            wav = mp3.with_suffix(".wav")
            if not wav.exists():
                pal = gerador_gratis.locucao_edge(fala["fala"], mp3, voz, vel, tom)
                subprocess.run([ffmpeg, "-y", "-v", "error", "-nostdin", "-i", str(mp3), "-ar", str(taxa), "-ac", "1", str(wav)], check=True)
                mp3.unlink(missing_ok=True)
                (wav.with_suffix(".json")).write_text(json.dumps(pal), encoding="utf-8")
            pal = json.loads(wav.with_suffix(".json").read_text(encoding="utf-8"))
            pcm, _ = _ler_wav(wav)
            dur = len(pcm) / 2 / taxa
            fala["inicio"], fala["fim"] = t, t + dur
            fala["palavras"] = [[t + a, t + b, w] for a, b, w in gerador_gratis.alinhar_pontuacao(pal, fala["fala"])]
            palavras_globais += [tuple(x) for x in fala["palavras"]]
            pcm_total += pcm + b"\x00\x00" * int(taxa * pausa)
            t += dur + pausa
        cena["fim"] = t
    destino = pasta / "narracao.wav"
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        w.writeframes(bytes(pcm_total))
    return t, palavras_globais


# ════════════════════════════════════════════════════════════════════
# Cenarios
# ════════════════════════════════════════════════════════════════════


def cenario_desenhado(destino, W, H, seed):
    """Fallback sem internet: ceu, sol, nuvens e chao em recorte."""
    rng = random.Random(seed)
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    topo = rng.choice([(110, 180, 245), (250, 170, 110), (120, 110, 200), (90, 200, 230)])
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(c * (1 - k * 0.35) + 255 * k * 0.25) for c in topo))
    d.ellipse([W * 0.65, H * 0.08, W * 0.65 + 220, H * 0.08 + 220], fill=(255, 220, 80), outline=(30, 20, 20), width=6)
    for _ in range(4):
        x, y = rng.randint(-100, W), rng.randint(int(H * 0.05), int(H * 0.35))
        for k in range(3):
            d.ellipse([x + k * 70, y - k % 2 * 30, x + k * 70 + 160, y + 90 - k % 2 * 30], fill=(255, 255, 255),
                      outline=(30, 20, 20), width=5)
    cor_morro = rng.choice([(90, 170, 80), (200, 170, 110), (120, 150, 90)])
    d.polygon([(0, H * 0.62), (W * 0.35, H * 0.52), (W * 0.7, H * 0.6), (W, H * 0.5), (W, H), (0, H)],
              fill=tuple(max(0, c - 30) for c in cor_morro), outline=(30, 20, 20))
    d.polygon([(0, H * 0.72), (W, H * 0.68), (W, H), (0, H)], fill=cor_morro, outline=(30, 20, 20))
    im.save(destino)
    return destino


def preparar_cenario(cena, pasta, W, H, raiz, rng, usar_ia=True, estilo=None):
    desc = cena.get("cenario_en", "a colorful open place")
    chave = hashlib.md5(desc.encode("utf-8")).hexdigest()[:12]
    cache = raiz / ".cache" / "backgrounds"
    cache.mkdir(parents=True, exist_ok=True)
    bruto = cache / f"{chave}.jpg"
    if not bruto.exists():
        ok = False
        if usar_ia:
            try:
                gerador_gratis.gerar_cenario(f"{estilo or ESTILO_CENARIO}. Setting: {desc}", bruto, seed=rng.randint(1, 10**9),
                                             largura=768, altura=1344, tentativas=3)
                ok = True
            except Exception as e:
                log.warning("AI background failed (%s); using a code-drawn one.", str(e)[:120])
        if not ok:
            cenario_desenhado(bruto, W, H, rng.randint(1, 10**9))
    im = Image.open(bruto).convert("RGB")
    esc = max(W * 1.08 / im.width, H * 1.08 / im.height)
    im = im.resize((int(im.width * esc), int(im.height * esc)), Image.LANCZOS)
    return im


# ════════════════════════════════════════════════════════════════════
# Render quadro a quadro
# ════════════════════════════════════════════════════════════════════
def _layout(ids, W, linha_chao):
    pet = next((p for p in ids if p in pc.PETS), None)
    humanos = [p for p in ids if p not in pc.PETS][:3]
    sprites = {p: pc.desenhar(p) for p in humanos}
    larg = {p: sprites[p].width - 150 for p in humanos}
    total = sum(larg.values()) * 0.98 if humanos else 0
    reserva = 250 if pet == "KIKO" else 0  # papagaio ganha um espaco proprio ao lado
    escala = min(1.45, (W * 0.97 - reserva) / total) if total else 1.0
    pos = {}
    x = (W - reserva - total * escala) / 2
    for p in humanos:
        w = larg[p] * escala
        pos[p] = (x + w / 2, linha_chao, escala)
        x += w * 0.98
    if pet == "KIKO":
        pos[pet] = (W - 140, linha_chao + 10, 1.0)
    elif pet:
        lado = W * (0.18 if len(humanos) % 2 else 0.80)
        pos[pet] = (lado, linha_chao + (90 if pet == "JIMMY" else 40), min(escala, 1.2))
    return pos


def renderizar_cartoon(cenas, total_audio, pasta, W, H, fps, ffmpeg, raiz, rng, cartao=None, cartao_seg=3.5,
                       usar_ia=True, ass="legendas.ass", estilo_cenario=None):
    linha_chao = int(H * 0.80)
    bgs = [preparar_cenario(c, pasta, W, H, raiz, rng, usar_ia, estilo_cenario) for c in cenas]
    total = total_audio + 0.4
    n_frames = int(total * fps)
    extra = int(cartao_seg * fps) if cartao else 0
    dur_total = (n_frames + extra) / fps
    # Passo 1: so os quadros (pipe simples, comprovado no Windows). Passo 2: legendas + audio.
    cmd = [ffmpeg, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "video_mudo.mp4"]
    err1 = open(pasta / "ffmpeg_passo1.txt", "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=err1, cwd=str(pasta))
    piscadas = {}
    layouts = [_layout(c["personagens"], W, linha_chao) for c in cenas]
    cache_spr = {}

    def sprite(pid, boca, pisc, olhar, braco, esc):
        k = (pid, boca, pisc, olhar, braco, esc)
        if k not in cache_spr:
            spr = pc.desenhar(pid, boca, pisc, olhar, braco)
            if esc != 1.0:
                spr = spr.resize((max(1, int(spr.width * esc)), max(1, int(spr.height * esc))), Image.BILINEAR)
            cache_spr[k] = spr
        return cache_spr[k]

    sombras = []
    for pos_c in layouts:
        som = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sdr = ImageDraw.Draw(som)
        for pid, (cx, chao, esc) in pos_c.items():
            larg = sprite(pid, False, False, 0, 0, esc).width
            sdr.ellipse([cx - larg * 0.22, chao - 12, cx + larg * 0.22, chao + 12], fill=(0, 0, 0, 90))
        sombras.append(som.filter(ImageFilter.GaussianBlur(6)))
    for f in range(n_frames):
        t = f / fps
        ci = next((i for i, c in enumerate(cenas) if c["inicio"] - 0.12 <= t < c["fim"]), len(cenas) - 1)
        cena = cenas[ci]
        bg = bgs[ci]
        prog = (t - cena["inicio"]) / max(cena["fim"] - cena["inicio"], 0.1)
        dx = int((bg.width - W) * (0.5 + 0.5 * math.sin(prog * 1.2)) * 0.9)
        dy = int((bg.height - H) * 0.5)
        quadro = bg.crop((dx, dy, dx + W, dy + H)).convert("RGBA")
        fala = next((fl for fl in cena["falas"] if fl["inicio"] <= t < fl["fim"] + 0.05), None)
        falante = fala["quem"] if fala else None
        boca = False
        if fala and falante not in FALANTES_SEM_BOCA:
            ativa = any(a <= t < b for a, b, _ in fala["palavras"])
            boca = ativa and int(t * 11) % 2 == 0
        pos = layouts[ci]
        ordem = sorted(pos.items(), key=lambda kv: (kv[0] == falante, kv[0] in pc.PETS))
        desenhos = []
        for pid, (cx, chao, esc) in ordem:
            prox = piscadas.setdefault(pid, rng.uniform(1.0, 4.0))
            piscando = prox <= t < prox + 0.12
            if t >= prox + 0.12:
                piscadas[pid] = t + rng.uniform(2.5, 4.5)
            fala_eu = pid == falante
            olhar = 0
            if falante and not fala_eu and falante in pos:
                olhar = 1 if pos[falante][0] > cx else -1
            braco = 1 if (fala_eu and pid not in pc.PETS and int(t * 1.5) % 2 == 0) else 0
            spr = sprite(pid, boca if fala_eu else False, piscando, olhar, braco, esc)
            pulo = int(abs(math.sin(t * 9)) * 14) if fala_eu else int(math.sin(t * 2 + cx) * 3)
            desenhos.append((spr, max(0, min(W - spr.width, int(cx - spr.width / 2))), max(0, int(chao - spr.height - pulo))))
        quadro.alpha_composite(sombras[ci])
        for spr, x, y in desenhos:
            quadro.alpha_composite(spr, (x, y))
        proc.stdin.write(quadro.convert("RGB").tobytes())
        if f % (fps * 5) == 0:
            log.info("Animating... %d%%", int(100 * f / max(n_frames, 1)))
    if cartao:
        card = Image.open(cartao).convert("RGB").resize((W, H))
        dados = card.tobytes()
        for _ in range(extra):
            proc.stdin.write(dados)
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed in pass 1 (see ffmpeg_passo1.txt)")
    log.info("Animating... 100%. Adding voices and subtitles.")
    cmd2 = [ffmpeg, "-y", "-v", "error", "-nostdin", "-i", "video_mudo.mp4", "-i", "narracao.wav",
            "-vf", f"ass={ass},format=yuv420p",
            "-af", f"apad=whole_dur={dur_total:.2f},volume=4dB,alimiter=limit=0.9:level=disabled,aresample=48000",
            "-t", f"{dur_total:.2f}", "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "video_final.mp4"]
    with open(pasta / "ffmpeg_passo2.txt", "w", encoding="utf-8") as err2:
        r = subprocess.run(cmd2, stdin=subprocess.DEVNULL, stderr=err2, cwd=str(pasta))
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed in pass 2 (see ffmpeg_passo2.txt)")
    return dur_total
