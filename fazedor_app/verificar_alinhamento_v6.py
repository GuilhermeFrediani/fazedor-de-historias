# -*- coding: utf-8 -*-
"""verificar_alinhamento_v6.py — checagem estática V6 × pipeline (sem API).

Corre com:
  python verificar_alinhamento_v6.py

Não chama AgentRouter/Gemini, não renderiza, não imprime chaves.
"""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
APP = Path(__file__).resolve().parent
ROOT = APP.parent
sys.path.insert(0, str(APP))

import regras_v4  # noqa: E402
import regras_v6  # noqa: E402
import auditor_v6  # noqa: E402
import fazedor_app as app  # noqa: E402

OK = 0
FAIL = 0


def check(nome, cond, detalhe=""):
    global OK, FAIL
    if cond:
        OK += 1
        print("OK   %s%s" % (nome, (" | " + detalhe) if detalhe else ""))
    else:
        FAIL += 1
        print("FAIL %s%s" % (nome, (" | " + detalhe) if detalhe else ""))


def main():
    # 1. Prompt canônico
    txt = (ROOT / "PROMPT_SISTEMA_v6.txt").read_bytes()
    mod = regras_v6.PROMPT_MESTRE_V6.encode("utf-8")
    check("PROMPT_SISTEMA_v6.txt byte-igual ao módulo", txt == mod,
          "%d chars" % len(regras_v6.PROMPT_MESTRE_V6))
    check("instrucoes_dossie() == V6", app.instrucoes_dossie() == regras_v6.PROMPT_MESTRE_V6)
    check("V6 contém 14 partes", all(("PARTE %d" % i) in regras_v6.PROMPT_MESTRE_V6
                                    for i in range(1, 15)))
    check("AUDITOR_V6 carregado", len(auditor_v6.PROMPT_AUDITOR_V6) > 6000,
          "%d chars" % len(auditor_v6.PROMPT_AUDITOR_V6))

    # 2. Contrato do render / áudio
    s = {"n": 1, "planos": [{"t": "00:00.000", "texto": "TEO lifts a wooden panel."},
                            {"t": "00:03.500", "texto": "JUCA pushes it over."}],
         "overall_soundscape": "Wooden panel scrapes across concrete, rough and heavy.",
         "non_diegetic_music": "", "estado_in": "A panel rests on the floor.",
         "estado_out": "The panel lies flat."}
    p = regras_v4.montar_prompt_v4(s, {}, {}, exigir_cortes=True)
    check("montar_prompt_v4() mantém integrated_multimodal_description",
          p.startswith("integrated_multimodal_description: "))
    check("montar_prompt_v4() mantém overall_soundscape", "\noverall_soundscape: " in p)
    check("montar_prompt_v4() NUNCA emite N/A", "\nnon_diegetic_music: N/A" not in p)
    mus = p.split("\nnon_diegetic_music: ", 1)[1]
    check("trilha instrumental de fallback",
          "no vocals" in mus.lower() or "instrumental" in mus.lower(),
          mus[:70])

    smoke = (APP / "smoke_60s.py").read_text(encoding="utf-8")
    check("âncora do smoke sem N/A", "non_diegetic_music: N/A" not in smoke)
    check("smoke usa a trilha instrumental padrão",
          "regras_v4.MUSICA_INSTRUMENTAL_PADRAO" in smoke)
    check("smoke grava heartbeat", "def heartbeat(" in smoke and "heartbeat(ep_dir" in smoke)
    check("smoke tem checkpoint raw antes do gate",
          "raw_%s.json" in smoke and "RAW REAPROVEITADO" in smoke)

    # 3. Formatos e modelos
    check("FORMATOS = 3/6/30", sorted(app.FORMATOS) == [3, 6, 30], str(sorted(app.FORMATOS)))
    check("AgentRouter 6.2", app.AR_MODELOS == ["gpt-6.2-astra", "gpt-6.2-sol"],
          ", ".join(app.AR_MODELOS))
    fapp = (APP / "fazedor_app.py").read_text(encoding="utf-8")
    check("/api/auditar ativo", '"/api/auditar"' in fapp and "def _auditar(" in fapp)
    check("auditor usa o outro modelo",
          "m for m in AR_MODELOS if m != criador" in fapp)

    # 4. Benchmark seco
    r = subprocess.run([sys.executable, str(APP / "benchmark_v6.py"), "--dry"],
                       cwd=str(APP), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    check("benchmark --dry EXIT 0", r.returncode == 0,
          (r.stdout or "").splitlines()[0] if r.stdout else (r.stderr or "")[:120])

    # 5. Compilação
    alvos = ["regras_v4.py", "regras_v6.py", "auditor_v6.py", "benchmark_v6.py",
             "fazedor_app.py", "canon_comedia.py", "smoke_60s.py",
             "render_supervisor.py", "iniciar_supervisor.py", "iniciar_smoke_60s.py"]
    r = subprocess.run([sys.executable, "-m", "py_compile"] +
                       [str(APP / a) for a in alvos], cwd=str(APP),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    check("py_compile de %d módulos" % len(alvos), r.returncode == 0,
          (r.stderr or "")[:160])

    print("\n>>> ALINHAMENTO V6: %d OK / %d FAIL" % (OK, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
