# inchurch-sync: plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repo público `Lacerdamix/inchurch-sync` que é plugin do Claude Code e fonte dos scripts: um leigo instala o plugin, escreve `instalar`, e sai com pregações e push de live rodando no GitHub Actions da igreja dele.

**Architecture:** `sync.py` e `live.py` são cópias generalizadas dos scripts da Boas Novas (`/Users/LacerdaMix/GitHub/Auto youtube add /`), lendo tudo que é da igreja de um `igreja.json`. `instalar.py` gera a pasta do repo da igreja (config + workflows com cron já calculado) a partir de `modelo/`. A skill `skills/instalar/SKILL.md` conduz a entrevista e chama `instalar.py` e `gh`. Os workflows da igreja fazem checkout de `Lacerdamix/inchurch-sync@v1` e rodam os scripts de lá.

**Tech Stack:** Python 3 stdlib (urllib, json, re, xml, zoneinfo, datetime). `gh` CLI. GitHub Actions. Claude Code plugin (`.claude-plugin/`, `skills/`, `commands/`).

**Spec:** `/Users/LacerdaMix/GitHub/inchurch-sync/docs/design.md`

## Global Constraints

- Só stdlib; nenhum `pip install` em lugar nenhum.
- Tudo que o cliente lê é em português do Brasil.
- Senha da InChurch nunca em arquivo nem no chat do agente: só `gh secret set INCHURCH_PASSWORD` digitado pelo cliente.
- Nenhuma alteração no repo da Boas Novas (`Auto youtube add`); só leitura para copiar.
- Testes no estilo do repo de origem: `test_*.py` com `assert`, rodáveis com `python3 test_x.py` e com `pytest -q`.
- Commits pequenos, mensagem em português, sufixo `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Working dir do repo novo: `/Users/LacerdaMix/GitHub/inchurch-sync` (já tem `docs/`).

## Review Focus

1. Título sem separador na aba Vídeos ("Noite de Louvor") deve ser ignorado; na aba Ao vivo, publicado com autor = nome da igreja. (Task 2)
2. Igreja com `titulo.campos` sem `pregador` e canal só de cultos: tudo da aba Ao vivo entra, nada da aba Vídeos sem série por prefixo. (Task 2)
3. Live agendada já com título de pregação não pode virar Palavra antes do culto. (Task 3)
4. Janela de live que cruza a meia-noite UTC (19:00–23:55 BRT) tem de gerar duas linhas de cron com dias deslocados. (Task 5)
5. `igreja.json` com campo faltando ou hora malformada deve falhar com mensagem em português dizendo o campo, não com traceback. (Task 1)

---

### Task 1: Esqueleto do repo e leitor da config

**Files:**
- Create: `igreja.py`, `igreja.exemplo.json`, `test_igreja.py`, `.gitignore`

**Interfaces:**
- Produces: `carregar_igreja(path: str) -> dict` em `igreja.py`. Lê o JSON, aplica defaults (`destaques=3`, `cultos_genericos=[]`, `prefixos_pregador=["PR","PRA","PASTOR","PASTORA","AP"]`, `series_por_prefixo={}`, `titulo={"separador":"|","campos":["titulo","pregador"]}`, `live={"canal_inchurch":None,"janelas":[]}`), valida e devolve o dict. Erro de validação: `sys.exit("igreja.json: <campo>: <problema>")`.
- Produces: `ERRO_CONFIG` não existe; a validação usa `sys.exit` com string começando por `igreja.json:`.

- [ ] **Step 1: `git init` em `/Users/LacerdaMix/GitHub/inchurch-sync`, `.gitignore` com `.env`, `__pycache__/`, `.pytest_cache/`, `*.log`. Commit "repo: início" com o `docs/` que já está lá.**

- [ ] **Step 2: Escrever `igreja.exemplo.json`** com exatamente o JSON da seção "igreja.json" do design (nome "Igreja Exemplo", handle "@IgrejaExemplo", `youtube_channel_id` "UCxxxxxxxxxxxxxxxxxxxxxx").

- [ ] **Step 3: Escrever `test_igreja.py` (falhando)**

```python
import json, tempfile, os
from igreja import carregar_igreja

def grava(d):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(d, f); f.close(); return f.name

