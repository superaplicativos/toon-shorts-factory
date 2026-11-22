# -*- coding: utf-8 -*-
"""
Paper-cutout cartoon characters drawn 100% in code (Pillow), South-Park-like flat style.

Each character is defined in the channel config (channel.json -> "cast" -> "look") and supports:
mouth open/closed (lip sync), blinking, gaze direction and a raised arm while talking.
No external images, so there is nothing to license and every channel gets its own original cast.
"""
from functools import lru_cache

from PIL import Image, ImageDraw

SS = 2  # supersampling for smooth edges
PRETO = (25, 20, 20)
PELE_PADRAO = (255, 218, 185)
PELE = PELE_PADRAO
BRANCO = (255, 255, 255)
CONTORNO = 5

PERFIS = {}
PETS = set()

HAIR_STYLES = {"short": "curto", "buns": "coques", "messy": "bagunçado", "side_ponytail": "rabo_lateral",
               "cap": "bone", "afro": "afro", "bowl": "cogumelo", "wild": "maluco", "bald": "careca"}
PROPS = {"phone": "celular", "belt": "cinto", "backpack": "mochila", "notepad": "bloco", "plush": "pelucia",
         "camera": "camera", "map": "mapa", "none": "nenhum"}


def _cor(v, padrao=None):
    if v is None:
        return padrao
    if isinstance(v, str):
        v = v.lstrip("#")
        return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(v)


def register_cast(cast):
    """Load the cast from channel.json. Keys are character IDs (UPPERCASE)."""
    PERFIS.clear()
    PETS.clear()
    desenhar.cache_clear()
    for cid, info in cast.items():
        look = info.get("look", {})
        if look.get("pet"):
            PERFIS[cid] = {"pet": look["pet"]}
            PETS.add(cid)
            continue
        PERFIS[cid] = {
            "altura": int(look.get("height", 600)),
            "camisa": _cor(look.get("shirt"), (220, 80, 60)),
            "calca": _cor(look.get("pants"), None) if "pants" in look else (60, 80, 120),
            "sapato": _cor(look.get("shoes"), (240, 240, 240)),
            "cabelo": _cor(look.get("hair_color"), (60, 40, 25)),
            "estilo_cabelo": HAIR_STYLES.get(look.get("hair_style", "short"), "curto"),
            "prop": PROPS.get(look.get("prop", "none"), "nenhum"),
            "pele": _cor(look.get("skin"), PELE_PADRAO),
            "cor_bone": _cor(look.get("cap_color"), (30, 110, 200)),
            "short": bool(look.get("shorts")), "vestido": bool(look.get("dress")),
            "jaleco": bool(look.get("lab_coat")), "brincos": bool(look.get("earrings")),
            "oculos": bool(look.get("glasses")), "goggles": bool(look.get("goggles")),
            "blush": bool(look.get("blush")), "adult": bool(look.get("adult")),
            "print": look.get("shirt_print"), "luvas": _cor(look.get("gloves"), None),
        }


@lru_cache(maxsize=512)
def desenhar(pid, boca_aberta=False, piscando=False, olhar=0, braco=0):
    """RGBA sprite, feet at the bottom. olhar: -1 left, 0 front, 1 right. braco: 1 = raised arm."""
    return _desenhar(pid, boca_aberta, piscando, olhar, braco)


def _e(d, box, fill, w=CONTORNO):
    d.ellipse([c * SS for c in box], fill=fill, outline=PRETO, width=w * SS)


def _r(d, box, fill, raio=18, w=CONTORNO):
    d.rounded_rectangle([c * SS for c in box], radius=raio * SS, fill=fill, outline=PRETO, width=w * SS)


def _p(d, pts, fill, w=CONTORNO):
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill, outline=PRETO, width=w * SS)


def _l(d, pts, cor=PRETO, w=CONTORNO):
    d.line([(x * SS, y * SS) for x, y in pts], fill=cor, width=w * SS, joint="curve")


