# -*- coding: utf-8 -*-
# imprime o trecho AT START..fim dos settings que importam para o conserto v7
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4\settings")
alvos = [
    "operacao_ralo_exato_v4_c01_ligacao_settings.json",
    "operacao_ralo_exato_v4_c03_primeira_falha_v2_settings.json",
    "operacao_ralo_exato_v4_c04_jeitinho_v6a_settings.json",
    "operacao_ralo_exato_v4_c05_escalada_v6a_settings.json",
    "operacao_ralo_exato_v4_c06_climax_v6a_settings.json",
]
for nome in alvos:
    p = json.loads((S / nome).read_text(encoding="utf-8"))["prompt"]
    i = p.find("AT START")
    print("=" * 100)
    print(nome)
    print("=" * 100)
    print(p[i:] if i >= 0 else "(sem AT START)")
    print()
