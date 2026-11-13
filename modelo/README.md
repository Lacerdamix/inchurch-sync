# inchurch-sync · {{NOME}}

Este repositório só guarda a configuração da {{NOME}} (`igreja.json`) e os agendamentos do GitHub Actions.
O código vem de [Lacerdamix/inchurch-sync](https://github.com/Lacerdamix/inchurch-sync) a cada execução.

- **Pregações:** todo dia por volta das 8h17, as pregações novas do YouTube viram Palavras no app.
- **Live:** a cada 5 minutos nos horários de culto, um push avisa quando a live começa.

O GitHub Actions é um paliativo: o agendamento costuma atrasar e às vezes não dispara.
Para rodar na hora: `gh workflow run sync.yml` ou `gh workflow run live.yml`. Para ver o que aconteceu: `gh run list`.
Para mudar horários ou o padrão dos títulos, abra o Claude Code ou o Codex nesta pasta e peça "mudar horário" ou "configurar".
