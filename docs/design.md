# inchurch-sync como produto: desenho

Data: 2026-10-28. Origem: repo "Auto youtube add" (automações da Boas Novas). Destino: repo novo e público `Lacerdamix/inchurch-sync`, que é ao mesmo tempo plugin do Claude Code (marketplace) e fonte dos scripts que as igrejas executam.

## Intenção

Entregar a outras igrejas que usam o app InChurch duas automações que já rodam há meses na Boas Novas: publicar as pregações do YouTube como Palavras e mandar push quando a live começa. O cliente é leigo: instala o Claude Code, roda dois comandos de plugin, escreve `instalar`, responde perguntas e sai com tudo rodando no GitHub dele.

## Objetivos

- Leigo instala sozinho em uma sessão de Claude Code, sem editar arquivo, abrir o GitHub na mão nem clonar nada.
- Pregações novas do canal da igreja viram Palavra no app, deduplicadas contra a própria InChurch, com push "Nova Palavra" para a mais recente de cada execução.
- Push "Estamos ao vivo" quando a live entra no ar, uma vez por live.
- Configuração por igreja: canal, data de corte, nomes de culto, padrão de título, destaques, dias e horários de live.
- Correção nos scripts chega a todas as igrejas sem reinstalar: o repo da igreja baixa os scripts do repo público a cada execução.

## Não objetivos

- Banners, banner da semana, eventos recorrentes, comandos de WhatsApp, Telegram, VPS, Docker. Nada disso entra.
- Garantir pontualidade no Actions. README e skill dizem, com todas as letras, que o GitHub Actions é paliativo: o cron atrasa horas e às vezes não dispara. A VPS é o caminho confiável e fica como "próximo passo", sem código no repo.
- Documentar a API de admin da InChurch (inradar) como se fosse pública. A parceria com a InChurch cobre o uso; o README não precisa escondê-la, mas também não a promove.
- Retroativo (yt-dlp). Fora. A data de corte resolve o começo.
- Funcionar em outros agentes além do Claude Code (o formato plugin é do Claude Code; o README traz o passo a passo manual para quem não usa agente).

## Anti-objetivos (fracasso mesmo funcionando)

- Publicar a mesma pregação duas vezes ou mandar push duplicado da live.
- Publicar música, podcast ou clipe como Palavra.
- Pedir ao leigo que crie secret, edite YAML ou entenda cron.
- Deixar o cliente achar que a live vai avisar na hora, sem ter lido que o Actions atrasa.
- Quebrar todas as igrejas de uma vez com um push ruim no repo público (ver "versão fixada").

## Restrições

- Python 3 só com stdlib (igual ao repo atual). Sem pip install.
- `gh` logado no cliente. A skill detecta, orienta a instalar e a rodar `gh auth login`, e só segue depois.
- Repo criado no GitHub do cliente é privado (tem e-mail da igreja na config; a senha vai só em secret).
- Português do Brasil em tudo que o cliente lê.

## Forma do repo público `inchurch-sync`

```
inchurch-sync/
  .claude-plugin/plugin.json          # nome inchurch-sync, versão, descrição
  .claude-plugin/marketplace.json     # para /plugin marketplace add Lacerdamix/inchurch-sync
  skills/instalar/SKILL.md            # a entrevista e a instalação (detalhe abaixo)
  commands/instalar.md                # /inchurch-sync:instalar -> invoca a skill
  README.md                           # o que é, os dois comandos de instalação, aviso do Actions como paliativo, passo a passo manual
  sync.py                             # pregações -> Palavra (derivado do atual, lê igreja.json)
  live.py                             # push da live (derivado do atual, lê igreja.json)
  test_sync.py                        # testes de hoje adaptados ao json
  igreja.exemplo.json                 # modelo da config
  modelo/                             # o que vai para o repo da igreja
    sync.yml
    live.yml
    README.md                         # curto: "este repo é só config; o código vem de Lacerdamix/inchurch-sync"
  docs/design.md                      # este arquivo
  docs/img/inchurch-logo.png          # logo da InChurch, no topo do README (fornecido pelo usuário)
```