cfg = carregar_igreja("igreja.exemplo.json")
assert cfg["nome"] == "Igreja Exemplo" and cfg["destaques"] == 3 and cfg["titulo"]["separador"] == "|"
minimo = carregar_igreja(grava({"nome": "X", "youtube_handle": "@X", "youtube_channel_id": "UC" + "a" * 22, "desde": "2026-01-01"}))
assert minimo["prefixos_pregador"] == ["PR", "PRA", "PASTOR", "PASTORA", "AP"] and minimo["live"]["janelas"] == []
for ruim, campo in [({"nome": "X"}, "youtube_channel_id"),
                    ({"nome": "X", "youtube_handle": "@X", "youtube_channel_id": "UC" + "a" * 22, "desde": "01/01/2026"}, "desde"),
                    ({"nome": "X", "youtube_handle": "@X", "youtube_channel_id": "UC" + "a" * 22, "desde": "2026-01-01",
                      "live": {"janelas": [{"dias": [0], "de": "9h", "ate": "12:00"}]}}, "live.janelas")]:
    try:
        carregar_igreja(grava(ruim)); assert False, ruim
    except SystemExit as e:
        assert str(e).startswith(f"igreja.json: {campo}"), str(e)
print("ok")
```

- [ ] **Step 4: Rodar `python3 test_igreja.py`, esperar `ModuleNotFoundError: igreja`.**

- [ ] **Step 5: Implementar `carregar_igreja(path)` em `igreja.py`.** Validação: `nome`, `youtube_handle`, `youtube_channel_id` (regex `^UC[\w-]{22}$`), `desde` (`date.fromisoformat`) obrigatórios; `destaques` int ≥ 0; cada janela com `dias` lista de 0–6 e `de`/`ate` no formato `HH:MM`. Handle sem `@` ganha `@`.

- [ ] **Step 6: Rodar `python3 test_igreja.py`, esperar `ok`. Commit "igreja.json: leitor com defaults e validação".**

---

### Task 2: `sync.py` lendo a config

**Files:**
- Create: `sync.py` (copiado de `/Users/LacerdaMix/GitHub/Auto youtube add /sync.py`), `test_sync.py`

**Interfaces:**
- Consumes: `carregar_igreja` (Task 1).
- Produces: `parse(titulo: str, aba: str, cfg: dict) -> tuple[str, str, str | None] | None`; `rss(aba: str, channel_id: str) -> list[dict]`; `descobrir_canal(handle: str) -> str` (abre `https://www.youtube.com/<handle>` e tira o `UC…` do `<link rel="canonical" href=".../channel/UC…">`; levanta `SystemExit` em português se não achar); `http`, `login`, `enviar_push`, `segmentacao`, `capa`, `carregar_env`, `norm`, `resumo` mantidos com as assinaturas atuais; `main()` aceita `--config` (default `igreja.json`), `--dry-run`, `--limite`, `--canal @handle` (imprime o channel id e sai; é o que a skill usa).

- [ ] **Step 1: Copiar `sync.py` e escrever `test_sync.py` (falhando).** Portar os casos de `parse` do repo de origem usando `cfg_bn` = config equivalente à Boas Novas (`separador "|"`, `campos ["titulo","pregador","serie"]`, `cultos_genericos` = lista do `GENERICO` atual, `prefixos_pregador ["PR","PRA","PASTOR","PASTORA","AP"]`, `series_por_prefixo {"CONF": "CONFERÊNCIA"}`), menos o caso "PALAVRA DA SEMANA" (deixa de existir). Acrescentar:

```python
cfg_hifen = {**cfg_bn, "nome": "Igreja Y", "titulo": {"separador": "-", "campos": ["pregador", "titulo"]}}
assert parse("Pr. João - A Graça", "videos", cfg_hifen) == ("A Graça", "Pr. João", None)
cfg_sem_pregador = {**cfg_bn, "titulo": {"separador": "|", "campos": ["titulo"]}}
assert parse("A GRAÇA", "streams", cfg_sem_pregador) == ("A GRAÇA", "Igreja Exemplo", None)
assert parse("A GRAÇA", "videos", cfg_sem_pregador) is None
assert parse("Noite de Louvor", "streams", cfg_bn) == ("Noite de Louvor", cfg_bn["nome"], None)   # sem separador, ao vivo
assert parse("Noite de Louvor", "videos", cfg_bn) is None                                           # sem separador, vídeos
cfg_bispo = {**cfg_bn, "prefixos_pregador": ["BISPO"]}
assert parse("A GRAÇA | BISPO JOÃO", "videos", cfg_bispo) == ("A GRAÇA", "BISPO JOÃO", None)
assert parse("A GRAÇA | PR. JOÃO", "videos", cfg_bispo) is None
assert descobrir_canal.__doc__  # existe
```

