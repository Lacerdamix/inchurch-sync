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

print("ok")
