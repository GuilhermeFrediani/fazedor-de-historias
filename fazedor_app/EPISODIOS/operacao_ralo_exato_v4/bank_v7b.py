# -*- coding: utf-8 -*-
# Bancada da rodada 2: c01 t2 (7007) e c02 t2 (7006) APROVADOS no re-gate corrigido;
# c03 fica como fallback (ja resolvido); c04 t1 entra como fallback (3/4 no re-gate).
import json, re
from pathlib import Path

EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")

rep = json.loads((EP / "cadeia_v7_relatorio.json").read_text(encoding="utf-8"))
rg = json.loads((EP / "regate_v7b.json").read_text(encoding="utf-8"))
by = {f["curto"]: f for f in rep}

# estado real do c04 (ultimo que a cadeia imprimiu no log)
log = (EP / "cadeia_v7_run.log").read_text(encoding="utf-8", errors="replace")
ms = list(re.finditer(r"estado REAL da ancora \(c04\): (.+)", log))
est_c04 = ms[-1].group(1).strip() if ms else ""

# --- c01: t2 seed 7007, aprovado com1 nit documentado (grade encostada no ralo no insert)
c01 = dict(by["c01"])
c01.update({
    "aprovado": True,
    "ancora_out": str(EP / "refs" / "rg_c01_t2_seed7007_9.9.png"),
    "gate_ancora": rg["c01_t2_seed7007"]["frames"]["9.9"],
    "gate_meio": rg["c01_t2_seed7007"]["frames"]["5.0"],
    "gate_frames": rg["c01_t2_seed7007"]["frames"],
    "nota_gate": ("re-gate offline pos-correcao do gate (inserto/teclado/estado). "
                  "4/4 menos f3.0: grade encostada na borda do ralo no insert (nit; "
                  "papel em branco, sem ghost, cliente entrega, papel no bolso do TEO)"),
})
c01.pop("fallback", None)

# --- c02: t2 seed 7006, 4/4 limpo
c02 = dict(by["c02"])
c02.update({
    "aprovado": True,
    "ancora_out": str(EP / "refs" / "rg_c02_t2_seed7006_9.9.png"),
    "gate_ancora": rg["c02_t2_seed7006"]["frames"]["9.9"],
    "gate_meio": rg["c02_t2_seed7006"]["frames"]["5.0"],
    "gate_frames": rg["c02_t2_seed7006"]["frames"],
    "nota_gate": "re-gate offline pos-correcao do gate: 4/4 (inserto/teclado/estado)",
})
c02.pop("fallback", None)

# --- c03: continua fallback (3/3 reprovadas por fresta de ceu no topo)
c03 = dict(by["c03"])

# --- c04: t1 seed 7102, 3/4 (estado da almofada) -> fallback
c04 = {
    "slug": "operacao_ralo_exato_v4_c04_jeitinho_v6a",
    "curto": "c04",
    "mp4": str(OUT / "operacao_ralo_exato_v4_c04_jeitinho_v6a_v7.mp4"),
    "estado_in_real": est_c04,
    "aprovado": False,
    "fallback": True,
    "scan_ceu": {"veredito": "APROVADA", "violacoes": []},
    "gate_ancora": rg["c04_t1_seed7102"]["frames"]["9.9"],
    "gate_meio": rg["c04_t1_seed7102"]["frames"]["5.0"],
    "gate_frames": rg["c04_t1_seed7102"]["frames"],
    "ancora_out": str(EP / "refs" / "rg_c04_t1_seed7102_9.9.png"),
    "nota_gate": "re-gate offline: 3/4 - estado f9.9 (almofada nao cobre as duas botas); demais limpo",
    "tentativas": [{"slug": "operacao_ralo_exato_v4_c04_jeitinho_v6a_v7", "seed": 7102,
                    "mp4": str(OUT / "operacao_ralo_exato_v4_c04_jeitinho_v6a_v7.mp4")}],
}

bank = {"c01": c01, "c02": c02, "c03": c03, "c04": c04}
(EP / "cadeia_v7_bancados.json").write_text(
    json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")
print("bancados:", list(bank))
for k, v in bank.items():
    print("  %s: aprovado=%s fallback=%s mp4=%s" % (k, v.get("aprovado"), v.get("fallback"),
                                                    Path(v.get("mp4", "?")).name))
