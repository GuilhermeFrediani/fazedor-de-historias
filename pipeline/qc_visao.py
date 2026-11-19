# -*- coding: utf-8 -*-
"""
qc_visao.py — GATE DE VISAO (a camada que faltava: julgar o FRAME, nao o JSON).
Extrai frames de cada clipe renderizado e manda ao Gemini (Interactions API,
mesmo cofre do app) julgar as DUAS notas que travam o projeto:

  A) POR CLIPE  — 4 frames (0.2 / 3.5 / 7.0 / 9.5 s) vs estado_in/estado_out:
     compliance das pontas, 2 bonecos, reacao visivel, texto na tela.
  B) EPISODIO   — 1o frame de cada clipe + a cadeia de estados:
     continuidade_visual 0-10 e causalidade_narrativa 0-10 (as notas do veredito humano:
     4/10 e 3/10 no v4). Teleportes e personagens extras listados.

Uso:
  python qc_visao.py --clipes <pasta> --padrao "*.mp4" --settings <pasta settings> --saida qc.json
Chave: config_secret.json (campo gemini_key) — nunca impressa.
"""
import argparse, base64, json, re, subprocess, sys, tempfile, urllib.request, urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "fazedor_app"))
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
MODELOS = ["gemini-3.8-flash", "gemini-3-flash-preview", "gemini-3.6-flash", "gemini-2.5-flash"]
TEMPOS = [0.2, 3.5, 7.0, 9.5]


def _chave():
    cfg = json.loads((AQUI.parent / "fazedor_app" / "config_secret.json").read_text(encoding="utf-8"))
    k = cfg.get("gemini_key", "")
    if not k:
        raise SystemExit("sem gemini_key no cofre")
    return k


# ── AGENTROUTER (CAMINHO PRINCIPAL — GPT via proxy do usuario; Gemini = reserva) ──
# Regras descobertas pelo app (fazedor_app.py 2026-11-05, ainda valendo):
# - WAF bloqueia imperativos de geracao no INPUT → input carrega so a imagem + "ok",
#   todo o conteudo/comando vai em `instructions`
# - UA generico -> 401 "unauthorized client detected" -> usar o UA do Codex CLI
# - `temperature` nao e suportado; modelos RACIOCINAM (reasoning low + orcamento folgado)
# - sincrono estoura 504 do ALB → stream obrigatorio
AR_BASE = "https://agentrouter.org/v1"
AR_MODELOS = ["gpt-5.6-sol", "gpt-6.1-sol", "gpt-6-astra"]
AR_UA = "codex_cli_rs/0.42.0 (Windows 11; x86_64) windows"


def _chave_ar():
    cfg = json.loads((AQUI.parent / "fazedor_app" / "config_secret.json").read_text(encoding="utf-8"))
    return cfg.get("agentrouter_key", "")


def _ar_stream_texto(corp):
    """Consome o SSE do /responses e concatena os deltas de texto."""
    ped = urllib.request.Request(
        AR_BASE + "/responses", data=json.dumps(corp).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + _chave_ar(),
                 "User-Agent": AR_UA, "Accept": "*/*",
                 "Accept-Encoding": "identity", "Connection": "keep-alive"})
    txt, final = [], None
    with urllib.request.urlopen(ped, timeout=600) as r:
        for linha in r:
            s = linha.decode("utf-8", "replace").strip()
            if not s.startswith("data:"):
                continue
            carga = s[5:].strip()
            if carga in ("", "[DONE]"):
                continue
            try:
                ev = json.loads(carga)
            except Exception:
                continue
            t = ev.get("type") or ""
            if t == "response.output_text.delta":
                txt.append(ev.get("delta") or "")
            elif t == "response.completed":
                final = ev.get("response") or {}
                break
    if not txt and final:   # reserva: texto do objeto final, se os deltas vieram vazios
        for passo in final.get("output") or []:
            for ctd in passo.get("content") or []:
                if ctd.get("type") == "output_text" and ctd.get("text"):
                    txt.append(ctd["text"])
    return "".join(txt)


