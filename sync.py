#!/usr/bin/env python3
"""Publica as pregações do YouTube da igreja (abas Vídeos e Ao vivo) como Palavras na InChurch.

  python3 sync.py --dry-run               # mostra o que publicaria
  python3 sync.py                         # publica os novos
  python3 sync.py --canal @SuaIgreja      # descobre o id do canal do YouTube (para o igreja.json)

Configuração da igreja no igreja.json (ver igreja.exemplo.json): canal, data de corte, como os títulos
dos vídeos são escritos, nomes de culto genéricos, destaques. Credenciais em variáveis de ambiente
(ou num .env ao lado): INCHURCH_EMAIL, INCHURCH_PASSWORD (e INCHURCH_APP_ID se o e-mail tiver mais de um app).

Push: a Palavra mais recente de cada execução gera um push "🙌 Nova Palavra no app" com a capa do vídeo.
Dedupe: a própria InChurch é o controle do que já foi publicado (id do vídeo e título).
"""
import argparse
import base64
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from igreja import carregar_igreja

FEED = "https://www.youtube.com/feeds/videos.xml?playlist_id={}"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "m": "http://search.yahoo.com/mrss/"}
# API interna do painel admin.inchurch.com.br (não documentada) — se quebrar, conferir no DevTools do painel.
API = "https://www.inradar.com.br/api"
FUSO = ZoneInfo("America/Sao_Paulo")
YT_ID = re.compile(r"(?:v=|youtu\.be/|embed/|live/|shorts/)([\w-]{11})")
CANAL_ID = re.compile(r'<link rel="canonical" href="https://www\.youtube\.com/channel/(UC[\w-]{22})"')


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", s).strip()


def parse(titulo, aba, cfg):
    """(titulo, autor, serie) se for publicável, senão None. O formato do título vem de cfg["titulo"]."""
    t = cfg["titulo"]
    partes = [" ".join(p.split()) for p in titulo.split(t["separador"])]
    campos = dict(zip(t["campos"], partes))
    nome = campos.get("titulo") or partes[0]
    if any(norm(nome).startswith(g) for g in map(norm, cfg["cultos_genericos"])):
        return None  # nome de culto no início = live ainda não renomeada
    pregador = campos.get("pregador", "")
    tem_pregador = any(re.match(rf"{re.escape(norm(p))}(\s|$)", norm(pregador)) for p in cfg["prefixos_pregador"])
    serie = None
    for prefixo, nome_serie in cfg["series_por_prefixo"].items():
        m = next((re.match(rf"{re.escape(prefixo)}\.?\s*(.+)", p, re.I) for p in partes[1:]
                  if re.match(rf"{re.escape(prefixo)}\b", p, re.I)), None)
        if m:
            serie = f"{nome_serie} {m.group(1)}".upper()
    # Toda live é culto; na aba Vídeos tem música e podcast, então lá só entra pregador ou série.
    if aba == "streams" or tem_pregador or serie:
        autor = re.sub(r"^(PRA?|AP)\.(?=\S)", r"\1. ", pregador, flags=re.I) if pregador else cfg["nome"]
        return nome[:120], autor, serie
    return None


def resumo(descricao, fallback):
    """1º parágrafo de verdade da descrição do YouTube (pula saudação, texto fixo e blocos de emoji), até 120 chars."""
    for p in re.split(r"\n\s*\n", descricao or ""):
        p = " ".join(p.split())
        if p and p[0].isalnum() and not p.lower().startswith(("bem-vindo", "toda semana", "e, nesta semana")):
            return p if len(p) <= 120 else p[:119].rsplit(" ", 1)[0] + "…"
    return fallback


# --- YouTube ---