def _desenhar(pid, boca_aberta=False, piscando=False, olhar=0, braco=0):
    """Retorna RGBA com os pes na base e centralizado. olhar: -1 esquerda, 0 frente, 1 direita.
    braco: 0 parado, 1 levantado (gesto ao falar)."""
    p = PERFIS[pid]
    if p.get("pet") == "dog":
        return _desenhar_jimmy(boca_aberta, piscando)
    if p.get("pet") == "parrot":
        return _desenhar_kiko(boca_aberta, piscando)
    PELE = p.get("pele", PELE_PADRAO)
    H = p["altura"]
    W = int(H * 0.78) + 160
    im = Image.new("RGBA", (W * SS, (H + 40) * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = W / 2
    cab_r = H * (0.21 if p.get("adult") else 0.30)
    cab_cy = cab_r + 30
    corpo_top = cab_cy + cab_r * 0.80
    pe_y = H + 20
    corpo_h = (pe_y - corpo_top) * 0.62
    corpo_w = cab_r * 1.55

    # pernas e sapatos
    perna_top = corpo_top + corpo_h - 10
    for sx in (-1, 1):
        x = cx + sx * corpo_w * 0.22
        cor_perna = p["calca"] if p["calca"] else PELE
        if p.get("short") or p.get("vestido"):
            _r(d, (x - 22, perna_top - 5, x + 22, pe_y - 18), PELE, 8, 4)
            if p.get("short"):
                _r(d, (x - 30, perna_top - 10, x + 30, perna_top + 45), p["calca"], 8, 4)
        else:
            _r(d, (x - 28, perna_top - 5, x + 28, pe_y - 18), cor_perna, 8, 4)
        _e(d, (x - 42 + sx * 6, pe_y - 36, x + 42 + sx * 6, pe_y + 4), p["sapato"], 4)

    # backpack (behind the body)
    if p["prop"] == "mochila":
        _r(d, (cx - corpo_w * 0.62, corpo_top + 8, cx + corpo_w * 0.62, corpo_top + corpo_h * 0.85), (95, 120, 60), 22)

    # corpo / camisa / vestido / jaleco
    if p.get("vestido"):
        _p(d, [(cx - corpo_w * 0.42, corpo_top), (cx + corpo_w * 0.42, corpo_top),
               (cx + corpo_w * 0.62, corpo_top + corpo_h + 20), (cx - corpo_w * 0.62, corpo_top + corpo_h + 20)],
           p["camisa"])
        for k in range(5):  # dress pattern
            lx = cx - corpo_w * 0.35 + k * corpo_w * 0.17
            ly = corpo_top + corpo_h * (0.45 + 0.25 * (k % 2))
            d.ellipse([(lx - 8) * SS, (ly - 8) * SS, (lx + 8) * SS, (ly + 8) * SS], outline=(150, 110, 20), width=3 * SS)
            _l(d, [(lx + 6, ly + 6), (lx + 14, ly + 14)], (150, 110, 20), 3)
    else:
        _r(d, (cx - corpo_w / 2, corpo_top, cx + corpo_w / 2, corpo_top + corpo_h), p["camisa"], 30)
        if p.get("jaleco"):
            _p(d, [(cx - corpo_w / 2 - 10, corpo_top), (cx - 10, corpo_top), (cx - 25, corpo_top + corpo_h + 60),
                   (cx - corpo_w / 2 - 20, corpo_top + corpo_h + 60)], (235, 235, 228))
            _p(d, [(cx + corpo_w / 2 + 10, corpo_top), (cx + 10, corpo_top), (cx + 25, corpo_top + corpo_h + 60),
                   (cx + corpo_w / 2 + 20, corpo_top + corpo_h + 60)], (235, 235, 228))
            for k in range(3):
                d.ellipse([(cx - 60 + k * 12) * SS, (corpo_top + 90 + k * 40) * SS,
                           (cx - 46 + k * 12) * SS, (corpo_top + 104 + k * 40) * SS], fill=(150, 200, 90))
        if p.get("print") == "circuit":
            for k in range(4):
                y = corpo_top + 40 + k * 28
                _l(d, [(cx - 40, y), (cx - 10, y), (cx - 10, y + 14), (cx + 30, y + 14)], (90, 160, 230), 3)
        if p.get("print") == "dino":
            _e(d, (cx - 35, corpo_top + 50, cx + 35, corpo_top + 95), (60, 170, 80), 3)
            _e(d, (cx + 18, corpo_top + 35, cx + 48, corpo_top + 62), (60, 170, 80), 3)
        if p.get("print") == "tech":
            for k, (dx, dy) in enumerate([(-35, 50), (20, 60), (-10, 100)]):
                d.rectangle([(cx + dx) * SS, (corpo_top + dy) * SS, (cx + dx + 18) * SS, (corpo_top + dy + 18) * SS],
                            outline=(220, 190, 255), width=3 * SS)
    if p["prop"] == "mochila":
        for sx in (-1, 1):
            _l(d, [(cx + sx * corpo_w * 0.25, corpo_top + 5), (cx + sx * corpo_w * 0.3, corpo_top + corpo_h - 10)],
               (70, 90, 40), 10)
    if p["prop"] == "cinto":
        _r(d, (cx - corpo_w / 2 - 4, corpo_top + corpo_h - 34, cx + corpo_w / 2 + 4, corpo_top + corpo_h - 8),
           (120, 75, 35), 6, 4)
        _r(d, (cx + 18, corpo_top + corpo_h - 40, cx + 34, corpo_top + corpo_h + 18), (200, 200, 210), 4, 3)
        _e(d, (cx - 52, corpo_top + corpo_h - 38, cx - 26, corpo_top + corpo_h - 6), (240, 200, 40), 3)

    # bracos
    for sx in (-1, 1):
        ombro_x = cx + sx * corpo_w * 0.5
        ombro_y = corpo_top + 30
        manga = p["camisa"] if not p.get("jaleco") else (235, 235, 228)
        if braco == 1 and sx == 1:
            mao = (ombro_x + 55, ombro_y - 70)
        else:
            mao = (ombro_x + sx * 20, ombro_y + corpo_h * 0.55)
        _l(d, [(ombro_x, ombro_y), mao], PRETO, 34)
        _l(d, [(ombro_x, ombro_y), mao], manga, 26)
        _e(d, (mao[0] - 17, mao[1] - 17, mao[0] + 17, mao[1] + 17), p.get("luvas") or PELE, 4)
        if sx == -1 and p["prop"] == "celular":
            _r(d, (mao[0] - 16, mao[1] - 40, mao[0] + 16, mao[1] + 8), (30, 30, 40), 5, 3)
            holo = Image.new("RGBA", im.size, (0, 0, 0, 0))
            hd = ImageDraw.Draw(holo)
            hd.polygon([((mao[0] - 10) * SS, (mao[1] - 40) * SS), ((mao[0] - 70) * SS, (mao[1] - 150) * SS),
                        ((mao[0] + 40) * SS, (mao[1] - 150) * SS), ((mao[0] + 10) * SS, (mao[1] - 40) * SS)],
                       fill=(80, 220, 255, 90))
            hd.rectangle([(mao[0] - 70) * SS, (mao[1] - 200) * SS, (mao[0] + 40) * SS, (mao[1] - 150) * SS],
                         fill=(80, 220, 255, 140), outline=(200, 250, 255, 255), width=3 * SS)
            im.alpha_composite(holo)
        if sx == -1 and p["prop"] == "camera":
            _r(d, (mao[0] - 34, mao[1] - 30, mao[0] + 34, mao[1] + 16), (45, 45, 55), 8, 4)
            _e(d, (mao[0] - 16, mao[1] - 22, mao[0] + 16, mao[1] + 10), (120, 180, 230), 4)
            _r(d, (mao[0] - 26, mao[1] - 40, mao[0] - 8, mao[1] - 30), (45, 45, 55), 3, 3)
        if sx == -1 and p["prop"] == "mapa":
            _p(d, [(mao[0] - 40, mao[1] - 45), (mao[0] - 10, mao[1] - 38), (mao[0] + 20, mao[1] - 45),
                   (mao[0] + 45, mao[1] - 38), (mao[0] + 45, mao[1] + 20), (mao[0] + 20, mao[1] + 13),
                   (mao[0] - 10, mao[1] + 20), (mao[0] - 40, mao[1] + 13)], (245, 235, 200), 3)
            _l(d, [(mao[0] - 30, mao[1] - 20), (mao[0], mao[1] - 5), (mao[0] + 30, mao[1] - 25)], (210, 60, 60), 3)
            _e(d, (mao[0] + 24, mao[1] - 32, mao[0] + 36, mao[1] - 20), (210, 60, 60), 2)
        if sx == -1 and p["prop"] == "bloco":
            _r(d, (mao[0] - 26, mao[1] - 36, mao[0] + 22, mao[1] + 22), (255, 250, 230), 4, 3)
            for k in range(3):
                _l(d, [(mao[0] - 18, mao[1] - 22 + k * 12), (mao[0] + 14, mao[1] - 22 + k * 12)], (120, 150, 200), 2)
        if sx == -1 and p["prop"] == "pelucia":
            _e(d, (mao[0] - 38, mao[1] - 40, mao[0] + 30, mao[1] + 25), (170, 120, 80), 4)
            _e(d, (mao[0] - 40, mao[1] - 52, mao[0] - 18, mao[1] - 30), (170, 120, 80), 4)
            _e(d, (mao[0] + 8, mao[1] - 52, mao[0] + 30, mao[1] - 30), (170, 120, 80), 4)
            d.ellipse([(mao[0] - 14) * SS, (mao[1] - 20) * SS, (mao[0] - 8) * SS, (mao[1] - 14) * SS], fill=PRETO)
            d.ellipse([(mao[0] + 2) * SS, (mao[1] - 20) * SS, (mao[0] + 8) * SS, (mao[1] - 14) * SS], fill=PRETO)

    # cabelo de tras
    cor_c = p["cabelo"]
    est = p["estilo_cabelo"]
    if est == "rabo_lateral":
        _e(d, (cx + cab_r * 0.55, cab_cy + cab_r * 0.1, cx + cab_r * 1.15, cab_cy + cab_r * 1.35), cor_c)
    if est == "coques":
        _e(d, (cx - cab_r * 1.05, cab_cy - cab_r * 1.15, cx - cab_r * 0.45, cab_cy - cab_r * 0.55), cor_c)
        _e(d, (cx + cab_r * 0.45, cab_cy - cab_r * 1.15, cx + cab_r * 1.05, cab_cy - cab_r * 0.55), cor_c)

    if est == "afro":
        _e(d, (cx - cab_r * 1.38, cab_cy - cab_r * 1.12, cx + cab_r * 1.38, cab_cy + cab_r * 0.6), cor_c)

    # cabeca
    _e(d, (cx - cab_r, cab_cy - cab_r * 0.95, cx + cab_r, cab_cy + cab_r * 0.9), PELE)

    # cabelo da frente
    if est == "curto":
        _p(d, [(cx - cab_r * 0.98, cab_cy - cab_r * 0.15), (cx - cab_r * 0.9, cab_cy - cab_r * 0.75),
               (cx - cab_r * 0.3, cab_cy - cab_r * 1.02), (cx + cab_r * 0.5, cab_cy - cab_r * 1.0),
               (cx + cab_r * 0.98, cab_cy - cab_r * 0.4), (cx + cab_r * 0.95, cab_cy - cab_r * 0.15),
               (cx + cab_r * 0.2, cab_cy - cab_r * 0.5), (cx - cab_r * 0.5, cab_cy - cab_r * 0.35)], cor_c)
    elif est == "coques":
        _p(d, [(cx - cab_r * 0.98, cab_cy), (cx - cab_r * 0.85, cab_cy - cab_r * 0.8), (cx, cab_cy - cab_r * 1.0),
               (cx + cab_r * 0.85, cab_cy - cab_r * 0.8), (cx + cab_r * 0.98, cab_cy),
               (cx + cab_r * 0.6, cab_cy - cab_r * 0.45), (cx - cab_r * 0.6, cab_cy - cab_r * 0.45)], cor_c)
    elif est == "bagunçado":
        pts = []
        alturas = [0.95, 1.2, 0.85, 1.12, 0.8, 1.25, 0.88, 1.1, 0.9]
        incl = [-0.12, -0.05, 0.0, 0.06, 0.1, 0.02, -0.04, 0.08, 0.12]
        for k in range(9):
            ang_x = cx - cab_r + k * cab_r * 0.25 + incl[k] * cab_r
            pts.append((ang_x, cab_cy - cab_r * (alturas[k] if k % 2 == 0 else 0.72)))
        _p(d, [(cx - cab_r * 0.98, cab_cy - cab_r * 0.2)] + pts + [(cx + cab_r * 0.98, cab_cy - cab_r * 0.2),
                                                                   (cx, cab_cy - cab_r * 0.55)], cor_c)
    elif est == "rabo_lateral":
        _p(d, [(cx - cab_r * 0.98, cab_cy - cab_r * 0.1), (cx - cab_r * 0.8, cab_cy - cab_r * 0.8),
               (cx, cab_cy - cab_r * 1.0), (cx + cab_r * 0.85, cab_cy - cab_r * 0.8), (cx + cab_r * 0.98, cab_cy),
               (cx + cab_r * 0.4, cab_cy - cab_r * 0.5), (cx - cab_r * 0.5, cab_cy - cab_r * 0.45)], cor_c)
        _e(d, (cx + cab_r * 0.65, cab_cy - cab_r * 0.1, cx + cab_r * 0.9, cab_cy + cab_r * 0.15), (230, 60, 90), 3)
    elif est == "bone":
        cb = p.get("cor_bone", (30, 110, 200))
        _p(d, [(cx - cab_r * 0.98, cab_cy - cab_r * 0.25), (cx - cab_r * 0.9, cab_cy - cab_r * 0.75),
               (cx - cab_r * 0.3, cab_cy - cab_r * 1.05), (cx + cab_r * 0.5, cab_cy - cab_r * 1.02),
               (cx + cab_r * 0.98, cab_cy - cab_r * 0.45), (cx + cab_r * 0.98, cab_cy - cab_r * 0.25)], cb)
        _p(d, [(cx + cab_r * 0.2, cab_cy - cab_r * 0.32), (cx + cab_r * 1.45, cab_cy - cab_r * 0.28),
               (cx + cab_r * 1.3, cab_cy - cab_r * 0.12), (cx + cab_r * 0.2, cab_cy - cab_r * 0.2)], cb)
        _e(d, (cx - cab_r * 0.12, cab_cy - cab_r * 1.12, cx + cab_r * 0.12, cab_cy - cab_r * 0.96), (240, 240, 240), 3)
        for sx in (-1, 1):
            _p(d, [(cx + sx * cab_r * 0.98, cab_cy - cab_r * 0.25), (cx + sx * cab_r * 0.85, cab_cy + cab_r * 0.1),
                   (cx + sx * cab_r * 0.75, cab_cy - cab_r * 0.25)], cor_c, 3)
    elif est == "afro":
        _p(d, [(cx - cab_r * 0.98, cab_cy - cab_r * 0.1), (cx - cab_r * 0.7, cab_cy - cab_r * 0.75),
               (cx, cab_cy - cab_r * 0.95), (cx + cab_r * 0.7, cab_cy - cab_r * 0.75),
               (cx + cab_r * 0.98, cab_cy - cab_r * 0.1), (cx + cab_r * 0.5, cab_cy - cab_r * 0.5),
               (cx - cab_r * 0.5, cab_cy - cab_r * 0.5)], cor_c)
        _r(d, (cx - cab_r * 0.95, cab_cy - cab_r * 0.72, cx + cab_r * 0.95, cab_cy - cab_r * 0.52), (240, 200, 40), 8, 3)
    elif est == "cogumelo":
        _p(d, [(cx - cab_r * 1.02, cab_cy - cab_r * 0.05), (cx - cab_r * 0.95, cab_cy - cab_r * 0.7),
               (cx, cab_cy - cab_r * 1.05), (cx + cab_r * 0.95, cab_cy - cab_r * 0.7),
               (cx + cab_r * 1.02, cab_cy - cab_r * 0.05), (cx, cab_cy - cab_r * 0.3)], cor_c)
    elif est == "maluco":  # big fluffy "mad scientist" cloud
        for k in range(7):
            ang = 3.14159 * (0.05 + 0.9 * k / 6)
            import math as _m
            hx = cx - _m.cos(ang) * cab_r * 0.95
            hy = cab_cy - _m.sin(ang) * cab_r * 0.78
            rr = cab_r * 0.36
            _e(d, (hx - rr, hy - rr, hx + rr, hy + rr), cor_c, 4)

    # olhos
    ox = cab_r * 0.30 + olhar * cab_r * 0.06
    oy = cab_cy - cab_r * 0.05
    orx, ory = cab_r * 0.30, cab_r * 0.36
    for sx in (-1, 1):
        ex = cx + sx * orx * 0.95
        if piscando:
            _l(d, [(ex - orx * 0.8, oy), (ex + orx * 0.8, oy)], PRETO, 5)
        else:
            _e(d, (ex - orx, oy - ory, ex + orx, oy + ory), BRANCO, 4)
            px = ex + olhar * orx * 0.35
            d.ellipse([(px - 9) * SS, (oy - 2) * SS, (px + 9) * SS, (oy + 16) * SS], fill=PRETO)
    if p.get("brincos"):
        for sx in (-1, 1):
            bx = cx + sx * cab_r * 0.97
            d.ellipse([(bx - 16) * SS, (cab_cy + cab_r * 0.22) * SS, (bx + 16) * SS, (cab_cy + cab_r * 0.22 + 34) * SS],
                      outline=(240, 200, 40), width=6 * SS)
    if p.get("oculos"):
        for sx in (-1, 1):
            ex = cx + sx * orx * 0.95
            d.ellipse([(ex - orx * 1.12) * SS, (oy - ory * 1.08) * SS, (ex + orx * 1.12) * SS, (oy + ory * 1.08) * SS],
                      outline=(120, 40, 160), width=7 * SS)
        _l(d, [(cx - orx * 0.18, oy - ory * 0.3), (cx + orx * 0.18, oy - ory * 0.3)], (120, 40, 160), 6)
    if p.get("goggles"):
        _l(d, [(cx - orx * 1.9, oy - ory * 1.4), (cx - orx * 0.2, oy - ory * 0.9)], PRETO, 9)
        _l(d, [(cx + orx * 1.9, oy - ory * 1.4), (cx + orx * 0.2, oy - ory * 0.9)], PRETO, 9)
        for sx in (-1, 1):
            d.ellipse([(cx + sx * orx * 0.95 - orx * 1.1) * SS, (oy - ory * 1.1) * SS,
                       (cx + sx * orx * 0.95 + orx * 1.1) * SS, (oy + ory * 1.1) * SS], outline=PRETO, width=5 * SS)
    if p.get("blush"):
        for sx in (-1, 1):
            d.ellipse([(cx + sx * cab_r * 0.6 - 14) * SS, (cab_cy + cab_r * 0.3 - 8) * SS,
                       (cx + sx * cab_r * 0.6 + 14) * SS, (cab_cy + cab_r * 0.3 + 8) * SS], fill=(255, 170, 160))

    # boca
    by = cab_cy + cab_r * 0.48
    bw = cab_r * (0.5 if p.get("adult") else 0.36)
    if boca_aberta:
        _e(d, (cx - bw * 0.7, by - cab_r * 0.08, cx + bw * 0.7, by + cab_r * 0.26), (70, 20, 30), 4)
        d.ellipse([(cx - bw * 0.35) * SS, (by + cab_r * 0.08) * SS, (cx + bw * 0.35) * SS, (by + cab_r * 0.24) * SS],
                  fill=(230, 90, 100))
    else:
        d.arc([(cx - bw) * SS, (by - cab_r * 0.18) * SS, (cx + bw) * SS, (by + cab_r * 0.12) * SS],
              20, 160, fill=PRETO, width=5 * SS)

    im = im.resize((W, H + 40), Image.LANCZOS)
    return im


def _desenhar_jimmy(boca_aberta, piscando):
    W, H = 380, 300
    im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    MARROM, BR = (110, 60, 30), (250, 250, 245)
    _l(d, [(330, 170), (365, 105)], PRETO, 30)
    _l(d, [(330, 170), (365, 105)], MARROM, 22)
    _e(d, (352, 90, 376, 114), BR, 3)
    for x in (95, 140, 250, 295):
        _r(d, (x - 16, 190, x + 16, 285), MARROM if x in (140, 295) else BR, 10, 4)
    _e(d, (70, 120, 345, 240), MARROM)
    _e(d, (95, 160, 190, 240), BR, 3)
    _e(d, (10, 40, 175, 190), MARROM)
    _p(d, [(70, 50), (40, 0), (110, 45)], MARROM)
    _p(d, [(130, 48), (170, 5), (172, 70)], MARROM)
    _p(d, [(80, 60), (100, 185), (60, 175)], BR, 3)
    _e(d, (2, 110, 90, 175), BR, 4)
    d.ellipse([10 * SS, 115 * SS, 34 * SS, 135 * SS], fill=PRETO)
    for ex in (60, 120):
        if piscando:
            _l(d, [(ex - 14, 95), (ex + 14, 95)], PRETO, 5)
        else:
            _e(d, (ex - 16, 80, ex + 16, 110), BR, 3)
            d.ellipse([(ex - 6) * SS, (87) * SS, (ex + 8) * SS, (103) * SS], fill=PRETO)
    if boca_aberta:
        _e(d, (25, 150, 70, 185), (70, 20, 30), 3)
        d.ellipse([33 * SS, 165 * SS, 60 * SS, 190 * SS], fill=(230, 90, 100))
    else:
        _l(d, [(25, 160), (60, 168)], PRETO, 4)
    return im.resize((W, H), Image.LANCZOS)


def _desenhar_kiko(boca_aberta, piscando):
    """Parrot sidekick."""
    W, H = 300, 380
    im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    VERDE, AMAR, VERM, AZUL = (60, 185, 80), (250, 210, 50), (225, 55, 50), (40, 110, 210)
    _p(d, [(120, 250), (95, 370), (135, 360), (150, 260)], AZUL)
    _p(d, [(150, 250), (165, 375), (190, 360), (175, 255)], VERM)
    for x in (120, 175):
        _l(d, [(x, 300), (x - 10, 345)], (230, 150, 60), 8)
        _l(d, [(x - 25, 348), (x + 10, 345)], (230, 150, 60), 7)
    _e(d, (70, 120, 230, 320), VERDE)
    _e(d, (100, 200, 200, 300), AMAR, 3)
    _p(d, [(80, 160), (40, 260), (120, 280), (130, 190)], AZUL)
    _p(d, [(70, 190), (55, 250), (100, 255)], VERM, 3)
    _e(d, (85, 25, 245, 175), VERDE)
    _p(d, [(120, 30), (140, 0), (160, 32)], VERM, 3)
    _p(d, [(150, 28), (185, 2), (190, 38)], AMAR, 3)
    _e(d, (190, 80, 230, 120), BRANCO, 3)
    if piscando:
        _l(d, [(140, 85), (180, 85)], PRETO, 5)
    else:
        _e(d, (138, 62, 188, 112), BRANCO, 4)
        d.ellipse([158 * SS, 74 * SS, 178 * SS, 98 * SS], fill=PRETO)
    if boca_aberta:
        _p(d, [(205, 95), (275, 120), (215, 132)], (245, 200, 60), 4)
        _p(d, [(205, 140), (255, 160), (210, 168)], (60, 60, 60), 4)
    else:
        _p(d, [(205, 100), (280, 130), (220, 150), (205, 140)], (245, 200, 60), 4)
    return im.resize((W, H), Image.LANCZOS)



