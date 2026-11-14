# -*- coding: utf-8 -*-
"""Patch v4 no fazedor_app.py: prompt mestre, montagem, validador composto."""
import re, shutil, sys
from pathlib import Path

APP = Path("/home/user/repo/fazedor_app/fazedor_app.py")
src = APP.read_text(encoding="utf-8")
shutil.copy(APP, APP.with_suffix(".py.v3.bak"))

# 1. import
a = "_HERE = Path(__file__).resolve().parent\nsys.path.insert(0, str(_HERE.parent))\nimport regras_v3"
assert a in src, "ancora import"
src = src.replace(a, a + "\nimport regras_v4", 1)

# 2. prompt mestre
a = "    return regras_v3.PROMPT_MESTRE_V3"
assert a in src, "ancora prompt"
src = src.replace(a, "    return regras_v4.PROMPT_MESTRE_V4", 1)

# 3. montagem
a = "    return regras_v3.montar_prompt_v3(s, ep, blocos_fixos())"
assert a in src, "ancora montar"
src = src.replace(a, "    return regras_v4.montar_prompt_v4(s, ep, blocos_fixos())", 1)

# 4. validador composto: render (v3) + montage (v4)
a = '''def validar_dossie(ep):
    base = _validar_dossie_v2(ep)
    render = regras_v3.validar_renderizavel(ep)'''
assert a in src, "ancora validador"
src = src.replace(a, '''def _com_action(ep):
    """v4 escreve 'planos'; o checador de física da v3 lê 'action'. Deriva um do outro."""
    novo = dict(ep)
    shots = []
    for s in ep.get("shots") or []:
        s2 = dict(s)
        if not s2.get("action"):
            s2["action"] = " ".join(str(p.get("texto", "")) for p in (s.get("planos") or []))
        shots.append(s2)
    novo["shots"] = shots
    return novo


def validar_dossie(ep):
    base = _validar_dossie_v2(ep)
    render = regras_v3.validar_renderizavel(_com_action(ep))''', 1)

a = '''    base.update({"erros": erros, "avisos": avisos, "humor": humor,
                 "render": render["nota"], "nota": nota, "formato": "dossie_v3",
                 "checks_render": render["checks"]})
    return base'''
assert a in src, "ancora update"
src = src.replace(a, '''    mont = regras_v4.validar_montagem(_com_action(ep))
    erros += [e for e in mont["erros"] if e not in erros]
    avisos = ["MONTAGE: %d/10 - %s" % (mont["nota"], "; ".join(mont["checks"]) or "-")] + \\
             mont["avisos"] + avisos
    nota = round(0.30 * humor + 0.35 * render["nota"] + 0.35 * mont["nota"], 1)
    base.update({"erros": erros, "avisos": avisos, "humor": humor,
                 "render": render["nota"], "montage": mont["nota"], "nota": nota,
                 "formato": "dossie_v4", "checks_render": render["checks"],
                 "checks_montage": mont["checks"]})
    return base''', 1)

APP.write_text(src, encoding="utf-8")
print("OK — fazedor_app.py em v4")