def pagina(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "pt-BR"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def em_breve(vid):
    """A live ainda não começou? Agendada tem "isUpcoming":true, ou isLiveNow false sem endTimestamp (sala de espera).
    Sem rede: False, publica como antes em vez de derrubar a execução."""
    try:
        p = pagina(f"https://www.youtube.com/watch?v={vid}")
    except (urllib.error.URLError, OSError):
        return False
    return '"isUpcoming":true' in p or ('"isLiveNow":false' in p and '"endTimestamp"' not in p)


def descobrir_canal(handle):
    """Id do canal (UC…) a partir do @handle: vem do <link rel="canonical"> da página do canal."""
    m = CANAL_ID.search(pagina(f"https://www.youtube.com/{handle}"))
    if not m:
        sys.exit(f"Não achei o canal {handle} no YouTube. Confira o endereço (ex.: @SuaIgreja).")
    return m.group(1)


def rss(aba, channel_id):
    # O RSS não diz se a live ainda é agendada; em_breve() confere na página antes de publicar.
    playlist = {"videos": "UULF", "streams": "UULV"}[aba] + channel_id[2:]
    try:
        with urllib.request.urlopen(FEED.format(playlist), timeout=30) as r:
            entradas = ET.parse(r).getroot().findall("a:entry", NS)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"O YouTube não achou o canal {channel_id} (aba {aba}). Confira youtube_channel_id no igreja.json.")
        raise
    return [{"id": e.findtext("yt:videoId", namespaces=NS), "title": e.findtext("a:title", namespaces=NS),
             "timestamp": datetime.fromisoformat(e.findtext("a:published", namespaces=NS)).timestamp(),
             "description": e.findtext("m:group/m:description", namespaces=NS), "aba": aba} for e in entradas]


def listar(channel_id):
    # Aba Vídeos primeiro: quando a mesma pregação existe como live e como vídeo editado, fica o editado.
    return rss("videos", channel_id) + rss("streams", channel_id)


def capa(vid):
    for q in ("maxresdefault", "hqdefault"):
        try:
            with urllib.request.urlopen(f"https://i.ytimg.com/vi/{vid}/{q}.jpg", timeout=30) as r:
                b64 = base64.b64encode(r.read()).decode()
            return {"name": "Image.jpeg", "content_type": "image/jpeg", "file": "data:image/jpeg;base64," + b64}
        except urllib.error.HTTPError:
            pass
    return None


# --- InChurch ---

def http(method, path, body=None, token=None):
    headers = {"Accept": "application/json", "Content-Type": "application/json;charset=UTF-8", "Channel": "control_panel"}
    if token:
        headers["Authorization"] = token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}/{path}", data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read() or b"null")


def login(env):
    email, senha = env["INCHURCH_EMAIL"], env["INCHURCH_PASSWORD"]
    app_id = env.get("INCHURCH_APP_ID")
    if not app_id:
        apps = http("POST", "v1/basic_user/get_app_ids/", {"email": email, "password": senha})
        if len(apps) != 1:
            sys.exit("Defina INCHURCH_APP_ID. Opções: " + ", ".join(f"{a['app_id']} ({a['name']})" for a in apps))
        app_id = apps[0]["app_id"]
    r = http("POST", "v1/basic_user_person/login/",
             {"username": email, "password": senha, "app_id": app_id, "source": "inchurch"})
    return r["authorization"], r["basic_user"]


def existentes(token):
    """IDs do YouTube e títulos já publicados — a própria InChurch é o controle do que já foi."""
    ids, titulos, offset = set(), set(), 0
    while True:
        r = http("GET", f"v2/inchurch_preach/?limit=100&offset={offset}&fields=id,title,url_video", token=token)
        for p in r["objects"]:
            ids.update(YT_ID.findall(p.get("url_video") or ""))
            titulos.add(norm(p.get("title") or ""))
        if not r["objects"] or not (r.get("meta") or {}).get("next"):
            return ids, titulos
        offset += 100


def series(token):
    """Séries de verdade (não as automáticas de 1 Palavra): título normalizado → resource_uri."""
    r = http("GET", "v2/preach_series/?limit=0&is_abstract=false&fields=title,resource_uri", token=token)
    return {norm(s["title"]): s["resource_uri"] for s in r["objects"]}