Manter os asserts de `resumo` e `capa_mudou` do original. Regra de `parse`: separa por `cfg["titulo"]["separador"]`, mapeia pela ordem de `campos`; `GENERICO` vira `any(norm(partes[0]).startswith(g) for g in cultos_genericos)`; `PASTOR` vira prefixo de `norm(pregador)` seguido de espaço ou ponto; `series_por_prefixo` é `{prefixo: nome_da_serie}` e o valor da série é `f"{nome} {resto}".upper()`; autor default `cfg["nome"]`.

- [ ] **Step 2: Rodar `python3 test_sync.py`, esperar falha de import ou de assinatura.**

- [ ] **Step 3: Generalizar `sync.py`.** Remover `CHANNEL`, `FEED` fixo, `DESDE`, `SERIES_MANUAIS`, `GENERICO`, `PASTOR`, `CONF`, `ytdlp`, `listar(retroativo)`, `--retroativo`. `FEED = "https://www.youtube.com/feeds/videos.xml?playlist_id={}"` com `playlist = {"videos": "UULF", "streams": "UULV"}[aba] + channel_id[2:]`. `main` carrega `cfg = carregar_igreja(a.config)`, `desde = datetime.fromisoformat(cfg["desde"]).replace(tzinfo=FUSO)`, filtra `v["timestamp"] >= desde.timestamp()`, chama `destacar(token, cfg["destaques"])` (pula se 0). Docstring do módulo reescrita sem Boas Novas.

- [ ] **Step 4: Rodar `python3 test_sync.py`, esperar `ok`. Rodar `python3 sync.py --dry-run --config igreja.exemplo.json` sem `.env`: esperar "Sem .env: dry-run sem checar" e nenhum traceback (o feed do canal fictício pode vir vazio ou 404; 404 deve virar mensagem "canal não encontrado", não traceback).**

- [ ] **Step 5: Commit "sync: lê igreja.json; parse configurável; sem retroativo".**

---

### Task 3: Live agendada não vira Palavra

**Files:**
- Modify: `sync.py`, `test_sync.py`

**Interfaces:**
- Produces: `em_breve(vid: str) -> bool` em `sync.py`: abre `https://www.youtube.com/watch?v=<vid>` (User-Agent e Accept-Language como em `live.pagina`) e devolve `True` se a página tem `"isUpcoming":true` ou `"isLiveNow":false`. Falha de rede → `False` (publica como hoje; não derruba a execução).

- [ ] **Step 1: Testes (falhando)** com fixtures copiadas do `test_sync.py` de origem (`agendada`, `espera_servidor`, `no_ar_servidor`, `encerrada`):

```python
import sync
paginas = {"a": agendada, "e": espera_servidor, "n": no_ar_servidor, "f": encerrada}
sync.pagina = paginas.__getitem__
assert sync.em_breve("a") and sync.em_breve("e") and not sync.em_breve("f")
```

- [ ] **Step 2: Rodar, esperar `AttributeError: em_breve`.**

- [ ] **Step 3: Implementar `pagina(url)` (igual à do live.py; `live.py` passa a importar daqui na Task 4) e `em_breve(vid)`. Em `main`, no loop de `novos`, antes de montar `linha`: `if v["aba"] == "streams" and em_breve(vid): print(f"AGENDADA {titulo}"); continue`.** Só vídeos que já passaram pelo filtro e pelo dedupe chegam aqui, então é uma requisição por vídeo novo.

- [ ] **Step 4: Rodar `python3 test_sync.py`, esperar `ok`. Commit "sync: live agendada com título de pregação espera o culto".**

---

### Task 4: `live.py` lendo a config

**Files:**
- Create: `live.py` (copiado de origem), `test_live.py`

**Interfaces:**
- Consumes: `pagina`, `capa`, `carregar_env`, `enviar_push`, `http`, `login`, `segmentacao` de `sync.py`; `carregar_igreja`.
- Produces: `ao_vivo(pagina: str)` inalterado; `procurar_live(handle: str)`; `main(cfg: dict, dry: bool)`; `rodar()` inalterado. `--config` default `igreja.json`, `--dry-run`.

