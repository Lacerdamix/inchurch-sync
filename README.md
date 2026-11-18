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
- Um assistente instalado: o [Claude Code](https://claude.com/claude-code) ou o [Codex](https://developers.openai.com/codex). Qualquer um dos dois serve; cada um faz parte dos planos pagos da sua empresa (Claude ou ChatGPT).
- Uma conta no [GitHub](https://github.com/signup), gratuita. Se não tiver, dá para criar durante a instalação.
- O e-mail e a senha de quem acessa o painel da InChurch da igreja.

Você não precisa saber programar nem instalar mais nada antes: o assistente instala o que faltar.

## Instalação

**1. Adicione o inchurch-sync ao seu assistente.** Cole as duas linhas, uma de cada vez, apertando Enter depois de cada uma.

No **Claude Code**, dentro da conversa:

```
/plugin marketplace add Lacerdamix/inchurch-sync
/plugin install inchurch-sync
```

No **Codex**, no Terminal (Mac: Cmd+Espaço e digite "Terminal"; Windows: menu Iniciar, "PowerShell"):

```
codex plugin marketplace add Lacerdamix/inchurch-sync
codex plugin add inchurch-sync@inchurch-sync
```

Depois abra o Codex.

**Atalho, sem instalar o plugin:** baixe o arquivo [INSTALAR.md](https://raw.githubusercontent.com/Lacerdamix/inchurch-sync/main/INSTALAR.md) (no navegador, Cmd+S ou Ctrl+S) e envie-o na conversa do Claude Code ou do Codex. O assistente começa sozinho; pule para o passo 3.

**2. Escreva `instalar`** e aperte Enter. Daqui em diante o assistente conduz. Quando ele pedir permissão para executar algo, pode aceitar.

**3. Entre no GitHub.** O assistente abre uma página do GitHub no seu navegador e mostra um código na conversa. Entre na sua conta (ou crie uma), digite o código e clique em **Authorize**.

**4. Responda às perguntas.** O canal do YouTube, os dias e horários dos cultos e o e-mail do painel. O assistente olha os títulos dos seus vídeos sozinho e só confirma com você como eles são escritos.

**5. Digite a senha do painel.** O assistente abre uma janela pronta, só para isso. Digite a senha e aperte Enter (as letras não aparecem enquanto você digita, é normal). Ela vai direto para o cofre do GitHub e não passa pela conversa.

**6. Confira e dê o OK.** O assistente mostra o que seria publicado. Nada vai para o app antes do seu OK.

Pronto. Não precisa fazer mais nada, e o computador pode ficar desligado.

## Depois de instalado

Para mudar ou conferir algo, abra o mesmo assistente e peça em português:

- **"mudar horário"**, quando os dias ou horários dos cultos mudarem;
- **"configurar"**, para ajustar qualquer outra resposta da instalação;
- **"testar"**, para ver o que seria publicado agora, sem publicar.

## Importante: o GitHub Actions é um paliativo

A instalação usa o GitHub Actions, o agendador gratuito do GitHub, para não precisar de servidor. Ele funciona, mas **não é pontual**: o agendamento costuma atrasar, às vezes por horas, e de vez em quando não dispara.

- Para as **pregações**, isso quase não importa: se atrasar, a Palavra entra mais tarde no mesmo dia.
- Para o **aviso de live**, o push pode chegar atrasado ou não chegar.

Se a igreja quiser o aviso na hora, o caminho confiável é rodar os mesmos scripts, com agendamento a cada 5 minutos, numa máquina que fique sempre ligada. Há duas opções:

- **Um computador antigo** que a igreja já tenha, ligado na tomada e na internet o tempo todo. Não custa nada além da luz, mas se ele desligar ou a internet cair, o aviso para.
- **Um servidor alugado (VPS)**, que fica num datacenter e custa uma mensalidade pequena. Não depende da luz nem da internet da igreja.

Nos dois casos a configuração é feita à mão por alguém técnico; esta instalação não cuida disso.

O plano gratuito do GitHub dá 2.000 minutos por mês em repositório privado. A instalação mostra a estimativa para os seus horários; uma igreja com três cultos por semana fica perto de 800.

## Para quem é técnico

Como funciona por dentro, os campos do `igreja.json`, a instalação manual sem agente e os testes estão em [docs/avancado.md](docs/avancado.md).