def capa_mudou(etag, atualizado_em):
    """A miniatura do YouTube foi trocada depois da última atualização da Palavra?

    O etag do i.ytimg.com é o epoch do envio da miniatura; updated_at da InChurch vem em horário de
    Brasília sem fuso. Trocar a imagem atualiza o updated_at, então a mesma capa não é reenviada.
    """
    try:
        enviada = int(str(etag).strip('"'))
    except ValueError:
        return False
    return enviada > datetime.fromisoformat(atualizado_em[:19]).replace(tzinfo=FUSO).timestamp()


def etag_capa(vid):
    for q in ("maxresdefault", "hqdefault"):  # mesma ordem de capa()
        try:
            req = urllib.request.Request(f"https://i.ytimg.com/vi/{vid}/{q}.jpg", method="HEAD")
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.headers.get("ETag")
        except urllib.error.HTTPError:
            pass
    return None


def atualizar_capas(token, dry_run=False, dias=60):
    """Troca a imagem das Palavras recentes cuja miniatura no YouTube virou a definitiva depois."""
    # ponytail: só os últimos 60 dias; Palavra mais velha raramente ganha capa nova.
    r = http("GET", "v2/inchurch_preach/?limit=0&order_by=-published_at&fields=id,title,url_video,updated_at,published_at",
             token=token)
    limite = datetime.now(FUSO).replace(tzinfo=None) - timedelta(days=dias)
    for p in r["objects"]:
        if datetime.fromisoformat(p["published_at"][:19]) < limite:
            break
        vid = next(iter(YT_ID.findall(p.get("url_video") or "")), None)
        if vid and capa_mudou(etag_capa(vid), p["updated_at"]):
            print(f"CAPA NOVA {p['title']}")
            if not dry_run:
                http("PATCH", f"v2/inchurch_preach/{p['id']}/", {"image": capa(vid)}, token)


def destacar(token, n):
    """Deixa em destaque só as n Palavras mais recentes (tira o destaque das outras). n = 0 não mexe."""
    if not n:
        return
    r = http("GET", "v2/inchurch_preach/?limit=0&order_by=-published_at&fields=id,title,is_highlighted", token=token)
    for i, p in enumerate(r["objects"]):
        if p["is_highlighted"] != (i < n):
            http("PATCH", f"v2/inchurch_preach/{p['id']}/", {"is_highlighted": i < n}, token)
            print(("DESTAQUE " if i < n else "SEM DESTAQUE ") + p["title"])


def enviar_push(token, seg, titulo, texto, link, imagem=None):
    # Mesmo formato do painel (conteudo/push/novo-push); sem send_date = envia na hora.
    http("POST", "v1/inchurch_push_notification/",
         {"title": titulo, "content": texto, "redirect_url": link, "image": imagem, "recurrence": None, **seg}, token)


def segmentacao(basic_user):
    # Igual às Palavras publicadas à mão: "Denominação" = group + subgroup, sem regional/local.
    uri = lambda x: x.get("resource_uri") if isinstance(x, dict) else x
    return {"group": uri(basic_user["group"]), "subgroup": uri(basic_user["subgroup"]),
            "regional": None, "tertiarygroup": None, "small_groups": []}