- [ ] **Step 1: `test_live.py` (falhando):** portar da origem os asserts de `ao_vivo`, `procurar_live` (agora `live.procurar_live("@X")` com `paginas` chaveado por `"https://www.youtube.com/@X/live"` e `"https://www.youtube.com/@X/streams"`) e de `rodar`. Acrescentar:

```python
chamadas = []
live.http = lambda method, path, body=None, token=None: chamadas.append((method, path)) or {"objects": [], "is_live": False}
live.login = lambda env: ("tok", {"group": None, "subgroup": None})
live.procurar_live = lambda handle: None
live.main({"youtube_handle": "@X", "live": {"canal_inchurch": None}}, dry=True)
assert chamadas == []                      # sem canal configurado, não toca em inchurch_channel
live.main({"youtube_handle": "@X", "live": {"canal_inchurch": 6720}}, dry=True)
assert chamadas == [("GET", "v1/inchurch_channel/6720/")]
```

- [ ] **Step 2: Rodar `python3 test_live.py`, esperar falha.**

- [ ] **Step 3: Generalizar `live.py`:** `LIVE`/`ABA_AO_VIVO` viram f-strings do handle dentro de `procurar_live(handle)`; `CANAL` vira `f"v1/inchurch_channel/{cfg['live']['canal_inchurch']}/"` e todo o bloco liga/desliga só roda se `canal_inchurch` não for `None`; `pagina` importado de `sync`; `main(cfg, dry)` recebe argumentos; `rodar()` faz o `argparse` e chama `main`. Docstring sem Boas Novas.

- [ ] **Step 4: Rodar `python3 test_live.py` e `python3 -m pytest -q`, esperar tudo verde. Commit "live: lê igreja.json; canal da home opcional".**

---

### Task 5: `instalar.py` gera o repo da igreja a partir de `modelo/`

**Files:**
- Create: `instalar.py`, `test_instalar.py`, `modelo/sync.yml`, `modelo/live.yml`, `modelo/README.md`

**Interfaces:**
- Consumes: `carregar_igreja`.
- Produces: `crons(janelas: list[dict]) -> list[str]` e `gerar(config_path: str, destino: str) -> None` em `instalar.py`. CLI: `python3 instalar.py <igreja.json> <pasta-destino>` cria `<destino>/igreja.json` (cópia), `<destino>/README.md`, `<destino>/.github/workflows/sync.yml` e `live.yml`, substituindo em `live.yml` a linha `#CRONS#` pelas linhas `    - cron: "<expr>"` geradas. Não faz git nem gh.

- [ ] **Step 1: `test_instalar.py` (falhando)**

```python
import os, tempfile
from instalar import crons, gerar
assert crons([{"dias": [0], "de": "09:00", "ate": "12:55"}]) == ["*/5 12-15 * * 0"]
assert crons([{"dias": [0, 3], "de": "19:00", "ate": "23:55"}]) == ["*/5 22-23 * * 0,3", "*/5 0-2 * * 1,4"]
assert crons([{"dias": [6], "de": "21:00", "ate": "23:30"}]) == ["*/5 0-2 * * 0"]
assert crons([]) == []
d = tempfile.mkdtemp(); gerar("igreja.exemplo.json", d)
live_yml = open(os.path.join(d, ".github/workflows/live.yml")).read()
assert '- cron: "*/5 12-15 * * 0"' in live_yml and "#CRONS#" not in live_yml and "Lacerdamix/inchurch-sync" in live_yml and "ref: v1" in live_yml
assert os.path.exists(os.path.join(d, "igreja.json")) and os.path.exists(os.path.join(d, ".github/workflows/sync.yml"))
print("ok")
```

Regra de `crons`: BRT = UTC−3 fixo (Brasil não tem horário de verão desde 2019). Converte `de` e `ate` para hora UTC inteira (minuto ignorado; `ate` arredonda para a hora cheia que contém o minuto). Se a faixa não cruza a meia-noite, uma linha; se cruza, uma linha até 23 com os dias originais e outra de 0 até o fim com os dias +1 mod 7. Dias no cron em ordem crescente separados por vírgula.

- [ ] **Step 2: Rodar, esperar falha de import.**

