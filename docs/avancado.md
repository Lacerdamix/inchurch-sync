# inchurch-sync: para quem é técnico

Quem só quer instalar não precisa ler esta página: o [README](../README.md) basta.

## Como funciona

A instalação cria um repositório privado no seu GitHub, `inchurch-sync-<sua-igreja>`, com apenas a configuração (`igreja.json`) e os dois agendamentos. A cada execução, o GitHub baixa o código deste repositório na versão `v1`, então correções chegam sozinhas, sem reinstalar.

- **Pregações** (`sync.py`): uma vez por dia, lê as abas Vídeos e Ao vivo do canal. Da aba Ao vivo entra todo culto que já tem título de pregação. Da aba Vídeos só entra o que tem pregador ou série no título, para música e podcast ficarem de fora. Live agendada espera o culto acontecer.
- **Live** (`live.py`): a cada 5 minutos nos horários de culto, confere se o canal está ao vivo e manda o push uma vez por live. Opcionalmente liga o canal "ao vivo" na home do app.

## Configuração (`igreja.json`)

A instalação preenche tudo. Para referência, veja [`igreja.exemplo.json`](../igreja.exemplo.json).

| Campo | O que é |
|---|---|
| `nome` | Nome da igreja. Vira o autor quando o título não diz quem pregou. |
| `youtube_handle`, `youtube_channel_id` | O canal do YouTube (`@SuaIgreja` e o id que começa com `UC`). |
| `desde` | Data a partir da qual as pregações são publicadas (`AAAA-MM-DD`). |
| `destaques` | Quantas Palavras recentes ficam em destaque no app. `0` não mexe. |
| `titulo` | Como os títulos são escritos: `separador` (ex. `\|`) e a ordem dos `campos` (`titulo` sempre; `pregador` e `serie` se houver). A parte `serie` vira a série da Palavra. |
| `prefixos_pregador` | Como vocês escrevem quem prega: `PR`, `PRA`, `PASTOR`, `BISPO`... |
| `cultos_genericos` | Nomes de live ainda não renomeada (`CULTO`, `DOMINGO`...). Essas não são publicadas. |
| `series_por_prefixo` | Opcional. Ex.: `{"CONF": "CONFERÊNCIA"}` faz `\| CONF. JOVENS 2026` virar a série "CONFERÊNCIA JOVENS 2026". |
| `live.janelas` | Dias (0 = domingo) e horários, em Brasília, em que o aviso de live fica ligado. |
| `live.canal_inchurch` | Opcional. Número do canal da home do app que deve ficar "ao vivo" durante a live. |

## Instalação sem o Claude Code

1. Instale `python3`, `git` e o [GitHub CLI](https://cli.github.com), e rode `gh auth login`.
2. Copie `igreja.exemplo.json` para uma pasta nova como `igreja.json` e preencha. Para achar o id do canal: `python3 sync.py --canal @SuaIgreja`.
3. Confira o que seria publicado: `python3 sync.py --dry-run --config igreja.json`.
4. Gere a pasta: `python3 instalar.py igreja.json <pasta>`.
5. Na pasta: `git init`, `git add -A`, `git commit -m inicial`, `gh repo create inchurch-sync-<igreja> --private --source . --push`.
6. Guarde o login: `gh secret set INCHURCH_EMAIL` e `gh secret set INCHURCH_PASSWORD`.
7. Teste: `gh workflow run sync.yml -f dry_run=true` e veja com `gh run list`.

## Rodar numa máquina própria (computador antigo ou VPS)

Para o aviso de live chegar na hora, rode os scripts fora do GitHub Actions, em qualquer máquina sempre ligada com `python3`: um computador antigo da igreja ou uma VPS. Clone este repositório e ponha na pasta o `igreja.json` e um arquivo `.env` com duas linhas, `INCHURCH_EMAIL=...` e `INCHURCH_PASSWORD=...` (os scripts leem esse arquivo; ele já está no `.gitignore`). Agende `python3 live.py` a cada 5 minutos e `python3 sync.py` uma vez por dia (cron no Linux e no Mac, Agendador de Tarefas no Windows). O `live.py` pode rodar o dia inteiro: fora do culto ele só responde "Sem live no ar". No computador antigo, desligue a suspensão automática.

Depois desative os agendamentos do repositório da igreja no GitHub (aba Actions), para não rodar nos dois lugares. O app continua sendo o controle do que já foi publicado e avisado, mas duas execuções no mesmo instante poderiam mandar o aviso de live em dobro.

## Desenvolvimento

Só Python 3 com a biblioteca padrão. Testes: `for t in test_*.py; do python3 "$t"; done`.