def carregar_env():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        pares = (l.split("=", 1) for l in f if "=" in l and not l.lstrip().startswith("#"))
        return {k.strip(): v.strip().strip("'\"") for k, v in pares}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="igreja.json", help="arquivo de configuração da igreja")
    ap.add_argument("--dry-run", action="store_true", help="só mostra, não publica")
    ap.add_argument("--limite", type=int, help="publica no máximo N (os mais antigos primeiro)")
    ap.add_argument("--canal", metavar="@handle", help="imprime o id do canal do YouTube e sai")
    a = ap.parse_args()
    if a.canal:
        print(descobrir_canal(a.canal if a.canal.startswith("@") else "@" + a.canal))
        return
    cfg = carregar_igreja(a.config)
    desde = datetime.fromisoformat(cfg["desde"]).replace(tzinfo=FUSO)
    env = {**carregar_env(), **os.environ}

    token, seg, ids_ok, titulos_ok, serie_uri = None, {}, set(), set(), {}
    if env.get("INCHURCH_EMAIL"):
        token, basic_user = login(env)
        seg = segmentacao(basic_user)
        ids_ok, titulos_ok = existentes(token)
        serie_uri = series(token)
        print(f"InChurch: {len(ids_ok)} vídeos já publicados, {len(serie_uri)} séries")
    elif a.dry_run:
        print("Sem credenciais: dry-run sem checar o que já está na InChurch")
    else:
        sys.exit("Faltam INCHURCH_EMAIL / INCHURCH_PASSWORD")

    novos = []
    for v in listar(cfg["youtube_channel_id"]):
        p = parse(v.get("title") or "", v["aba"], cfg)
        # ponytail: dedupe por título também pega live x vídeo editado; o custo é "PARTE 01/02" com o mesmo título virar uma só.
        if not p or v["timestamp"] < desde.timestamp() or v["id"] in ids_ok or norm(p[0]) in titulos_ok:
            continue
        if v["aba"] == "streams" and em_breve(v["id"]):  # só vídeo novo chega aqui: uma página a mais por vídeo
            print(f"AGENDADA (espera o culto) {p[0]}")
            continue
        titulos_ok.add(norm(p[0]))
        novos.append((v,) + p)
    novos = sorted(novos, key=lambda n: n[0]["timestamp"])[:a.limite]  # mais antigo primeiro, o mais recente por último
    print(f"{len(novos)} novas pregações desde {desde:%d/%m/%Y}")

    falhas = 0
    for i, (v, titulo, autor, serie) in enumerate(novos):
        vid = v["id"]
        push = i == len(novos) - 1  # só 1 push por execução, da Palavra mais recente
        quando =datetime.fromtimestamp(v["timestamp"], FUSO).strftime("%Y-%m-%dT%H:%M")
        linha =f"{quando}  {titulo} — {autor}" + (f"  [série: {serie}]" if serie else "") + ("  [push]" if push else "")
        if a.dry_run:
            print(f"{linha}  https://youtu.be/{vid}")
            continue
        try:
            imagem = capa(vid)
            if serie and norm(serie) not in serie_uri:
                http("POST", "v2/preach_series/", {"title": serie, "description": serie, "preaches": [],
                                                   "categories": [], "image": imagem, **seg}, token)
                serie_uri = series(token)
                if norm(serie) not in serie_uri:  # sem isso, cada Palavra seguinte criaria outra série igual
                    sys.exit(f"Série {serie} foi criada mas não aparece na lista — conferir no painel")
                print(f"SÉRIE CRIADA {serie}")
            http("POST", "v2/inchurch_preach/", {
                "title": titulo, "description": resumo(v.get("description"), titulo),
                "author": autor, "author_field_name": "Preletor",
                "url_video": f"https://www.youtube.com/watch?v={vid}", "url_audio": None, "text": None,
                "categories": [], "series": serie_uri[norm(serie)] if serie else None, "published_at": quando,
                "can_share": True, "send_push": False, "is_highlighted": False, "is_scheduled": False,
                "image": imagem, **seg,
            }, token)
            print(f"OK {linha}")
            if push:
                enviar_push(token, seg, "🙌 Nova Palavra no app", f"{titulo} — {autor}",
                            f"https://www.youtube.com/watch?v={vid}", imagem)
                print(f"PUSH ENVIADO {titulo}")
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError) as e:
            falhas += 1
            corpo = e.read().decode(errors="ignore")[:300] if isinstance(e, urllib.error.HTTPError) else ""
            print(f"ERRO {vid} {titulo}: {e!r} {corpo}")
    if token and not a.dry_run:
        atualizar_capas(token)
        destacar(token, cfg["destaques"])
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
