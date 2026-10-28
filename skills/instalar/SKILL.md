---
name: instalar
description: Use quando o usuário pedir para instalar, configurar, testar, mudar horário ou atualizar o inchurch-sync da igreja dele (publicar pregações do YouTube como Palavras no app InChurch e mandar push quando a live começa).
---

# inchurch-sync: instalação guiada

Quem fala com você é, quase sempre, alguém da equipe de mídia ou secretaria de uma igreja, sem experiência com programação. Fale português simples, uma pergunta por vez, sem jargão (diga "repositório no GitHub" no máximo uma vez e explique; nunca diga "cron", "secret", "YAML", "workflow" sem traduzir). Você executa os comandos; a pessoa só responde e, em dois momentos, digita algo no Terminal dela.

**Pasta do plugin (`PLUGIN`)**: `${CLAUDE_PLUGIN_ROOT}`. Se essa variável não estiver preenchida, é a pasta dois níveis acima do diretório base desta skill (onde ficam `sync.py`, `live.py`, `instalar.py`). Use o caminho absoluto, entre aspas.

**Regra de ouro sobre a senha**: a senha do painel InChurch nunca é digitada nesta conversa nem gravada em arquivo. Se a pessoa colar a senha aqui, avise que ela deve trocá-la no painel depois, e siga sem usá-la.

Escolha o fluxo pelo pedido: **instalar** (padrão), **testar**, **configurar / mudar horário**, **atualizar**.

---

## Instalar

### 1. Conferir o computador

Rode `python3 --version`, `git --version`, `gh --version` e `gh auth status`.

