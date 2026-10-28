<p align="center">
  <img src="docs/img/inchurch-logo.png" alt="InChurch" width="420">
</p>

<h1 align="center">inchurch-sync</h1>

<p align="center"><b>As pregações do YouTube da sua igreja no app InChurch, sozinhas.</b><br>Em parceria com a InChurch.</p>

---

O inchurch-sync faz duas coisas pela sua equipe de mídia:

- **Pregações viram Palavras.** Todo dia, as pregações novas do canal da igreja no YouTube são publicadas como Palavras no app, com título, pregador, capa e resumo. A mais recente gera uma notificação "🙌 Nova Palavra no app".
- **Aviso de live.** Nos horários de culto, quando a transmissão começa, todo mundo com o app recebe "🔴 Estamos ao vivo!".

Nada é publicado duas vezes: o próprio app é a referência do que já foi.

## O que você precisa

- Um computador Mac ou Windows, só para a instalação (depois pode ficar desligado).
- O [Claude Code](https://claude.com/claude-code) instalado.
- Uma conta no [GitHub](https://github.com/signup), gratuita.
- O e-mail e a senha de quem acessa o painel da InChurch da igreja.

## Instalação

Abra o Claude Code e digite:

```
/plugin marketplace add Lacerdamix/inchurch-sync
/plugin install inchurch-sync
```

Depois escreva **`instalar`**. O Claude conversa com você: pergunta o canal do YouTube, olha os títulos dos seus vídeos, pergunta os dias e horários dos cultos e o e-mail do painel. Ele monta tudo, mostra o que seria publicado e só publica depois do seu OK.

A senha do painel você digita uma única vez, no Terminal do seu computador, quando o Claude pedir. Ela vai direto para o cofre do GitHub e não passa pela conversa.

Para mudar algo depois, abra o Claude Code e peça **"mudar horário"**, **"configurar"** ou **"testar"**.

## Importante: o GitHub Actions é um paliativo

A instalação usa o GitHub Actions, o agendador gratuito do GitHub, para não precisar de servidor. Ele funciona, mas **não é pontual**: o agendamento costuma atrasar, às vezes por horas, e de vez em quando não dispara.

- Para as **pregações**, isso quase não importa: se atrasar, a Palavra entra mais tarde no mesmo dia.
- Para o **aviso de live**, o push pode chegar atrasado ou não chegar.

Se a igreja quiser o aviso na hora, o caminho confiável é rodar os mesmos scripts num servidor próprio (VPS) com agendamento a cada 5 minutos.

O plano gratuito do GitHub dá 2.000 minutos por mês em repositório privado. A instalação mostra a estimativa para os seus horários; uma igreja com três cultos por semana fica perto de 800.

## Como funciona

A instalação cria um repositório privado no seu GitHub, `inchurch-sync-<sua-igreja>`, com apenas a configuração (`igreja.json`) e os dois agendamentos. A cada execução, o GitHub baixa o código deste repositório na versão `v1`, então correções chegam sozinhas, sem reinstalar.

- **Pregações** (`sync.py`): uma vez por dia, lê as abas Vídeos e Ao vivo do canal. Da aba Ao vivo entra todo culto que já tem título de pregação. Da aba Vídeos só entra o que tem pregador ou série no título, para música e podcast ficarem de fora. Live agendada espera o culto acontecer.
- **Live** (`live.py`): a cada 5 minutos nos horários de culto, confere se o canal está ao vivo e manda o push uma vez por live. Opcionalmente liga o canal "ao vivo" na home do app.

## Configuração (`igreja.json`)

A instalação preenche tudo. Para referência, veja [`igreja.exemplo.json`](igreja.exemplo.json).

| Campo | O que é |
|---|---|
| `nome` | Nome da igreja. Vira o autor quando o título não diz quem pregou. |
| `youtube_handle`, `youtube_channel_id` | O canal do YouTube (`@SuaIgreja` e o id que começa com `UC`). |
| `desde` | Data a partir da qual as pregações são publicadas (`AAAA-MM-DD`). |
| `destaques` | Quantas Palavras recentes ficam em destaque no app. `0` não mexe. |
| `titulo` | Como os títulos são escritos: `separador` (ex. `\|`) e a ordem dos `campos` (`titulo`, `pregador`, `serie`). |
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

## Desenvolvimento

Só Python 3 com a biblioteca padrão. Testes: `for t in test_*.py; do python3 "$t"; done`.
