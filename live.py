#!/usr/bin/env python3
"""Quando a live da igreja entra no ar: manda um push "🔴 Estamos ao vivo!" (uma vez por live).
Se o igreja.json tiver live.canal_inchurch, também liga o "Está ao vivo agora?" desse canal na InChurch
(põe a live na home do app) e desliga quando a live acaba.

  python3 live.py --dry-run   # só mostra o que faria
  python3 live.py             # manda o push (e liga/desliga o canal)

Roda a cada 5 min nos horários dos cultos (live.janelas do igreja.json). Mesmas credenciais do sync.py.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error

from igreja import carregar_igreja
from sync import capa, carregar_env, enviar_push, http, login, pagina, segmentacao

# Duas versões da página /live:
#  - navegador comum: bloco "videoDetails" do player com videoId, title e "isLive":true;
#  - servidores (GitHub, VPS): sem esse bloco; o vídeo vem do currentVideoEndpoint e o "ao vivo"
#    do contador de espectadores ("24 assistindo agora", videoViewCountRenderer ... "isLive":true).
# [^{}]*? / (?:(?!Renderer").) não deixam o padrão escapar do bloco; live agendada não tem "isLive":true ali.
PLAYER = re.compile(r'"videoDetails":\{"videoId":"([\w-]{11})","title":"((?:[^"\\]|\\.)*)"[^{}]*?"isLive":true')
VIDEO = re.compile(r'"currentVideoEndpoint":\{.{0,600}?"watchEndpoint":\{"videoId":"([\w-]{11})"')
CONTADOR_AO_VIVO = re.compile(r'"videoViewCountRenderer":\{(?:(?!Renderer").){0,400}?"isLive":true')
TITULO = re.compile(r'"videoPrimaryInfoRenderer":\{"title":\{"runs":\[\{"text":"((?:[^"\\]|\\.)*)"')


def ao_vivo(pagina):
    """(video_id, titulo) se a página mostra uma transmissão acontecendo agora, senão None."""
    if "ytInitialData" not in pagina:
        sys.exit("O YouTube não devolveu a página esperada (bloqueio?) — nada foi enviado")
    if '"isLiveNow":false' in pagina:  # agendada com sala de espera: o contador ("1 aguardando") também vem com "isLive":true
        return None
    m = PLAYER.search(pagina)
    if m:
        return m.group(1), json.loads(f'"{m.group(2)}"')
    video, titulo = VIDEO.search(pagina), TITULO.search(pagina)
    if video and CONTADOR_AO_VIVO.search(pagina):
        return video.group(1), json.loads(f'"{titulo.group(1)}"') if titulo else ""
    return None


def procurar_live(handle):
    """A /live do canal; se ela não abrir na live (às vezes cai na home do canal com a live no ar),
    a página de cada uma das primeiras lives da aba Ao vivo."""
    live = ao_vivo(pagina(f"https://www.youtube.com/{handle}/live"))
    # ponytail: só as 3 primeiras da aba; se a live no ar não aparecer entre elas, aumentar.
    aba = [] if live else re.findall(r"/watch\?v=([\w-]{11})", pagina(f"https://www.youtube.com/{handle}/streams"))
    for vid in list(dict.fromkeys(aba))[:3]:
        live = ao_vivo(pagina(f"https://www.youtube.com/watch?v={vid}"))
        if live:
            break
    return live


def ja_avisado(token, vid):
    """A própria InChurch é o controle: já existe push recente com o link dessa live?"""
    r = http("GET", "v1/inchurch_push_notification/?is_abstract=false&limit=20&order_by=-id", token=token)
    return any(vid in (p.get("redirect_url") or "") for p in r["objects"])


def main(cfg, dry):
    live = procurar_live(cfg["youtube_handle"])
    token, basic_user = login({**carregar_env(), **os.environ})
    canal_id = cfg["live"].get("canal_inchurch")
    canal = f"v1/inchurch_channel/{canal_id}/" if canal_id else None
    if canal and bool(live) != http("GET", canal, token=token)["is_live"]:
        print(("LIGANDO" if live else "DESLIGANDO") + ' o "Está ao vivo agora?" do canal' + (f" ({live[0]})" if live else ""))
        if not dry:
            # send_push False sempre: o push do próprio canal sairia junto com o nosso.
            mudanca = {"is_live": bool(live), "send_push": False}
            if live:  # capa do card "ao vivo" na home = capa da live no YouTube
                mudanca["image"] = capa(live[0])
            http("PATCH", canal, mudanca, token)
    if not live:
        print("Sem live no ar")
        return
    vid, titulo_live = live
    link = f"https://www.youtube.com/watch?v={vid}"
    texto = " — ".join(p.strip() for p in titulo_live.split("|")) + ". Vem assistir com a gente agora!"

    if ja_avisado(token, vid):
        print(f"Push dessa live já foi enviado: {link}")
        return
    if dry:
        print(f"Mandaria: 🔴 Estamos ao vivo! | {texto} | {link}")
        return
    if canal:  # primeira vez que vemos esta live: capa do canal = capa dela, mesmo se o "ao vivo" foi ligado à mão
        http("PATCH", canal, {"image": capa(vid), "send_push": False}, token)
    enviar_push(token, segmentacao(basic_user), "🔴 Estamos ao vivo!", texto, link, capa(vid))
    print(f"PUSH ENVIADO: {texto} | {link}")


def rodar(cfg, dry):
    """Falha de rede passageira (DNS) tenta mais uma vez antes de virar erro.
    Repetir o main é seguro: o ja_avisado impede push duplicado. HTTPError (resposta da API) não repete."""
    try:
        main(cfg, dry)
    except urllib.error.HTTPError:
        raise
    except urllib.error.URLError as e:
        print(f"Rede indisponível ({e.reason}), nova tentativa em 30 s")
        time.sleep(30)
        main(cfg, dry)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="igreja.json", help="arquivo de configuração da igreja")
    ap.add_argument("--dry-run", action="store_true", help="só mostra, não envia")
    a = ap.parse_args()
    rodar(carregar_igreja(a.config), a.dry_run)
