import json
import os
import shutil
import tempfile

from instalar import crons, gerar, minutos_mes

AQUI = os.path.dirname(os.path.abspath(__file__))
EXEMPLO = os.path.join(AQUI, "igreja.exemplo.json")

# Horário de Brasília (UTC−3) para o cron do Actions (UTC).
assert crons([{"dias": [0], "de": "09:00", "ate": "12:55"}]) == ["*/5 12-15 * * 0"]
assert crons([{"dias": [0, 3], "de": "19:00", "ate": "23:55"}]) == ["*/5 22-23 * * 0,3", "*/5 0-2 * * 1,4"]
assert crons([{"dias": [6], "de": "21:00", "ate": "23:30"}]) == ["*/5 0-2 * * 0"]       # sábado à noite = domingo UTC
assert crons([{"dias": [4, 0], "de": "20:00", "ate": "20:30"}]) == ["*/5 23 * * 0,4"]
assert crons([]) == []
# Minutos do Actions por mês (cada execução conta 1 min): live a cada 5 min nas janelas + sync diário.
assert minutos_mes(["*/5 12-15 * * 0", "*/5 22-23 * * 0,3", "*/5 0-2 * * 1,4"]) == 762
assert minutos_mes([]) == 31

d = tempfile.mkdtemp()
gerar(EXEMPLO, d)
live_yml = open(os.path.join(d, ".github/workflows/live.yml")).read()
sync_yml = open(os.path.join(d, ".github/workflows/sync.yml")).read()
assert '- cron: "*/5 12-15 * * 0"' in live_yml and '- cron: "*/5 0-2 * * 1,4"' in live_yml, live_yml
assert "#CRONS#" not in live_yml and "Lacerdamix/inchurch-sync" in live_yml and "ref: v1" in live_yml
assert "Lacerdamix/inchurch-sync" in sync_yml and "ref: v1" in sync_yml and "dry_run" in sync_yml
assert json.load(open(os.path.join(d, "igreja.json")))["nome"] == "Igreja Exemplo"
assert "Igreja Exemplo" in open(os.path.join(d, "README.md")).read()

# "atualizar": roda de dentro da pasta da igreja, com o igreja.json de lá (origem = destino).
gerar(os.path.join(d, "igreja.json"), d)
assert json.load(open(os.path.join(d, "igreja.json")))["nome"] == "Igreja Exemplo"

# Igreja sem horários de live: live.yml só com o botão manual, sem "schedule:" vazio (o Actions rejeita).
sem_live = os.path.join(tempfile.mkdtemp(), "igreja.json")
cfg = json.load(open(EXEMPLO))
cfg["live"]["janelas"] = []
json.dump(cfg, open(sem_live, "w"))
d2 = tempfile.mkdtemp()
gerar(sem_live, d2)
live_yml = open(os.path.join(d2, ".github/workflows/live.yml")).read()
assert "schedule" not in live_yml and "workflow_dispatch" in live_yml, live_yml

shutil.rmtree(d)
shutil.rmtree(d2)
print("ok")