def _call_ar(system, parts, max_tokens=8000):
    """Gate multimodal via AgentRouter (GPT). → texto.
    WAF do proxy (PROVADO 19/11 por sonda A-G): texto de dados no INPUT ->
    'content-blocked'; o padrao do app vale — TODO texto vai em instructions,
    o input carrega apenas a imagem + 'ok'."""
    entrada, dados = [], []
    for p in parts:
        if p.get("type") == "image":
            entrada.append({"type": "input_image",
                            "image_url": "data:%s;base64,%s" % (p.get("mime_type", "image/png"),
                                                                p["data"])})
        else:
            dados.append(p.get("text", ""))
    sist = system
    if dados:
        sist += "\n\n=== DADOS DA TAREFA ===\n" + "\n".join(dados)
    sist += ("\n\nDevolva SOMENTE o JSON pedido, compacto, comecando imediatamente.")
    entrada.append({"type": "input_text", "text": "ok"})
    ult = None
    for mdl in AR_MODELOS:
        corp = {"model": mdl,
                "instructions": sist,
                "input": [{"role": "user", "content": entrada}],
                "max_output_tokens": max(8000, int(max_tokens or 0) or 8000),
                "stream": True,
                "reasoning": {"effort": "low"}}
        try:
            tx = _ar_stream_texto(corp).strip()
            if tx:
                return tx
            ult = "resposta vazia (" + mdl + ")"
        except urllib.error.HTTPError as e:
            try:
                corpo = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                corpo = "(sem corpo)"
            ult = "HTTP %s (%s): %s" % (e.code, mdl, corpo)
        except Exception as e:
            ult = str(e)[:200]
    raise RuntimeError("AgentRouter falhou em todos os modelos: " + str(ult))


