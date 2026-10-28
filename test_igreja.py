import json
import os
import tempfile

from igreja import carregar_igreja

AQUI = os.path.dirname(os.path.abspath(__file__))


def grava(d):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(d, f)
    f.close()
    return f.name


cfg = carregar_igreja(os.path.join(AQUI, "igreja.exemplo.json"))
assert cfg["nome"] == "Igreja Exemplo" and cfg["destaques"] == 3 and cfg["titulo"]["separador"] == "|"

UC = "UC" + "a" * 22
minimo = carregar_igreja(grava({"nome": "X", "youtube_handle": "X", "youtube_channel_id": UC, "desde": "2026-01-01"}))
assert minimo["prefixos_pregador"] == ["PR", "PRA", "PASTOR", "PASTORA", "AP"] and minimo["live"]["janelas"] == []
assert minimo["youtube_handle"] == "@X" and minimo["live"]["canal_inchurch"] is None and minimo["destaques"] == 3

for ruim, campo in [
    ({"nome": "X"}, "youtube_handle"),
    ({"nome": "X", "youtube_handle": "@X", "youtube_channel_id": "abc", "desde": "2026-01-01"}, "youtube_channel_id"),
    ({"nome": "X", "youtube_handle": "@X", "youtube_channel_id": UC, "desde": "01/01/2026"}, "desde"),
    ({"nome": "X", "youtube_handle": "@X", "youtube_channel_id": UC, "desde": "2026-01-01", "destaques": -1}, "destaques"),
    ({"nome": "X", "youtube_handle": "@X", "youtube_channel_id": UC, "desde": "2026-01-01",
      "live": {"janelas": [{"dias": [0], "de": "9h", "ate": "12:00"}]}}, "live.janelas"),
    ({"nome": "X", "youtube_handle": "@X", "youtube_channel_id": UC, "desde": "2026-01-01",
      "live": {"janelas": [{"dias": [7], "de": "09:00", "ate": "12:00"}]}}, "live.janelas"),
    ({"nome": "X", "youtube_handle": "@X", "youtube_channel_id": UC, "desde": "2026-01-01",
      "live": {"janelas": [{"dias": [0], "de": "22:00", "ate": "01:00"}]}}, "live.janelas"),
]:
    try:
        carregar_igreja(grava(ruim))
        raise AssertionError(ruim)
    except SystemExit as e:
        assert str(e).startswith(f"igreja.json: {campo}"), str(e)

print("ok")
