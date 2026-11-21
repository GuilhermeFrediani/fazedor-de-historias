# -*- coding: utf-8 -*-
# Rodada 2 do v7: re-renderiza c01/c02 com os consertos da auditoria.
# bancados novo = so c03 (o que a cadeia atual ja resolveu); c01/c02 saem para re-render.
import json, shutil
from pathlib import Path

EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")

rep = json.loads((EP / "cadeia_v7_relatorio.json").read_text(encoding="utf-8"))
shutil.copy(EP / "cadeia_v7_relatorio.json", EP / "cadeia_v7_relatorio_rodada1.json")
if (EP / "cadeia_v7_bancados.json").exists():
    shutil.copy(EP / "cadeia_v7_bancados.json", EP / "cadeia_v7_bancados_rodada1.json")

bank = {}
for f in rep:
    if f.get("curto") == "c03" and f.get("mp4"):
        bank["c03"] = f
        break
(EP / "cadeia_v7_bancados.json").write_text(
    json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")

c3 = bank.get("c03", {})
print("bancados novo:", list(bank))
print("c03 aprovado=%s fallback=%s seed=%s mp4=%s"
      % (c3.get("aprovado"), c3.get("fallback"),
         (c3.get("tentativas") or [{}])[-1].get("seed"), c3.get("mp4")))
