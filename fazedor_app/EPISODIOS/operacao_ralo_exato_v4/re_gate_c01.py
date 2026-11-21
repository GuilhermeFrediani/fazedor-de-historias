# -*- coding: utf-8 -*-
"""re_gate_c01.py — recupera o veredito do c01 (tentativa 3) a partir dos frames
ja extraidos, sem re-renderizar. Grava cadeia_v7_bancados.json para a retomada."""
import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
PIPE = EP.parent.parent.parent / "pipeline"
sys.path.insert(0, str(PIPE))
import qc_visao
KEY = qc_visao._chave()

PROPS = ("white wall telephone box with handset and coiled cord, fallen steel grate, grey "
         "steel drum, rubber test plug, white absorbent pads that swell into one pillow, white "
         "paper sack, bucket cart with plastic buckets, squeegee, pressure hose reel, "
         "red-wheel water valves, wall-mounted pressure gauges, electric cabinets with dials "
         "on the right wall, two stacked steel drums at rear right, steel pipes along the "
         "walls, chain with hook, white canvas curtain, broom, caged industrial lamps, wet "
         "concrete floor with yellow safety lines, folded metal ruler, "
         "brass tape hook (loose on the drain rim), "
         "steel tape measure (JUCA's chest pocket - never TEO's hand), "
         "YELLOW carpenter pencil (TEO's; pinned through the hook eye in c05; never red), "
         "green document case (inside the sealed drum in c06), "
         "military client in olive uniform (clips 1 and 6 only, when announced by the estado)")

base = json.loads((EP / "settings" / "operacao_ralo_exato_v4_c01_ligacao_settings.json")
                  .read_text(encoding="utf-8"))
estado_end = re.search(r"AT END: (.+?)\.?(?:\n|$)", base["prompt"]).group(1)
print("AT END c01:", estado_end)
print()

j99 = qc_visao.gate_ancora(KEY, str(EP / "refs" / "ancora_v7_c01.png"),
                           estado=estado_end, props=PROPS, cliente=True)
print("GATE ANCOR f9.9:", j99.get("veredito"), "—", j99.get("motivo"))
print("  nao_plantados=%s props_violados=%s cenario=%s" %
      (j99.get("objetos_nao_plantados"), j99.get("props_violados"), j99.get("cenario_violado")))
j50 = qc_visao.gate_ancora(KEY, str(EP / "refs" / "meio_v7_c01.png"),
                           estado="", props=PROPS, cliente=True)
print("GATE MEIO  f5.0:", j50.get("veredito"), "—", j50.get("motivo"))
print("  nao_plantados=%s props_violados=%s cenario=%s" %
      (j50.get("objetos_nao_plantados"), j50.get("props_violados"), j50.get("cenario_violado")))

aprovado = (j99.get("veredito") == "APROVADA" and j50.get("veredito") == "APROVADA"
            and not j99.get("personagens_extras") and not j50.get("personagens_extras"))
mp4 = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs\operacao_ralo_exato_v4_c01_ligacao_v7_r2.mp4")
entrada = {
    "slug": "operacao_ralo_exato_v4_c01_ligacao",
    "curto": "c01",
    "mp4": str(mp4),
    "estado_in_real": "",
    "aprovado": bool(aprovado),
    "fallback": not bool(aprovado),
    "gate_ancora": j99,
    "gate_meio": j50,
    "ancora_out": str(EP / "refs" / "ancora_v7_c01.png"),
}
(EP / "cadeia_v7_bancados.json").write_text(json.dumps({"c01": entrada}, ensure_ascii=False,
                                                       indent=2), encoding="utf-8")
print("\nBANCADO c01 ->", "APROVADO" if aprovado else "FALLBACK",
      "| cadeia_v7_bancados.json gravado")