Identidade visual: o README abre com o logo da InChurch (verde `#6CD72B` e cinza `#4A4A4A`, tirados do logo). É uma parceria: a InChurch divulga o vídeo de lançamento nas redes oficiais, então o README apresenta como "em parceria com a InChurch" e o texto pode citar a InChurch abertamente. Vale pedir à InChurch um tenant de teste para a validação (ver perguntas em aberto).

## Forma do repo da igreja (gerado pela skill)

```
inchurch-sync-<slug>/
  igreja.json
  README.md
  .github/workflows/sync.yml
  .github/workflows/live.yml
```

Cada workflow faz `actions/checkout` do repo da igreja e um segundo `actions/checkout` de `Lacerdamix/inchurch-sync` numa tag fixa (`v1`), copia `igreja.json` para junto dos scripts e roda `python3 sync.py` ou `python3 live.py`. Secrets `INCHURCH_EMAIL` e `INCHURCH_PASSWORD`. Os dois workflows aceitam `workflow_dispatch` com entrada `dry_run` (padrão falso) para a primeira execução assistida.

**Versão fixada:** o workflow aponta para a tag `v1`, movível (o produto move a tag quando publica correção testada), não para `main`. Um commit ruim na `main` não derruba ninguém; mover a tag é o ato explícito de "liberar para todos". Quebra de compatibilidade do `igreja.json` vira `v2`, e a skill (via `/plugin update`) migra a igreja quando pedirem `atualizar`.

## igreja.json

```json
{
  "nome": "Igreja X",
  "youtube_handle": "@IgrejaX",
  "youtube_channel_id": "UCxxxxxxxxxxxxxxxxxxxxxx",
  "desde": "2026-01-01",
  "destaques": 3,
  "cultos_genericos": ["CULTO", "SANTA CEIA", "DOMINGO", "QUARTA"],
  "prefixos_pregador": ["PR", "PRA", "PASTOR", "PASTORA", "AP", "BISPO"],
  "titulo": {"separador": "|", "campos": ["titulo", "pregador", "serie"]},
  "series_por_prefixo": {"CONF": true},
  "live": {"canal_inchurch": null, "janelas": [{"dias": [0], "de": "09:00", "ate": "12:55"}, {"dias": [0, 3], "de": "19:00", "ate": "23:55"}]}
}
```

- `cultos_genericos`: prefixos que marcam vídeo sem pregador no título (o `GENERICO` atual vira lista).
- `prefixos_pregador`: substitui a regex `PASTOR` atual. Regra de "isto é pregação", igual à de hoje, só que configurável: da aba Ao vivo entra tudo que passa pela data de corte; da aba Vídeos só entra se o campo `pregador` começa com um desses prefixos ou se há série por prefixo (congresso). É o que barra música, podcast e clipe em canal misto. Título sem separador na aba Ao vivo é publicado com autor = nome da igreja; na aba Vídeos é ignorado.
- `titulo`: como a igreja escreve o título. `campos` é a ordem; qualquer campo pode faltar. Sem `pregador`, autor = nome da igreja. Sem `serie`, Palavra fica sem série.
- `series_por_prefixo`: opcional; mantido porque o parse de "CONF. NOME" já existe. Default vazio.
- `live.canal_inchurch`: id do canal InChurch para ligar o "ao vivo agora" na home. Opcional; `null` pula o PATCH.
- `live.janelas`: viram as linhas `cron` do `live.yml` (a skill converte BRT para UTC). Dias: 0 = domingo, como no cron.

## O que a skill faz (skills/instalar/SKILL.md)

Gatilhos: "instalar", "configurar", "testar", "mudar horário", "atualizar", `/inchurch-sync:instalar`.

