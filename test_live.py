import urllib.error

import live
from live import ao_vivo

# Página /live como o YouTube entrega: sem live (canal), live agendada, live no ar — nas duas versões
# (a de servidores vem com canonical "undefined" e sem isLiveNow), e página de bloqueio.
canal = '<link rel="canonical" href="https://www.youtube.com/channel/UC3P8FkGwOQnCHWo8J4HrpXA">var ytInitialData = {};'
agendada = ('var ytInitialData = {};"videoDetails":{"videoId":"ZReee-Oi3D8","title":"DOMINGO NOITE",'
            '"lengthSeconds":"0","isUpcoming":true,"isLiveContent":true,"thumbnail":{"thumbnails":[]},"isLive":true}')
no_ar_mac = ('<link rel="canonical" href="https://www.youtube.com/watch?v=E4tLVR84wDY">var ytInitialData = {};'
             '"videoDetails":{"videoId":"E4tLVR84wDY","title":"QUARTA PROFÉTICA | PR. PEDRO DANIEL \\u0026 CIA",'
             '"lengthSeconds":"0","isLive":true,"channelId":"UC3P8FkGwOQnCHWo8J4HrpXA"}"isLiveNow":true')
no_ar_github = ('<link rel="canonical" href="undefined">var ytInitialData = {};'
                '"videoDetails":{"videoId":"E4tLVR84wDY","title":"QUARTA PROFÉTICA | PR. PEDRO DANIEL \\u0026 CIA",'
                '"lengthSeconds":"0","isLive":true,"channelId":"UC3P8FkGwOQnCHWo8J4HrpXA"}')
no_ar_servidor = ('<link rel="canonical" href="undefined">var ytInitialData = {"currentVideoEndpoint":{'
                  '"clickTrackingParams":"CAAQg2ci","commandMetadata":{"webCommandMetadata":{"url":"/watch?v=6QXgmPctgJo",'
                  '"webPageType":"WEB_PAGE_TYPE_WATCH","rootVe":3832}},"watchEndpoint":{"videoId":"6QXgmPctgJo"}},'
                  '"contents":[{"videoPrimaryInfoRenderer":{"title":{"runs":[{"text":"QUINTA PROFÉTICA | PR. PEDRO DANIEL"}]},'
                  '"viewCount":{"videoViewCountRenderer":{"viewCount":{"runs":[{"text":"24"},{"text":" assistindo agora"}]},'
                  '"isLive":true,"originalViewCount":"24"}}}}]};')
assert ao_vivo(no_ar_servidor) == ("6QXgmPctgJo", "QUINTA PROFÉTICA | PR. PEDRO DANIEL"), ao_vivo(no_ar_servidor)
assert ao_vivo(no_ar_servidor.replace('"isLive":true,', '')) is None
assert ao_vivo(canal) is None
assert ao_vivo(agendada) is None
esperado = ("E4tLVR84wDY", "QUARTA PROFÉTICA | PR. PEDRO DANIEL & CIA")
assert ao_vivo(no_ar_mac) == esperado, ao_vivo(no_ar_mac)
assert ao_vivo(no_ar_github) == esperado, ao_vivo(no_ar_github)
try:
    ao_vivo("<html>Before you continue to YouTube</html>")
    raise AssertionError("página de bloqueio deveria abortar")
except SystemExit:
    pass
espera_servidor = ('<link rel="canonical" href="undefined">var ytInitialData = {"currentVideoEndpoint":{'
                   '"watchEndpoint":{"videoId":"5RTj-re35LI"}},"contents":[{"videoPrimaryInfoRenderer":{"title":{"runs":'
                   '[{"text":"QUINTA PROFÉTICA |  PR. RAIQUE CARMELO"}]},"viewCount":{"videoViewCountRenderer":{"viewCount":'
                   '{"runs":[{"text":"1 aguardando"}]},"isLive":true,"originalViewCount":"1"}}}}]};'
                   '"liveBroadcastDetails":{"isLiveNow":false}')
assert ao_vivo(espera_servidor) is None

# /live caindo na home do canal com a live no ar: acha a live pelas primeiras da aba Ao vivo.
aba = '"url":"/watch?v=5RTj-re35LI" "url":"/watch?v=6QXgmPctgJo" "url":"/watch?v=6QXgmPctgJo"'
paginas = {"https://www.youtube.com/@X/live": canal, "https://www.youtube.com/@X/streams": aba,
           "https://www.youtube.com/watch?v=5RTj-re35LI": espera_servidor,
           "https://www.youtube.com/watch?v=6QXgmPctgJo": no_ar_servidor}
live.pagina = paginas.__getitem__
assert live.procurar_live("@X") == ("6QXgmPctgJo", "QUINTA PROFÉTICA | PR. PEDRO DANIEL")
paginas["https://www.youtube.com/@X/streams"] = '"url":"/watch?v=5RTj-re35LI"'
assert live.procurar_live("@X") is None

# Canal da home ("ao vivo agora") só é tocado se a igreja configurou canal_inchurch.
chamadas = []
live.http = lambda method, path, body=None, token=None: chamadas.append((method, path)) or {"objects": [], "is_live": False}
live.login = lambda env: ("tok", {"group": None, "subgroup": None})
procurar = live.procurar_live
live.procurar_live = lambda handle: None
live.main({"youtube_handle": "@X", "live": {"canal_inchurch": None}}, dry=True)
assert chamadas == [], chamadas
live.main({"youtube_handle": "@X", "live": {"canal_inchurch": 6720}}, dry=True)
assert chamadas == [("GET", "v1/inchurch_channel/6720/")], chamadas
live.procurar_live = procurar

# Falha de rede tenta de novo uma vez; HTTPError não repete.
tentativas, live.time.sleep = [], lambda s: None
def main_falha_1x(cfg, dry):
    tentativas.append(1)
    if len(tentativas) == 1:
        raise urllib.error.URLError(OSError(-3, "Try again"))
live.main = main_falha_1x
live.rodar({"youtube_handle": "@X"}, False)
assert len(tentativas) == 2
def main_http(cfg, dry):
    raise urllib.error.HTTPError("u", 500, "erro", {}, None)
live.main = main_http
try:
    live.rodar({"youtube_handle": "@X"}, False)
    raise AssertionError("HTTPError não deveria repetir")
except urllib.error.HTTPError:
    pass
print("ok")