- [ ] **Step 3: Escrever `modelo/sync.yml`:** `on: schedule: - cron: "17 11 * * *"` + `workflow_dispatch` com input `dry_run` (boolean, default false); `concurrency: sync`; job com `actions/checkout@v4` (repo da igreja, path `igreja`), `actions/checkout@v4` com `repository: Lacerdamix/inchurch-sync`, `ref: v1`, path `sync`; step `cp igreja/igreja.json sync/ && cd sync && python3 test_sync.py && python3 sync.py ${{ inputs.dry_run == true && '--dry-run' || '' }}`; env `INCHURCH_EMAIL`/`INCHURCH_PASSWORD` dos secrets. `modelo/live.yml` igual, com `on: schedule:` seguido da linha `#CRONS#`, `concurrency: live`, `timeout-minutes: 5`, rodando `python3 live.py`. `modelo/README.md`: três linhas dizendo que o repo só tem config, o código vem de `Lacerdamix/inchurch-sync`, e como rodar à mão (`gh workflow run sync.yml`).

- [ ] **Step 4: Implementar `crons` e `gerar` em `instalar.py`.**

- [ ] **Step 5: Rodar `python3 test_instalar.py`, esperar `ok`. Commit "instalar.py: gera o repo da igreja com cron da live calculado".**

---

### Task 6: Plugin: manifesto, comando e skill

**Files:**
- Create: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `commands/instalar.md`, `skills/instalar/SKILL.md`

**Interfaces:**
- Consumes: `python3 ${CLAUDE_PLUGIN_ROOT}/sync.py --canal <handle>` (Task 2), `python3 ${CLAUDE_PLUGIN_ROOT}/instalar.py <json> <destino>` (Task 5).

- [ ] **Step 1: `plugin.json`:** `{"name": "inchurch-sync", "version": "1.0.0", "description": "Publica as pregações do YouTube e avisa a live no app InChurch da sua igreja", "author": {"name": "Lacerdamix"}}`. `marketplace.json`: `{"name": "inchurch-sync", "owner": {"name": "Lacerdamix"}, "plugins": [{"name": "inchurch-sync", "source": "./", "description": <mesma>}]}`. Se `claude plugin validate .` existir nesta versão do Claude Code, rodar e corrigir o que apontar; senão, `python3 -c "import json;json.load(open('.claude-plugin/plugin.json'));json.load(open('.claude-plugin/marketplace.json'))"`.

- [ ] **Step 2: `commands/instalar.md`:** frontmatter `description: Instala o inchurch-sync para a sua igreja`, corpo "Use a skill `inchurch-sync:instalar` e siga os passos dela do início. $ARGUMENTS".

- [ ] **Step 3: `skills/instalar/SKILL.md`** com frontmatter `name: instalar`, `description: Use quando o usuário pedir para instalar, configurar, testar, mudar horário ou atualizar o inchurch-sync da igreja dele` e o corpo com os 7 passos da seção "O que a skill faz" do design, escritos como instruções ao agente, em português, com os comandos exatos:
  - Passo 1: `python3 --version`; `gh auth status`. Se faltar, link oficial de instalação e parar.
  - Passo 2: a entrevista, uma pergunta por vez, na ordem do design. Para o padrão de título: pedir 2 ou 3 títulos reais, propor `separador`/`campos`, confirmar. Para o canal: `python3 "${CLAUDE_PLUGIN_ROOT}/sync.py" --canal <handle>` para obter `youtube_channel_id`.
  - Passo 3: gravar `igreja.json` em `~/inchurch-sync-<slug>/` e rodar `python3 "${CLAUDE_PLUGIN_ROOT}/instalar.py" igreja.json .` dentro dela.
  - Passo 4: `git init && git add -A && git commit -m "inchurch-sync: configuração inicial"`, `gh repo create inchurch-sync-<slug> --private --source . --push`, `gh secret set INCHURCH_EMAIL --body "<email>"`. Em seguida mostrar ao cliente, para ele digitar no terminal dele: `gh secret set INCHURCH_PASSWORD --repo <owner>/inchurch-sync-<slug>` (explicar que a senha fica oculta e não passa pelo Claude). Só continuar quando `gh secret list` listar os dois.
  - Passo 5: `gh workflow run sync.yml -f dry_run=true`, `gh run watch` no run mais recente, mostrar as linhas que começam por data (o que seria publicado) e pedir OK.
  - Passo 6: `gh workflow run sync.yml` real, acompanhar, mostrar resultado.
  - Passo 7: texto de fechamento (o que roda quando, `gh run list`, aviso de que o Actions atrasa e pode não disparar, VPS como próximo passo).
  - Seção `atualizar`: `python3 "${CLAUDE_PLUGIN_ROOT}/instalar.py" igreja.json .` de novo na pasta da igreja, commit, push.
  - Seção "mudar horário": editar `live.janelas` no `igreja.json`, rodar `atualizar`.

