"""Lê e valida o igreja.json (a configuração da igreja). Erro de validação vira mensagem curta, sem traceback."""
import json
import re
import sys
from datetime import date

DEFAULTS = {
    "destaques": 3,
    "cultos_genericos": [],
    "prefixos_pregador": ["PR", "PRA", "PASTOR", "PASTORA", "AP"],
    "series_por_prefixo": {},
    "titulo": {"separador": "|", "campos": ["titulo", "pregador"]},
    "live": {"canal_inchurch": None, "janelas": []},
}
HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def erro(campo, problema):
    sys.exit(f"igreja.json: {campo}: {problema}")


def carregar_igreja(path):
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    for campo in ("nome", "youtube_handle", "youtube_channel_id", "desde"):
        if not cfg.get(campo):
            erro(campo, "obrigatório")
    cfg = {**DEFAULTS, **cfg}
    cfg["titulo"] = {**DEFAULTS["titulo"], **cfg["titulo"]}
    cfg["live"] = {**DEFAULTS["live"], **cfg["live"]}
    if not cfg["youtube_handle"].startswith("@"):
        cfg["youtube_handle"] = "@" + cfg["youtube_handle"]
    if not re.fullmatch(r"UC[\w-]{22}", cfg["youtube_channel_id"]):
        erro("youtube_channel_id", "deve começar com UC e ter 24 caracteres (ex.: UC3P8FkGwOQnCHWo8J4HrpXA)")
    try:
        date.fromisoformat(cfg["desde"])
    except ValueError:
        erro("desde", "use o formato AAAA-MM-DD (ex.: 2026-01-01)")
    if not isinstance(cfg["destaques"], int) or cfg["destaques"] < 0:
        erro("destaques", "número inteiro, 0 ou mais")
    for j in cfg["live"]["janelas"]:
        dias = j.get("dias")
        if not dias or any(d not in range(7) for d in dias):
            erro("live.janelas", "dias deve ser uma lista com 0 (domingo) a 6 (sábado)")
        for k in ("de", "ate"):
            if not HORA.match(str(j.get(k, ""))):
                erro("live.janelas", f"{k} deve ser HH:MM (ex.: 19:00)")
        if j["ate"] < j["de"]:
            erro("live.janelas", f"{j['de']}–{j['ate']}: a janela não pode passar da meia-noite (use até 23:55)")
    return cfg