1. Checa `python3` e `gh auth status`. Falta algo: explica como instalar (link oficial) e para.
2. Entrevista, uma pergunta por vez, em linguagem de leigo: nome da igreja, link do canal, dias e horários dos cultos com transmissão, como ficam os títulos dos vídeos (pede dois ou três exemplos reais e deduz separador e ordem, confirmando), como escrevem o nome de quem prega ("Pr.", "Bispo", ...), nomes comuns de culto que não são tema, desde quando publicar, quantos destaques, e-mail do painel InChurch.
3. Cria a pasta local do repo da igreja a partir de `modelo/`, grava `igreja.json`, reescreve o cron do `live.yml` a partir das janelas.
4. `gh repo create <nome> --private --source . --push`, `gh secret set INCHURCH_EMAIL`. A senha o cliente digita no terminal dele com `gh secret set INCHURCH_PASSWORD` (ver "Decididas na aprovação").
5. Dispara `gh workflow run sync.yml -f dry_run=true`, acompanha e mostra ao cliente o que seria publicado (lista de títulos e autores). Pede OK.
6. Dispara `gh workflow run sync.yml` de verdade, acompanha, mostra o resultado.
7. Fecha explicando: o que roda quando, onde ver os logs (`gh run list`), que o Actions atrasa e pode falhar em disparar, e que a VPS é o próximo passo se quiserem pontualidade.

`atualizar`: reaplica `modelo/` sobre o repo da igreja preservando `igreja.json`, migra o json se a versão exigir, faz commit e push.

O README do repo público repete os passos 2 a 6 em versão humana para quem instala sem agente.

## Decisões já tomadas (do usuário)

- Só Actions nesta versão, dito como paliativo.
- Só pregações e live.
- Entrevista pergunta dias de live e nomes comuns de cultos; o parse é da igreja, não o da Boas Novas.
- Formato plugin do Claude Code, repo público; o leigo precisa conseguir instalar e executar.

## Decisões minhas (podem ser revertidas)

- Repo da igreja fino (só config e workflows); scripts vêm do repo público em tag `v1` movível.
- Skill assume `gh` e ensina a instalar. Alternativa (gerar arquivos e o cliente sobe) descartada porque obriga o leigo a mexer em secrets.
- Filtro de pregação igual ao atual, com os prefixos de pregador configuráveis (`prefixos_pregador`), em vez de publicar tudo com separador.
- Primeira execução é sempre `dry_run` no Actions, com OK do cliente antes da real. Nenhum dry-run local, para a credencial não precisar existir na máquina do cliente.
- Config em um único `igreja.json` na raiz, commitado. Senha em secret, nunca no json.
- `live.canal_inchurch` opcional, default `null`.
- Push "Nova Palavra" fica, com texto fixo em português, igual ao atual.
- Regra dos N destaques fica, com N configurável (0 desliga).
- Nome do repo gerado: `inchurch-sync-<slug do nome da igreja>`.
- Os scripts nascem copiando `sync.py`, `live.py` e `test_sync.py` do repo atual e generalizando, não reescrevendo do zero. O repo atual da Boas Novas não muda.

## Decididas na aprovação (2026-10-28, recomendações aceitas por "quer aplicar o plano?")

- Senha do painel nunca passa pelo agente: a skill mostra o comando `gh secret set INCHURCH_PASSWORD --repo <igreja>` e pede que o cliente digite no terminal dele (digitação oculta), e só segue quando `gh secret list` mostrar o secret. O e-mail pode ir pelo chat.
- Live agendada: antes de publicar um vídeo novo da aba Ao vivo, `sync.py` abre a página do vídeo e pula se for "em breve" (`isUpcoming`/`"isLiveNow":false` com `liveBroadcastDetails` sem fim). Uma requisição a mais por vídeo novo, só para os que passariam pelo filtro.
- Tenant de teste: pedir à InChurch, dentro da parceria. Enquanto não houver, a primeira igreja real é piloto assistido (o `dry_run` do passo 5 já cobre a parte de publicação; o push da live é testado numa live real com o cliente avisado).

## Fica a critério do construtor

- Como deduzir separador e ordem dos campos a partir de exemplos de título (pode ser pergunta direta na entrevista se a dedução ficar frágil).
- Formato exato do `igreja.exemplo.json`, do `plugin.json` e das mensagens da entrevista.
- Se o `sync.py` valida o json ao iniciar e como reporta erro para leigo.
- Como a skill converte janelas BRT em cron UTC (a janela 19:00–23:55 BRT cruza a meia-noite UTC).
- Como o script localiza o `igreja.json` (argumento `--config` com default `./igreja.json`).
- Descoberta do channel ID a partir do handle, `INCHURCH_APP_ID` quando o e-mail tem mais de um app, se `atualizar_capas` continua, janela de live que estoura o `ate`, criação de série a partir do campo `serie`.