- [ ] **Step 4: Verificação manual:** `claude --plugin-dir /Users/LacerdaMix/GitHub/inchurch-sync` (ou o equivalente desta versão) numa pasta vazia; `/inchurch-sync:instalar` deve aparecer e carregar a skill. Registrar no commit se o comando foi encontrado.

- [ ] **Step 5: Commit "plugin: manifesto, comando /inchurch-sync:instalar e skill de instalação".**

---

### Task 7: README, validação com a Boas Novas e publicação

**Files:**
- Create: `README.md`
- Verify: tudo

- [ ] **Step 1: `README.md`:** logo `docs/img/inchurch-logo.png` no topo, título "inchurch-sync", linha "Em parceria com a InChurch", o que faz (duas frases), bloco de instalação:

```
/plugin marketplace add Lacerdamix/inchurch-sync
/plugin install inchurch-sync
```

seguido de "depois escreva `instalar`". Seção "Importante: o GitHub Actions é paliativo" com o texto do design (atrasa horas, às vezes não dispara; VPS é o caminho confiável). Seção "Instalação manual (sem Claude Code)" repetindo os passos 2 a 6 da skill em linguagem humana. Seção "Configuração" com a tabela dos campos do `igreja.json`.

- [ ] **Step 2: Validação ponta a ponta com a Boas Novas como se fosse cliente.** Criar `/private/tmp/claude-501/.../scratchpad/bn/igreja.json` a partir dos valores da Boas Novas (handle `@BoasNovasChurch`, channel id `UC3P8FkGwOQnCHWo8J4HrpXA`, `desde 2026-01-01`, `cultos_genericos` do `GENERICO`, `series_por_prefixo {"CONF": "CONFERÊNCIA"}`, `canal_inchurch 6720`, janelas do `docker-compose.yml`). Com o `.env` do repo de origem exportado no ambiente, rodar:

```
python3 sync.py --dry-run --config <scratchpad>/bn/igreja.json
python3 live.py --dry-run --config <scratchpad>/bn/igreja.json
python3 instalar.py <scratchpad>/bn/igreja.json <scratchpad>/bn/repo
```

Esperado: o dry-run do sync lista as mesmas pregações novas que `python3 sync.py --dry-run` no repo de origem (comparar as duas saídas; diferença aceitável só nos vídeos de `SERIES_MANUAIS`, que não existem mais); `live.py` imprime "Sem live no ar" ou a live; `live.yml` gerado tem as linhas `*/5 12-15 * * 0`, `*/5 22-23 * * 0,3,4`, `*/5 0-2 * * 1,4,5`.

- [ ] **Step 3: `python3 -m pytest -q` verde. Commit "README e validação com a Boas Novas".**

- [ ] **Step 4: Publicar:** `gh repo create Lacerdamix/inchurch-sync --public --source . --push`, `git tag v1 && git push origin v1`. Depois, numa pasta vazia, `claude` e os dois comandos do README; `instalar` deve carregar a skill. Reportar o resultado.

---

## Self-review

- Cobertura do spec: repo público e plugin (T6, T7), repo fino da igreja com checkout em `v1` (T5), `igreja.json` com todos os campos (T1, T2, T4), filtro de pregação configurável (T2), live agendada (T3), senha pelo terminal (T6 passo 4), dry_run no Actions (T5, T6), `atualizar` (T6), aviso de paliativo (T7), logo e parceria (T7). Tenant de teste: fora do código; T7 passo 2 é o piloto com a Boas Novas.
- Nomes consistentes: `carregar_igreja`, `parse(titulo, aba, cfg)`, `rss(aba, channel_id)`, `descobrir_canal`, `em_breve`, `pagina`, `procurar_live(handle)`, `main(cfg, dry)`, `crons`, `gerar`.
- Review Focus 1–5 têm teste em T2, T2, T3, T5, T1.