- Falta `python3` ou `git` no Mac: peça para rodar `xcode-select --install` no Terminal. No Windows: `winget install Python.Python.3.12 Git.Git`.
- Falta `gh`: Mac `brew install gh` (sem Homebrew: baixar em https://cli.github.com), Windows `winget install --id GitHub.cli`.
- `gh auth status` diz que não está logado: peça para a pessoa abrir o **Terminal** (Mac: Cmd+Espaço, digitar "Terminal"; Windows: menu Iniciar, "PowerShell") e rodar `gh auth login`, escolhendo GitHub.com, HTTPS e "Login with a web browser". Quem não tem conta no GitHub cria uma em https://github.com/signup antes.
- Se `gh auth status` não listar o escopo `workflow`, peça para rodar no Terminal `gh auth refresh -s workflow`.

Só siga quando os quatro comandos funcionarem.

### 2. Entrevista (uma pergunta por mensagem)

1. **Nome da igreja**, como deve aparecer como autor quando o vídeo não diz quem pregou.
2. **Canal do YouTube**: o link ou o @. Rode `python3 "PLUGIN/sync.py" --canal @Handle` para obter o id (começa com `UC`). Se falhar, peça o link de qualquer vídeo do canal e tente de novo pelo @ que aparece embaixo do vídeo.
3. **Como são os títulos**: baixe os títulos recentes você mesmo, sem perguntar:
   `curl -s "https://www.youtube.com/feeds/videos.xml?playlist_id=UULV<id sem o UC>"` (lives) e `...UULF<id sem o UC>` (vídeos). Mostre 5 a 10 títulos de cada e proponha:
   - `titulo.separador` (o caractere entre as partes, ex. `|` ou `-`);
   - `titulo.campos`, a ordem das partes: `titulo`, `pregador`, `serie` (só as que existem);
   - `prefixos_pregador`, como escrevem quem prega (`PR`, `PRA`, `PASTOR`, `BISPO`, `AP`, ...);
   - `cultos_genericos`, os nomes que aparecem quando a live ainda não foi renomeada (`CULTO`, `DOMINGO`, `SANTA CEIA`, ...). Pergunte: "quando a live vai ao ar, antes de vocês mudarem o título, como ela se chama?";
   - `series_por_prefixo` só se houver um padrão claro tipo `CONF. NOME DO EVENTO` (ex. `{"CONF": "CONFERÊNCIA"}`); senão `{}`.
   Explique a regra em uma frase: "da aba Ao vivo entra tudo que não tiver nome genérico; da aba Vídeos só entra o que tiver pregador ou série, assim música e podcast ficam de fora". Confirme.
4. **Dias e horários dos cultos transmitidos** (ex.: "domingo 10h e 19h, quarta 20h"). Proponha `live.janelas` começando 1 hora antes e terminando 3 horas depois do início (no máximo `23:55`, a janela não pode passar da meia-noite). Dias: 0 = domingo ... 6 = sábado. Confirme.
5. **Desde quando publicar**: sugira a data de 7 dias atrás. Explique que o YouTube só mostra os vídeos mais recentes, então não dá para trazer o histórico inteiro, e que só o mais recente gera notificação.
6. **Destaques**: quantas Palavras recentes ficam em destaque no app (padrão 3; 0 = não mexer nos destaques).
7. **Canal "ao vivo" da home do app** (opcional): "No painel da InChurch, em Programação > Canais, vocês têm um canal que aparece na home quando estão ao vivo? Se sim, abra ele e me diga o número no fim do endereço (ex.: …/detalhe/6720)". Sem isso, `canal_inchurch` fica `null` e só o push da live é enviado.
8. **E-mail** de login do painel InChurch (só o e-mail).

### 3. Montar a pasta e conferir

- Pasta: `~/inchurch-sync-<slug>`, onde `<slug>` é o nome da igreja em minúsculas, sem acento, com hífens.
- Grave `igreja.json` nela com os campos da entrevista (`nome`, `youtube_handle`, `youtube_channel_id`, `desde` em `AAAA-MM-DD`, `destaques`, `cultos_genericos`, `prefixos_pregador`, `titulo`, `series_por_prefixo`, `live`). Modelo: `PLUGIN/igreja.exemplo.json`.
- Rode, dentro da pasta, `python3 "PLUGIN/instalar.py" igreja.json .`. Ele valida o arquivo, cria os agendamentos e mostra a estimativa de minutos do GitHub Actions por mês. Se passar de 1.800, avise que o plano gratuito tem 2.000 minutos por mês em repositório privado e proponha encurtar as janelas.
- Prévia sem senha: `python3 "PLUGIN/sync.py" --dry-run --config igreja.json`. Mostre as linhas com data (é o que seria publicado, sem ainda checar o que já está no app). Se algo estiver errado (música entrando, pregação ficando de fora, autor errado), ajuste `igreja.json` e repita.

### 4. Criar o repositório e guardar o login

Explique: "vou criar um repositório privado no seu GitHub. É ali que ficam os agendamentos; o GitHub roda tudo sozinho, seu computador pode ficar desligado".

```
git init -q && git add -A && git commit -qm "inchurch-sync: configuração inicial"
gh repo create inchurch-sync-<slug> --private --source . --push
gh secret set INCHURCH_EMAIL --body "<email>"
```

Agora a senha. Mostre o comando abaixo (com o `<dono>` preenchido; descubra com `gh api user -q .login`) e peça para a pessoa colar **no Terminal**, apertar Enter e digitar a senha do painel quando ele pedir (os caracteres não aparecem enquanto digita, é normal):

```
gh secret set INCHURCH_PASSWORD --repo <dono>/inchurch-sync-<slug>
```

Espere a pessoa dizer que fez e confira com `gh secret list`. Só siga quando aparecerem `INCHURCH_EMAIL` e `INCHURCH_PASSWORD`.

### 5. Primeira execução, só mostrando

```
gh workflow run sync.yml -f dry_run=true
```

Se disser que não achou o workflow, espere 10 segundos e tente de novo. Pegue o id com `gh run list --workflow sync.yml --limit 1 --json databaseId -q '.[0].databaseId'`, acompanhe com `gh run watch <id> --exit-status` e leia o resultado com `gh run view <id> --log`. Mostre à pessoa as linhas com data (o que seria publicado agora, já descontando o que está no app). Se o login falhar, a senha ou o e-mail estão errados: repita o passo da senha.

Pergunte se pode publicar de verdade.

### 6. Primeira execução de verdade

`gh workflow run sync.yml`, acompanhe do mesmo jeito e mostre o que foi publicado. Rode também `gh workflow run live.yml -f dry_run=true` e confirme que terminou sem erro ("Sem live no ar" é o normal fora do culto).

### 7. Encerrar

Diga, em poucas linhas:
- As pregações novas entram todo dia por volta das 8h; a Palavra mais nova gera uma notificação.
- Nos horários de culto, a cada 5 minutos o GitHub confere se a live começou e manda "🔴 Estamos ao vivo!".
- **O GitHub Actions é um paliativo**: o agendamento costuma atrasar (às vezes horas) e de vez em quando não dispara. Para o aviso da live chegar na hora, o caminho confiável é rodar num servidor próprio (VPS); fale com quem instalou se quiser isso.
- Para conferir: `gh run list` na pasta, ou a aba Actions do repositório no GitHub.
- Para mudar algo depois: abrir o Claude Code e pedir "mudar horário", "configurar" ou "testar".

---

## Testar

Na pasta da igreja (procure `~/inchurch-sync-*`; se houver mais de uma ou nenhuma, pergunte qual): `gh workflow run sync.yml -f dry_run=true` e `gh workflow run live.yml -f dry_run=true`, acompanhe e mostre o resultado como no passo 5.

## Configurar / mudar horário

Na pasta da igreja, pergunte só o que a pessoa quer mudar, edite `igreja.json`, rode `python3 "PLUGIN/sync.py" --dry-run --config igreja.json` se mexeu em títulos, e siga para **Atualizar**.

## Atualizar

Na pasta da igreja:

```
python3 "PLUGIN/instalar.py" igreja.json .
git add -A && git commit -qm "inchurch-sync: atualiza configuração" && git push
```

Se `git commit` disser que não há nada para commitar, já estava atualizado. Correções do código chegam sozinhas (o GitHub baixa a versão `v1` a cada execução); isto só é preciso quando a configuração ou os agendamentos mudam, ou depois de `/plugin update`.
