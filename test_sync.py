from sync import capa_mudou, descobrir_canal, parse, resumo

S, V = "streams", "videos"
# Config equivalente à Boas Novas, que é de onde os casos abaixo vieram.
cfg_bn = {
    "nome": "Boas Novas Church",
    "cultos_genericos": ["CULTO", "CEIA", "SANTA CEIA", "DOMINGO", "SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO"],
    "prefixos_pregador": ["PR", "PRA", "PASTOR", "PASTORA", "AP"],
    "titulo": {"separador": "|", "campos": ["titulo", "pregador", "serie"]},
    "series_por_prefixo": {"CONF": "CONFERÊNCIA"},
}
casos = {
    ("O SOCORRO DE DEUS NA BATALHA | PR. PEDRO DANIEL", S): ("O SOCORRO DE DEUS NA BATALHA", "PR. PEDRO DANIEL", None),
    ("AS CHAVES DO REINO E A AUTORIDADE DA IGREJA | PR. PEDRO  DANIEL", S): ("AS CHAVES DO REINO E A AUTORIDADE DA IGREJA", "PR. PEDRO DANIEL", None),
    ("O PODER DA PODA | PR.MARCO LAVIOLA", S): ("O PODER DA PODA", "PR. MARCO LAVIOLA", None),
    ("QUANDO DEUS FRUSTRA OS SEUS PLANOS | LUCAS GOMES", S): ("QUANDO DEUS FRUSTRA OS SEUS PLANOS", "LUCAS GOMES", None),
    ("O COMANDO QUE MUDA SUA ESTAÇÃO | PRA. KELLE GRIPP", V): ("O COMANDO QUE MUDA SUA ESTAÇÃO", "PRA. KELLE GRIPP", None),
    ("RETUBAH | PRA. ANA CHILONGO | CONF.INFLUENCIADORAS DO REINO 2025", V):
        ("RETUBAH", "PRA. ANA CHILONGO", "CONFERÊNCIA INFLUENCIADORAS DO REINO 2025"),
    ("UMA MULHER INESQUECÍVEL | MARIANA VALADÃO | CONF. INFLUENCIADORAS DO REINO 2025", V):
        ("UMA MULHER INESQUECÍVEL", "MARIANA VALADÃO", "CONFERÊNCIA INFLUENCIADORAS DO REINO 2025"),
    # genéricos, música, podcast
    ("DOMINGO NOITE | PR. PEDRO DANIEL", S): None,
    ("QUARTA PROFÉTICA | PR. PEDRO DANIEL", S): None,
    ("QUINTA PROFÉTICA | PR. PEDRO DANIEL", S): None,
    ("TERÇA DA BENÇÃO | PRA. KELLE GRIPP", S): None,
    ("CULTO DOMINGO MANHÃ | PR. PEDRO DANIEL", S): None,
    ("OCEANOS | ANA NOBREGA NA BOAS NOVAS CHURCH", V): None,
    ("COMO MANTER A FÉ QUANDO A PROMESSA PARECE DEMORAR | ANA NOBREGA", V): None,
    ("EM NOME DE JESUS | Ao Vivo na Quinta Profética | BN Music", V): None,
    ("ACTION CAST #01 | Eduardo Schroeder – De R$10 Milhões em Dívida", V): None,
}
for (titulo, aba), esperado in casos.items():
    assert parse(titulo, aba, cfg_bn) == esperado, (titulo, parse(titulo, aba, cfg_bn))

