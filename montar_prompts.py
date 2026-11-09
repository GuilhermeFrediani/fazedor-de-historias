#!/usr/bin/env python3
"""
montar_prompts.py — TÉO & JUCA Company

Lê o JSON do episódio (devolvido pelo gerador), valida as regras do pipeline H3
e monta os prompts finais (3 campos oficiais), colando os blocos fixos verbatim.

Uso:
    python montar_prompts.py episodio.json
    python montar_prompts.py episodio.json --blocos blocos_fixos.json --out saida/ --forcar

Saída (pasta --out, padrão <episodio>_prompts/):
    shot_01.txt ... shot_NN.txt   -> um prompt por plano
    manifest.json                 -> video_length, inicio (ultimo_frame|texto), set, nº de caracteres
Código de saída: 0 = ok (pode ter avisos), 1 = erros (nada é gravado, a menos que use --forcar).
"""
import argparse
import json
import re
import sys
from pathlib import Path

LIMITE_CHARS = 7000
AVISO_CHARS = 6500
DUR_MIN, DUR_MAX = 4, 10
META_MIN_S, META_MAX_S = 120, 150
CAMPOS = ["n", "estagio", "duracao_s", "inicio", "set", "funcao_comica",
          "estado", "acao", "camera", "soundscape", "fim_estado"]
ESTAGIOS = {"INTRO", "SERVICO", "TENTATIVA", "FALHA", "REACAO_GAMBIARRA",
            "NOVO_CAOS", "RESOLUCAO", "TAG"}
SILENCIO = "beat of complete silence"

