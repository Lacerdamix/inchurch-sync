#!/usr/bin/env python3
"""Gera (ou atualiza) a pasta do repositório da igreja a partir de modelo/: igreja.json, README e os dois
workflows do GitHub Actions, com o cron da live calculado a partir de live.janelas. Não mexe em git nem gh.

  python3 instalar.py <igreja.json> <pasta-destino>
"""
import os
import shutil
import sys

from igreja import carregar_igreja

MODELO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modelo")
FUSO_HORAS = 3  # Brasília = UTC−3 (sem horário de verão desde 2019)


def crons(janelas):
    """Janelas em horário de Brasília → linhas de cron (UTC) a cada 5 min. Janela que passa da meia-noite UTC
    vira duas linhas: o resto do dia com os dias originais e a madrugada UTC com o dia seguinte."""
    linhas = []
    for j in janelas:
        ini = int(j["de"][:2]) + FUSO_HORAS
        fim = int(j["ate"][:2]) + FUSO_HORAS  # a hora cheia que contém o minuto final
        partes = [(ini, min(fim, 23), j["dias"])] if ini < 24 else []
        if fim >= 24:
            partes.append((max(ini, 24) - 24, fim - 24, [(d + 1) % 7 for d in j["dias"]]))
        for a, b, dias in partes:
            horas = f"{a}" if a == b else f"{a}-{b}"
            linhas.append(f"*/5 {horas} * * {','.join(map(str, sorted(dias)))}")
    return linhas


def minutos_mes(linhas):
    """Estimativa de minutos do Actions por mês: cada execução conta 1 minuto (o GitHub arredonda para cima).
    Live: 12 execuções por hora em cada linha de cron; sync: 1 por dia."""
    por_semana = 0
    for linha in linhas:
        _, horas, _, _, dias = linha.split()
        a, _, b = horas.partition("-")
        por_semana += (int(b or a) - int(a) + 1) * 12 * len(dias.split(","))
    return round(por_semana * 4.35) + 31


def gerar(config_path, destino):
    cfg = carregar_igreja(config_path)  # valida antes de escrever qualquer coisa
    workflows = os.path.join(destino, ".github", "workflows")
    os.makedirs(workflows, exist_ok=True)
    alvo = os.path.join(destino, "igreja.json")
    if os.path.abspath(config_path) != os.path.abspath(alvo):
        shutil.copyfile(config_path, alvo)
    with open(os.path.join(MODELO, "README.md"), encoding="utf-8") as f:
        readme = f.read().replace("{{NOME}}", cfg["nome"])
    with open(os.path.join(destino, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)
    shutil.copyfile(os.path.join(MODELO, "sync.yml"), os.path.join(workflows, "sync.yml"))
    linhas = crons(cfg["live"]["janelas"])
    schedule = "".join(f'    - cron: "{c}"\n' for c in linhas)
    with open(os.path.join(MODELO, "live.yml"), encoding="utf-8") as f:
        live = f.read().replace("#CRONS#\n", f"  schedule:  # horários de culto, em UTC\n{schedule}" if linhas else "")
    with open(os.path.join(workflows, "live.yml"), "w", encoding="utf-8") as f:
        f.write(live)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    gerar(sys.argv[1], sys.argv[2])
    print(f"Pronto: {os.path.abspath(sys.argv[2])}")
    minutos = minutos_mes(crons(carregar_igreja(sys.argv[1])["live"]["janelas"]))
    print(f"Estimativa: {minutos} minutos/mês do GitHub Actions (grátis até 2.000/mês em repositório privado)")