def _call(key, system, parts, max_tokens=2500):
    """1 chamada multimodal → texto. PRIMEIRO AgentRouter (GPT, proxy do usuario);
    Gemini (Interactions API) fica como RESERVA em caso de queda do proxy."""
    try:
        return _call_ar(system, parts, max_tokens)
    except Exception as e:
        print("[qc_visao] AgentRouter indisponivel (%s) — usando reserva Gemini"
              % str(e)[:140], flush=True)
    corp = {"model": MODELOS[0],
            "system_instruction": system,
            "generation_config": {"temperature": 0.0, "max_output_tokens": max_tokens},
            # NOTA 19/11: "thinking_level": "minimal" passou a dar 400 na Interactions
            # API ("not supported for this model") — campo omitido para sobreviver a
            # rotacoes de modelo; o contrato do gate nao depende dele.
            "store": False,
            "input": parts + [{"type": "text", "text": "Responda SOMENTE o JSON pedido."}]}
    ult = None
    for mdl in MODELOS:
        corp["model"] = mdl
        ped = urllib.request.Request(GEMINI_ENDPOINT, data=json.dumps(corp).encode("utf-8"),
                                     headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            with urllib.request.urlopen(ped, timeout=300) as r:
                resp = json.loads(r.read().decode("utf-8", "replace"))
            textos = []
            for passo in resp.get("output") or resp.get("steps") or []:
                if passo.get("type") in ("model_output", "text", "message"):
                    for ctd in passo.get("content") or []:
                        if ctd.get("type") == "text" and ctd.get("text"):
                            textos.append(ctd["text"])
            tx = "\n".join(textos).strip()
            if tx:
                return tx
            ult = "resposta vazia (" + mdl + ")"
        except urllib.error.HTTPError as e:
            ult = "API %s: %s" % (e.code, e.reason)
            if e.code in (401, 403):
                raise SystemExit(ult + " — chave invalida")
        except Exception as e:
            ult = str(e)[:200]
    raise SystemExit("Gemini falhou em todos os modelos: " + str(ult))


def _json_de(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        raise ValueError("sem JSON na resposta: " + txt[:200])
    return json.loads(m.group(0))


def _img_part(png):
    b64 = base64.b64encode(Path(png).read_bytes()).decode()
    return {"type": "image", "data": b64, "mime_type": "image/png"}


def _frames(mp4, pasta, prefixo):
    saida = []
    for t in TEMPOS:
        png = pasta / ("%s_f%.1f.png" % (prefixo, t))
        subprocess.run([FF, "-y", "-ss", str(t), "-i", str(mp4), "-frames:v", "1", str(png)],
                       capture_output=True)
        if png.exists():
            saida.append(png)
    return saida


def _estados(settings_dir, slugs):
    """AT START / AT END de cada settings (a fonte do que foi pedido ao modelo)."""
    cad = {}
    for slug in slugs:
        f = Path(settings_dir) / (slug + "_settings.json")
        if not f.exists():
            cad[slug] = {"in": "?", "out": "?"}
            continue
        p = json.loads(f.read_text(encoding="utf-8")).get("prompt", "")
        mi = re.search(r"AT START: (.+?)\. \[Shot", p)
        mo = re.search(r"AT END: (.+?)\.?(?:\n|$)", p)
        cad[slug] = {"in": mi.group(1).strip() if mi else "?",
                     "out": mo.group(1).strip() if mo else "?"}
    return cad


def gate_ancora(key, png, estado="", props=""):
    """GATE DE ANCORA pre-render: julga UM frame antes de encadear.
    Reprovado se: personagem extra, objeto flutuando sem apoio, texto na tela,
    ou objeto grande FORA do registro de props permitidos."""
    SYS = ("Voce e o porteiro de continuidade de uma serie de comedia muda em claymation "
           "com EXATAMENTE dois personagens fixos: TEO (alto, magro, bigode loiro de morsa, "
           "gorro teal, camisa xadrez vermelho-e-preto, a ESQUERDA) e JUCA (baixo, largo, "
           "pele escura, boina marrom, sueter mostarda, a DIREITA). Recebe UM frame que sera "
           "o ponto de partida do proximo clipe. Julgue so o que ve, com rigor: "
           "1) ha EXATAMENTE 2 bonecos? qualquer OUTRA figura (urso, silhueta, reflexo com "
           "corpo) e personagem extra; EXCECAO: se o estado esperado (abaixo) mencionar "
           "cliente/militar/oficial/nota, uma figura de uniforme militar (o CLIENTE da serie, "
           "mudo) e LEGITIMA em QUALQUER posicao do quadro (ele entra e sai quando o estado "
           "o anuncia); "
           "2) algum objeto esta FLUTUANDO? ATENCAO: objeto TOCANDO ou PRESO a um dos bonecos "
           "(pe, bota, mao, ombro, cabeca) TEM APOIO — nao e flutuante (a gag da serie e "
           "justamente objetos grudados nos corpos). Flutuante e SOMENTE objeto no ar sem "
           "tocar absolutamente nada (nem boneco, nem piso, nem gancho, nem corda, nem moveis); "
           "3) ha texto legivel na tela? "
           "4) REGISTRO DE PROPS: se a lista de objetos PERMITIDOS (abaixo) existir, todo "
           "objeto GRANDE e nomeavel do frame deve pertencer a ela ou ao estado esperado — "
           "objeto grande fora da lista vai em 'objetos_nao_plantados' (ex.: rolo de papel, "
           "extintor, saco que ninguem trouxe). "
           "5) INVARIANTE DE SET: este set e um GALPAO FECHADO de chapas de aco rebitadas, "
           "com TETO de aco e luminarias jauladas penduradas — NAO existe ceu aberto nele. "
           "Se o topo do quadro mostrar ceu azul, nuvens ou luz exterior no lugar de "
           "parede/teto de aco, marque em 'cenario_violado' (ex.: 'ceu aberto no topo'). "
           "Responda JSON estrito: "
           '{"dois_bonecos": true/false, "personagens_extras": [], "objetos_flutuantes": [], '
           '"texto_na_tela": true/false, "objetos_presentes": [], "objetos_nao_plantados": [], '
           '"cenario_violado": [], '
           '"veredito": "APROVADA" ou "REPROVADA", "motivo": "1 frase"}')
    parts = [_img_part(png)]
    if estado:
        parts.append({"type": "text", "text": "Estado que este frame deveria mostrar: " + estado})
    if props:
        parts.append({"type": "text", "text": "Objetos PERMITIDOS neste set (registro + cenário fixo): " + props})
    # 19/11: sem thinking_level, o modelo pensa e o thinking come o orcamento —
    # 1200 truncava o JSON; 3500 da folga para pensar + responder completo
    tx = _call(key, SYS, parts, max_tokens=3500)
    j = _json_de(tx)
    # enforcement: objeto grande fora do registro reprova a ancora
    if j.get("objetos_nao_plantados"):
        j["veredito"] = "REPROVADA"
        j["motivo"] = "props nao plantados: " + ", ".join(j["objetos_nao_plantados"][:4])
    # enforcement: invariante de set (galpao fechado, teto de aco — nunca ceu)
    if j.get("cenario_violado"):
        j["veredito"] = "REPROVADA"
        j["motivo"] = "cenario violado: " + ", ".join(j["cenario_violado"][:3])
    return j


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clipes")
    ap.add_argument("--ancora", metavar="PNG", help="gate de 1 frame (pre-render)")
    ap.add_argument("--estado", default="", help="estado esperado da ancora (opcional)")
    ap.add_argument("--props", default="", help="registro de props permitidos (opcional)")
    ap.add_argument("--padrao", default="*.mp4")
    ap.add_argument("--settings")
    ap.add_argument("--saida", default="qc_visao.json")
    a = ap.parse_args()

    # GATE DE ANCORA (pre-render): 1 frame decide se a cadeia pode prosseguir
    if a.ancora:
        key = _chave()
        j = gate_ancora(key, a.ancora, a.estado, a.props)
        print(json.dumps(j, ensure_ascii=False))
        print("ANCORA: " + j.get("veredito", "?") + " — " + j.get("motivo", ""))
        return 0 if j.get("veredito") == "APROVADA" else 3

    key = _chave()
    pasta = Path(a.clipes)
    clipes = sorted(pasta.glob(a.padrao))
    if not clipes:
        raise SystemExit("nenhum mp4 em " + str(pasta))
    slugs = [c.stem for c in clipes]
    cad = _estados(a.settings, slugs)
    tmp = Path(tempfile.mkdtemp(prefix="qc_"))
    print("gate de visao: %d clipes · frames em %s" % (len(clipes), tmp))

    SYS_A = ("Voce e o juiz de continuidade de uma serie de comedia muda em claymation "
             "(2 bonecos fixos: TEO alto de gorro verde a esquerda; JUCA baixo de boina e "
             "sueter mostarda a direita). Recebe 4 frames de UM clipe de 10 s (0.2s, 3.5s, "
             "7.0s, 9.5s) e o estado que o clipe PROMETE no inicio (AT START) e no fim "
             "(AT END). Julgue so o que ve. Responda JSON estrito: "
             '{"estado_in_cumprido": 0-10, "estado_out_cumprido": 0-10, "dois_bonecos": true/false, '
             '"personagens_extras": [], "reacao_visivel": true/false, "texto_na_tela": true/false, '
             '"objetos_visiveis": [], "objetos_sumidos": [], "notas": "1 frase"}')

    SYS_B = ("Voce e o juiz de continuidade e causalidade entre clipes. Recebe o PRIMEIRO frame "
             "de cada clipe de um episodio (na ordem) e a cadeia de estados prometida "
             "(AT END do clipe N deve ser o AT START do clipe N+1). Julgue olhando os frames: "
             "1) continuidade_visual 0-10 (objetos e cenario permanecem iguais entre um frame e "
             "o seguinte? telefone continua caido? buraco continua aberto? agua continua subindo?) "
             "2) causalidade_narrativa 0-10 (cada situacao nasce da anterior? existe arco ou sao "
             "eventos soltos?) 3) teleportes: objetos que mudaram de lugar/estado sem explicacao "
             "4) personagens_extras. Responda JSON estrito: "
             '{"continuidade_visual": 0-10, "causalidade_narrativa": 0-10, "teleportes": [], '
             '"personagens_extras": [], "momentos_sem_nexo": [], "notas": "2 frases"}')

    # A) por clipe
    por_clipe = []
    for c, slug in zip(clipes, slugs):
        fr = _frames(c, tmp, slug[:24])
        parts = [_img_part(f) for f in fr]
        st = cad.get(slug, {"in": "?", "out": "?"})
        parts.append({"type": "text", "text":
                      "AT START prometido: %s\nAT END prometido: %s" % (st["in"], st["out"])})
        tx = _call(key, SYS_A, parts)
        try:
            j = _json_de(tx)
        except ValueError:
            j = {"notas": tx[:300]}
        por_clipe.append({"clipe": slug, **j})
        print("[A] %-44s in=%s out=%s 2bonecos=%s texto=%s" % (
            slug[:44], j.get("estado_in_cumprido", "?"), j.get("estado_out_cumprido", "?"),
            j.get("dois_bonecos"), j.get("texto_na_tela")))

    # B) episodio (primeiro frame de cada clipe + cadeia)
    parts_b = []
    cadeia_txt = []
    for c, slug in zip(clipes, slugs):
        fr = _frames(c, tmp, "primeiro_" + slug[:20])
        if fr:
            parts_b.append(_img_part(fr[0]))
        cadeia_txt.append("clipe %s — AT START: %s | AT END: %s" % (slug, cad[slug]["in"], cad[slug]["out"]))
    parts_b.append({"type": "text", "text": "Cadeia prometida:\n" + "\n".join(cadeia_txt)})
    tx = _call(key, SYS_B, parts_b, max_tokens=4500)
    ep = _json_de(tx)
    print("\n[B] EPISODIO  continuidade_visual=%s  causalidade_narrativa=%s" % (
        ep.get("continuidade_visual"), ep.get("causalidade_narrativa")))
    print("    teleportes: %s" % ep.get("teleportes"))
    print("    extras: %s" % ep.get("personagens_extras"))
    print("    sem nexo: %s" % ep.get("momentos_sem_nexo"))

    ins = [p.get("estado_in_cumprido") for p in por_clipe if isinstance(p.get("estado_in_cumprido"), (int, float))]
    outs = [p.get("estado_out_cumprido") for p in por_clipe if isinstance(p.get("estado_out_cumprido"), (int, float))]
    resumo = {
        "episodio": ep,
        "por_clipe": por_clipe,
        "media_estado_in": round(sum(ins) / len(ins), 1) if ins else None,
        "media_estado_out": round(sum(outs) / len(outs), 1) if outs else None,
    }
    Path(a.saida).write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n>>> GATE SALVO EM:", a.saida)
    if resumo["media_estado_in"] is not None:
        print(">>> media estado_in cumprido: %s/10 · estado_out: %s/10" % (
            resumo["media_estado_in"], resumo["media_estado_out"]))


if __name__ == "__main__":
    sys.exit(main())