# Outras igrejas: separador e ordem diferentes, sem campo pregador, outros prefixos, título sem separador.
cfg_hifen = {**cfg_bn, "nome": "Igreja Y", "titulo": {"separador": "-", "campos": ["pregador", "titulo"]}}
assert parse("Pr. João - A Graça", V, cfg_hifen) == ("A Graça", "Pr. João", None)
cfg_sem_pregador = {**cfg_bn, "nome": "Igreja Exemplo", "titulo": {"separador": "|", "campos": ["titulo"]}}
assert parse("A GRAÇA", S, cfg_sem_pregador) == ("A GRAÇA", "Igreja Exemplo", None)
assert parse("A GRAÇA", V, cfg_sem_pregador) is None
assert parse("Noite de Louvor", S, cfg_bn) == ("Noite de Louvor", "Boas Novas Church", None)
assert parse("Noite de Louvor", V, cfg_bn) is None
assert parse("CULTO DE DOMINGO", S, cfg_bn) is None
cfg_bispo = {**cfg_bn, "prefixos_pregador": ["BISPO"]}
assert parse("A GRAÇA | BISPO JOÃO", V, cfg_bispo) == ("A GRAÇA", "BISPO JOÃO", None)
assert parse("A GRAÇA | PR. JOÃO", V, cfg_bispo) is None
assert parse("A GRAÇA | PR. JOÃO", S, cfg_bispo) == ("A GRAÇA", "PR. JOÃO", None)
assert descobrir_canal.__doc__

assert resumo("Bem-vindo à Boas Novas Church!\n\n\n🕊 Nossos cultos\n📍 Estoril", "fallback") == "fallback"
assert resumo("Bem-vindo!\n\nChega de viver preso ao passado.\n\nResumo", "x") == "Chega de viver preso ao passado."
assert len(resumo("Bem-vindo!\n\n" + "palavra " * 40, "x")) <= 120

assert capa_mudou('"1790888520"', "2026-10-01T18:00:00.000000")
assert not capa_mudou('"1790888520"', "2026-10-01T19:30:00.123456")
assert not capa_mudou(None, "2026-10-01T18:00:00")

# Live agendada (duas versões da página) não é publicada; encerrada e no ar, sim.
import sync
agendada = ('var ytInitialData = {};"videoDetails":{"videoId":"ZReee-Oi3D8","title":"DOMINGO NOITE",'
            '"lengthSeconds":"0","isUpcoming":true,"isLiveContent":true,"thumbnail":{"thumbnails":[]},"isLive":true}')
espera_servidor = ('<link rel="canonical" href="undefined">var ytInitialData = {"currentVideoEndpoint":{'
                   '"watchEndpoint":{"videoId":"5RTj-re35LI"}},"contents":[{"videoPrimaryInfoRenderer":{"title":{"runs":'
                   '[{"text":"QUINTA PROFÉTICA |  PR. RAIQUE CARMELO"}]},"viewCount":{"videoViewCountRenderer":{"viewCount":'
                   '{"runs":[{"text":"1 aguardando"}]},"isLive":true,"originalViewCount":"1"}}}}]};'
                   '"liveBroadcastDetails":{"isLiveNow":false}')
no_ar_servidor = ('<link rel="canonical" href="undefined">var ytInitialData = {"currentVideoEndpoint":{'
                  '"watchEndpoint":{"videoId":"6QXgmPctgJo"}},"contents":[{"videoPrimaryInfoRenderer":{"title":{"runs":'
                  '[{"text":"QUINTA PROFÉTICA | PR. PEDRO DANIEL"}]},"viewCount":{"videoViewCountRenderer":{"viewCount":'
                  '{"runs":[{"text":"24"},{"text":" assistindo agora"}]},"isLive":true,"originalViewCount":"24"}}}}]};')
encerrada = no_ar_servidor.replace('"isLive":true,', '')
# Live que já acabou também tem isLiveNow false, mas com endTimestamp.
encerrada_detalhes = encerrada + ('"liveBroadcastDetails":{"isLiveNow":false,"startTimestamp":"2026-10-26T22:00:00+00:00",'
                                  '"endTimestamp":"2026-10-27T00:10:00+00:00"}')
paginas = {"https://www.youtube.com/watch?v=a": agendada, "https://www.youtube.com/watch?v=e": espera_servidor,
           "https://www.youtube.com/watch?v=n": no_ar_servidor, "https://www.youtube.com/watch?v=f": encerrada,
           "https://www.youtube.com/watch?v=d": encerrada_detalhes}
sync.pagina = paginas.__getitem__
assert sync.em_breve("a") and sync.em_breve("e")
assert not sync.em_breve("f") and not sync.em_breve("n") and not sync.em_breve("d")
def falha(url):
    raise urllib.error.URLError("sem rede")
import urllib.error
sync.pagina = falha
assert not sync.em_breve("x")  # sem rede: publica como antes, não derruba a execução

print("ok")
