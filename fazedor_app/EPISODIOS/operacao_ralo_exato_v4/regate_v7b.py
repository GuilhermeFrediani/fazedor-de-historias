# -*- coding: utf-8 -*-
# Re-gate OFFLINE dos renders ja prontos com o gate corrigido:
#  - MODO INSERT em f2.0/f3.0 (close nao precisa dos dois bonecos)
#  - digitos de teclado/medidor nao contam como texto
#  - estado so reprova CONTRADICAO (nao mera ausencia em close)
# Candidatos: c01 t1/t2, c02 t1/t2, c04 t1.
import json, re, subprocess, sys
from pathlib import Path

EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")
PIPE = EP.parent.parent.parent / "pipeline"
sys.path.insert(0, str(PIPE))
import qc_visao

KEY = qc_visao._chave()
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()

src = (EP / "cadeia_v7.py").read_text(encoding="utf-8")
m = re.search(r"PROPS = \(.*?\)\n", src, flags=re.S)
PROPS = eval(m.group(0).split("=", 1)[1].strip())


def estado_end(slug_base):
    p = json.loads((EP / "settings" / (slug_base + "_settings.json")).read_text(encoding="utf-8"))["prompt"]
    mo = re.search(r"AT END: (.+?)\.?(?:\n|$)", p)
    return mo.group(1) if mo else ""


def ok(j, ins):
    return (j.get("veredito") == "APROVADA"
            and not j.get("personagens_extras")
            and not j.get("objetos_flutuantes")
            and not j.get("fantasmas")
            and (j.get("dois_bonecos") is not False or ins))


CANDS = [
    ("c01", "t1_seed7006", "operacao_ralo_exato_v4_c01_ligacao_v7(3).mp4",
     "operacao_ralo_exato_v4_c01_ligacao", True),
    ("c01", "t2_seed7007", "operacao_ralo_exato_v4_c01_ligacao_v7_r1(3).mp4",
     "operacao_ralo_exato_v4_c01_ligacao", True),
    ("c02", "t1_seed7005", "operacao_ralo_exato_v4_c02_cadeia_v7(3).mp4",
     "operacao_ralo_exato_v4_c02_cadeia", False),
    ("c02", "t2_seed7006", "operacao_ralo_exato_v4_c02_cadeia_v7_r1(3).mp4",
     "operacao_ralo_exato_v4_c02_cadeia", False),
    ("c04", "t1_seed7102", "operacao_ralo_exato_v4_c04_jeitinho_v6a_v7.mp4",
     "operacao_ralo_exato_v4_c04_jeitinho_v6a", False),
]

saida = {}
for curto, tag, nome, slug_base, cliente in CANDS:
    mp4 = OUT / nome
    if not mp4.exists():
        print("AUSENTE:", nome)
        continue
    est = estado_end(slug_base)
    print("\n=== %s %s ===" % (curto, tag))
    res = {"mp4": str(mp4), "frames": {}}
    todos_ok = True
    for ts, ins in (("9.9", False), ("5.0", False), ("3.0", True), ("2.0", True)):
        png = EP / "refs" / ("rg_%s_%s_%s.png" % (curto, tag, ts))
        subprocess.run([FF, "-y", "-ss", ts, "-i", str(mp4), "-frames:v", "1", str(png)],
                       capture_output=True)
        j = qc_visao.gate_ancora(KEY, str(png), estado=(est if ts == "9.9" else ""),
                                 props=PROPS, cliente=cliente, inserto=ins)
        bom = ok(j, ins)
        todos_ok = todos_ok and bom
        res["frames"][ts] = j
        print("  f%s%s: %s %s | %s" % (ts, " (inserto)" if ins else "", j.get("veredito"),
                                       "OK" if bom else "XX", j.get("motivo", "")))
        print("     extras=%s flut=%s texto=%s nao_plant=%s props=%s estado=%s cenario=%s fantasmas=%s dois=%s"
              % (j.get("personagens_extras"), j.get("objetos_flutuantes"), j.get("texto_na_tela"),
                 j.get("objetos_nao_plantados"), j.get("props_violados"), j.get("estado_divergente"),
                 j.get("cenario_violado"), j.get("fantasmas"), j.get("dois_bonecos")))
    res["aprovado_4frames"] = todos_ok
    saida[curto + "_" + tag] = res
    print("  => %s" % ("APROVADO (4/4)" if todos_ok else "reprovado"))

(EP / "regate_v7b.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
print("\ngravado regate_v7b.json")