RE_DURACAO = re.compile(
    r"\b\d+(\.\d+)?\s*(s|sec|secs|second|seconds)\b|"
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+seconds?\b", re.I)
RE_FREEZE = re.compile(r"\b(freeze|freezes|frozen|stare|stares|staring|motionless)\b", re.I)
RE_CAMERA_OLHAR = re.compile(r"(looks?|glances?|turns?)\s+(straight\s+)?(at|into|to)\s+the\s+(camera|lens|viewer)|fourth wall", re.I)
RE_PRECISAO = re.compile(r"\b(exactly|precisely|perfectly timed|millimet\w*)\b", re.I)
RE_FALA = re.compile(r"\b(speak|speaks|speaking|says|said|shouts|yells|talks|talking|whispers|"
                     r"mutters|grunts|groans|sighs|laughs|giggles|hums|voice|voices|dialogue|"
                     r"subtitles?|captions?)\b", re.I)
RE_HANDOFF = re.compile(r"\b(hands|passes|tosses|throws|gives|offers)\s+(him|her|over|the|a|JUCA|TÉO)\b", re.I)
RE_VAGO = re.compile(r"\b(hum|ambient|ambience|atmosphere|atmospheric|background noise|"
                     r"gentle sounds|quiet sounds|soft sounds)\b", re.I)
RE_CAM_PROIBIDA = re.compile(r"hand-?held|whip|crash zoom|zoom in|zoom out|shak(e|y)|\bfast\b|\bquick\b|\brapid\b", re.I)
RE_CAM_MOVS = re.compile(r"push-in|pull-back|pull-out|dolly|\bpan\b|\btilt\b|\btrack(ing)?\b|orbit|crane", re.I)
RE_FIM_PARADO = re.compile(r"\b(stand|stands|stay|stays|remain|remains|hold|holds)\b[^.]*\b(still|motionless|in place)\b", re.I)


def carregar_json(caminho):
    txt = Path(caminho).read_text(encoding="utf-8").strip()
    if txt.startswith("```"):  # tolera a saída colada com cerca de código
        txt = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", txt).strip()
    return json.loads(txt)


def montar(shot, blocos, ep):
    set_txt = blocos["SET_OFICINA"] if shot["set"] == "oficina" else ep["set_historia"]
    partes = [
        blocos["ESTILO"],
        set_txt,
        "Current state: " + shot["estado"],
        blocos["JUCA"],
        blocos["TEO"],
        shot["acao"],
        "They do not speak and their mouths do not move.",
        shot["camera"],
        blocos["NEGATIVOS"],
    ]
    visual = " ".join(p.strip() for p in partes)
    return ("integrated_multimodal_description: [Shot 1] " + visual + "\n"
            "overall_soundscape: " + shot["soundscape"].strip() + "\n"
            "non_diegetic_music: N/A\n")


def validar(ep, blocos):
    erros, avisos = [], []
    shots = ep.get("shots") or []
    if not shots:
        return ["episódio sem 'shots'"], avisos, 0
    if "set_historia" not in ep:
        erros.append("falta 'set_historia'")

    total = 0
    n_silencios = 0
    n_cortes = 0
    cam_inicios = []
    for i, s in enumerate(shots):
        tag = f"[{i + 1:02d}]"
        faltando = [c for c in CAMPOS if c not in s]
        if faltando:
            erros.append(f"{tag} campos ausentes: {', '.join(faltando)}")
            continue
        total += s["duracao_s"]
        if s["n"] != i + 1:
            erros.append(f"{tag} 'n' deveria ser {i + 1} (veio {s['n']})")
        if s["estagio"] not in ESTAGIOS:
            erros.append(f"{tag} estágio inválido: {s['estagio']}")
        if not DUR_MIN <= s["duracao_s"] <= DUR_MAX:
            erros.append(f"{tag} duracao_s={s['duracao_s']} fora de {DUR_MIN}–{DUR_MAX}s (teto do pipeline = {DUR_MAX}s)")
        if s["inicio"] not in ("texto", "ultimo_frame"):
            erros.append(f"{tag} 'inicio' deve ser 'texto' ou 'ultimo_frame'")
        if s["set"] not in ("oficina", "historia"):
            erros.append(f"{tag} 'set' deve ser 'oficina' ou 'historia'")

        corpo = " ".join([s["estado"], s["acao"], s["camera"], s["soundscape"]])
        if RE_DURACAO.search(corpo):
            erros.append(f"{tag} duração escrita no texto (a duração só vai no settings)")
        if RE_FREEZE.search(s["acao"]):
            erros.append(f"{tag} 'freeze/stare/motionless' na ação")
        if RE_CAMERA_OLHAR.search(corpo):
            erros.append(f"{tag} personagem olhando para a câmera")
        if RE_PRECISAO.search(s["acao"]):
            erros.append(f"{tag} exige impacto milimétrico (exactly/precisely)")
        if RE_FALA.search(corpo):
            erros.append(f"{tag} fala/voz/legenda no texto (personagens não falam, sem grunhidos)")
        if RE_HANDOFF.search(s["acao"]):
            avisos.append(f"{tag} possível hand-off de objeto entre personagens")
        if RE_FIM_PARADO.search(s["acao"][-160:]):
            avisos.append(f"{tag} final do plano parece parado (terminar em movimento)")

        cam = s["camera"]
        if RE_CAM_PROIBIDA.search(cam):
            erros.append(f"{tag} câmera proibida (handheld/whip/crash zoom/shake/rápida)")
        movs = {m.group(0).lower() for m in RE_CAM_MOVS.finditer(cam)}
        if len(movs) > 1:
            erros.append(f"{tag} mais de um trabalho de câmera: {sorted(movs)}")
        if "continuous" not in cam.lower():
            avisos.append(f"{tag} câmera sem 'flowing continuously'")
        cam_inicios.append(" ".join(cam.lower().split()[:3]))

        som = s["soundscape"]
        if RE_VAGO.search(som):
            erros.append(f"{tag} soundscape vago (use objeto + ação nomeados)")
        eventos = [e for e in re.split(r",|\bthen\b", som) if e.strip() and SILENCIO not in e]
        if len(eventos) < 3:
            avisos.append(f"{tag} soundscape com menos de 3 eventos nomeados ({len(eventos)})")
        if SILENCIO in som:
            n_silencios += 1

        if i == 0:
            if s["estagio"] != "INTRO" or s["set"] != "oficina" or s["inicio"] != "texto":
                erros.append("[01] o primeiro plano deve ser INTRO, set 'oficina', inicio 'texto'")
        else:
            ant = shots[i - 1]
            if s["inicio"] == "ultimo_frame" and ant.get("set") != s["set"]:
                erros.append(f"{tag} mudança de local exige inicio 'texto' (corte), não 'ultimo_frame'")
            if s["inicio"] == "texto":
                n_cortes += 1

        txt = montar(s, blocos, ep) if s["set"] == "oficina" or "set_historia" in ep else ""
        if len(txt) > LIMITE_CHARS:
            erros.append(f"{tag} prompt com {len(txt)} chars (limite {LIMITE_CHARS})")
        elif len(txt) > AVISO_CHARS:
            avisos.append(f"{tag} prompt com {len(txt)} chars (aviso a partir de {AVISO_CHARS})")

    if ep.get("duracao_total_s") != total:
        erros.append(f"duracao_total_s ({ep.get('duracao_total_s')}) ≠ soma dos planos ({total})")
    if not META_MIN_S <= total <= META_MAX_S:
        avisos.append(f"duração total {total}s fora da meta {META_MIN_S}–{META_MAX_S}s")
    if len(shots) > 1:
        pct = n_cortes / (len(shots) - 1)
        if not 0.25 <= pct <= 0.75:
            avisos.append(f"{pct:.0%} dos planos são corte ('texto'); alvo 25–75%")
    if n_silencios == 0 or n_silencios > 5:
        avisos.append(f"{n_silencios} planos com beat de silêncio (alvo 2–4 nos gags principais)")
    for i in range(2, len(cam_inicios)):
        if cam_inicios[i] == cam_inicios[i - 1] == cam_inicios[i - 2]:
            avisos.append(f"[{i + 1:02d}] três planos seguidos com a mesma abertura de câmera")

    cbs = ep.get("callbacks") or []
    if not cbs:
        erros.append("'callbacks' vazio: todo episódio precisa de ao menos 1 objeto plantado e colhido")
    for cb in cbs:
        try:
            obj, p, c = cb["objeto"].lower(), cb["plantado_shot"], cb["colhido_shot"]
        except KeyError:
            erros.append(f"callback incompleto: {cb}")
            continue
        if not (1 <= p < c <= len(shots)):
            erros.append(f"callback '{obj}': plantado ({p}) deve vir antes de colhido ({c})")
            continue
        sp, sc = shots[p - 1], shots[c - 1]
        if obj not in (sp["estado"] + " " + sp["acao"]).lower():
            avisos.append(f"callback '{obj}' não aparece no estado/ação do plano {p}")
        if obj not in (sc["estado"] + " " + sc["acao"]).lower():
            avisos.append(f"callback '{obj}' não aparece no estado/ação do plano {c}")
    return erros, avisos, total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episodio")
    ap.add_argument("--blocos", default=str(Path(__file__).with_name("blocos_fixos.json")))
    ap.add_argument("--out")
    ap.add_argument("--forcar", action="store_true", help="grava mesmo com erros")
    a = ap.parse_args()

    ep = carregar_json(a.episodio)
    blocos = json.loads(Path(a.blocos).read_text(encoding="utf-8"))
    erros, avisos, total = validar(ep, blocos)

    print(f"Episódio: {ep.get('titulo', '?')} · {len(ep.get('shots', []))} planos · {total}s ({total // 60}:{total % 60:02d})")
    for e in erros:
        print("ERRO  ", e)
    for w in avisos:
        print("AVISO ", w)
    if erros and not a.forcar:
        print(f"\n{len(erros)} erro(s): nada foi gravado. Corrija o JSON (ou use --forcar).")
        sys.exit(1)

    out = Path(a.out) if a.out else Path(a.episodio).with_suffix("").with_name(Path(a.episodio).stem + "_prompts")
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for s in ep["shots"]:
        txt = montar(s, blocos, ep)
        (out / f"shot_{s['n']:02d}.txt").write_text(txt, encoding="utf-8")
        manifest.append({"n": s["n"], "estagio": s["estagio"], "video_length": f"{s['duracao_s']}s",
                         "inicio": s["inicio"], "set": s["set"], "chars": len(txt)})
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(manifest)} prompts gravados em {out}/ · {len(avisos)} aviso(s) · {len(erros)} erro(s)")


if __name__ == "__main__":
    main()
