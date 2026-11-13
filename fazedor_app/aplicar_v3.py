# -*- coding: utf-8 -*-
"""Aplica a camada v3 no fazedor_app.py (com asserts: falha alto se um âncora não casar)."""
import re, sys, shutil
from pathlib import Path

APP = Path("/home/user/proj/g2/fazedor-de-historias/fazedor_app/fazedor_app.py")
src = APP.read_text(encoding="utf-8")
shutil.copy(APP, APP.with_suffix(".py.v2.bak"))
orig = src

# ── 1. importa regras_v3 ────────────────────────────────────────────────────
a1 = "from pathlib import Path\n\nAPP_DIR = Path(__file__).resolve().parent"
assert a1 in src, "ancora 1 nao encontrada"
src = src.replace(a1, """from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import regras_v3  # v3: camada de RENDERIZABILIDADE (orcamento de fisica + ancoras curtas)

APP_DIR = _HERE""", 1)

# ── 2. instrucoes_dossie devolve o prompt v3 ────────────────────────────────
a2 = ('def instrucoes_dossie():\n'
      '    """Prompt de sistema v2 - autossuficiente. ANCORAS nao entram aqui: o montador cola."""\n'
      '    return PROMPT_MESTRE_V2')
assert a2 in src, "ancora 2 nao encontrada"
src = src.replace(a2, '''def instrucoes_dossie():
    """v3: prompt mestre com ORCAMENTO DE FISICA + regra dos dois corpos + reacao legivel.
    A ancora visual continua fora daqui: o programa cola ancoras CURTAS (regras_v3)."""
    return regras_v3.PROMPT_MESTRE_V3''', 1)

# ── 3. prompt_dossie -> montar_prompt_v3 (acao primeiro) ────────────────────
pat = re.compile(r"def prompt_dossie\(s, ep\):.*?\n\nFORMATOS = \{", re.S)
assert pat.search(src), "ancora 3 nao encontrada"
src = pat.sub('''def prompt_dossie(s, ep):
    """v3: ACTION primeiro, ancoras CURTAS no meio, estilo/negativos no fim.
    Motivo: o modelo le o comeco do prompt. No v2 a acao ficava depois de ~3.900
    chars de roupa, e o video renderizava a roupa e ignorava a piada."""
    return regras_v3.montar_prompt_v3(s, ep, blocos_fixos())


FORMATOS = {''', src, count=1)

# ── 4. formato de 6 clipes = 6 clipes CONSECUTIVOS ──────────────────────────
pat6 = re.compile(r'6: \{"LIGACAO": 1[^}]*\}')
assert pat6.search(src), "ancora 4 nao encontrada"
src = pat6.sub('''6: {"LIGACAO": 1, "CHEGADA": 1, "PRIMEIRA_FALHA": 1,
        "JEITINHO": 1, "ESCALADA": 1, "CLIMAX": 1}''', src, count=1)

# ── 5. renomeia o validador antigo (fica como base de forma/humor) ──────────
assert "def validar_dossie(ep):" in src, "ancora 5 nao encontrada"
src = src.replace("def validar_dossie(ep):", "def _validar_dossie_v2(ep):", 1)

# ── 6. anexa o validador v3 (forma + humor + RENDERIZABILIDADE) ─────────────
src += '''

# ═══════════════════════════════════════════════════════════════════════════
# v3 — VALIDADOR FINAL: forma (v2) + humor (v2) + RENDERIZABILIDADE (v3)
# A falha do v2 foi dar 8,5/10 para um episodio que virou bug na tela: ele
# media a PIADA DECLARADA, nunca a PIADA FILMAVEL. Agora os dois contam.
# ═══════════════════════════════════════════════════════════════════════════
def validar_dossie(ep):
    base = _validar_dossie_v2(ep)
    render = regras_v3.validar_renderizavel(ep)
    erros = list(base.get("erros", [])) + list(render.get("erros", []))
    avisos = list(render.get("avisos", [])) + list(base.get("avisos", []))
    humor = base.get("humor", 0)
    nota = round(0.35 * humor + 0.65 * render["nota"], 1)
    avisos.insert(0, "RENDERIZABILIDADE: %d/10 (peso 65%%) - %s"
                  % (render["nota"], "; ".join(render["checks"]) or "nada comprovado"))
    base.update({"erros": erros, "avisos": avisos, "humor": humor,
                 "render": render["nota"], "nota": nota, "formato": "dossie_v3",
                 "checks_render": render["checks"]})
    return base
'''
assert src != orig
APP.write_text(src, encoding="utf-8")

# PROMPT_SISTEMA_v3.txt para colar em qualquer chat
PASTA = APP.parent.parent
(PASTA / "PROMPT_SISTEMA_v3.txt").write_text(regras_v3.PROMPT_MESTRE_V3.strip() + "\n", encoding="utf-8")
print("OK — fazedor_app.py atualizado")
print("PROMPT_SISTEMA_v3.txt:", len(regras_v3.PROMPT_MESTRE_V3), "chars")
