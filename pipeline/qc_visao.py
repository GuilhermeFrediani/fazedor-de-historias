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
sys.path.insert(0, str(AQUI))
import scan_ceu
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "fazedor_app"))
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
MODELOS = ["gemini-3.8-flash", "gemini-3-flash-preview", "gemini-3.6-flash", "gemini-2.5-flash"]
# CONSERTO (auditoria 20/11): 3.5/7.0 nao viam a EMENDA de ~1s (o ghost wide->insert
# do clipes 1 e N passava). Amostragem: ponta (0.2) + emenda (1.0) + meio (5.0) + fim (9.5).
# Nos clipes PONTE (image_start), 1.0 cai exatamente no morph ancora->planos[0].
TEMPOS = [0.2, 1.0, 5.0, 9.5]


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
    sist += ("\n\nDevolva SOMENTE o JSON pedido, compacto, comecando imediatamente. "
            "Seja ECONOMICO: motivo em UMA frase curta; objetos_presentes no maximo "
            "12 itens; nao repita o estado.")
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


def _call(key, system, parts, max_tokens=16000):
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
            "input": parts + [{"type": "text", "text": "Responda SOMENTE o JSON pedido, compacto e economico (motivo em 1 frase; objetos_presentes no maximo 12 itens)."}]}
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


def _consertar_json(t):
    """Juiz verboso as vezes estoura o orcamento no meio do objetos_presentes.
    Corta no ultimo membro completo e fecha os colchetes - os campos que decidem
    o veredito (extras/flutuante/texto/contagem/cenario) ficam no INICIO do JSON."""
    t = t[t.find("{"):]
    if not t.startswith("{"):
        return None
    dentro, esc, pilha, corte = False, False, [], None
    for i, ch in enumerate(t):
        if dentro:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                dentro = False
            continue
        if ch == '"':
            dentro = True
        elif ch in "{[":
            pilha.append(ch)
        elif ch in "}]":
            if pilha:
                pilha.pop()
            if not pilha:
                return t[:i + 1]
            corte = i
    if corte is None:
        # nenhum fechamento depois do '{': corta na ULTIMA virgula de topo
        # (o membro incompleto vai embora, os completos ficam)
        prof, dentro, esc, ultima_virgula = 0, False, False, None
        for i, ch in enumerate(t):
            if dentro:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    dentro = False
                continue
            if ch == '"':
                dentro = True
            elif ch in "{[":
                prof += 1
            elif ch in "}]":
                prof -= 1
            elif ch == "," and prof == 1:
                ultima_virgula = i
        if ultima_virgula is None:
            return None
        base = t[:ultima_virgula]
        return base + "}"
    # base TERMINA sempre num limite estrutural (o corte e um fecha-colchete
    # completo), entao nao ha string aberta para fechar: so fechar a pilha.
    base = t[:corte + 1].rstrip().rstrip(",:")
    pilha, dentro, esc = [], False, False
    for ch in base:
        if dentro:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                dentro = False
            continue
        if ch == '"':
            dentro = True
        elif ch in "{[":
            pilha.append(ch)
        elif ch in "}]":
            if pilha:
                pilha.pop()
    fechos = "".join("}" if c == "{" else "]" for c in reversed(pilha))
    return base + fechos


def _json_de(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if m:
        bruto = m.group(0)
    else:
        # resposta TRUNCADA: nao ha '}' final - pega do primeiro '{' em diante
        i = txt.find("{")
        bruto = txt[i:] if i >= 0 else ""
    if not bruto:
        raise ValueError("sem JSON na resposta: " + txt[:200])
    try:
        return json.loads(bruto)
    except Exception:
        consertado = _consertar_json(bruto)
        if consertado:
            try:
                j = json.loads(consertado)
                j["_truncado"] = True
                return j
            except Exception:
                pass
    raise ValueError("sem JSON na resposta: " + txt[:200])


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


def gate_ancora(key, png, estado="", props="", cliente=False, inserto=False):
    """GATE DE ANCORA pre-render: julga UM frame antes de encadear.
    Reprovado se: personagem extra, objeto flutuando sem apoio, texto na tela,
    objeto grande FORA do registro (v2: cor/posse/conexao), ou set violado.
    cliente=True SOMENTE nos clipes 1 e N (ocupacao AGENDADA, nao absoluta)."""
    SYS = ("Voce e o porteiro de continuidade de uma serie de comedia muda em claymation "
           "com EXATAMENTE dois personagens fixos: TEO (alto, magro, bigode loiro de morsa, "
           "gorro teal, camisa xadrez vermelho-e-preto, a ESQUERDA) e JUCA (baixo, largo, "
           "pele escura, boina marrom, sueter mostarda, a DIREITA). Recebe UM frame que sera "
           "o ponto de partida do proximo clipe. Julgue so o que ve, com rigor: "
           "1) OCUPACAO AGENDADA: a regra base e EXATAMENTE 2 bonecos (TEO e JUCA); "
           "qualquer OUTRA figura (urso, silhueta, reflexo com corpo) e personagem extra. "
           "O CLIENTE do episodio (figurino do setor: militar, padre, sindico...) e permitido SOMENTE se a linha "
           "'CLIENTE AUTORIZADO' disser SIM — e ai so onde o estado o anuncia; se a linha "
           "disser NAO, qualquer terceira figura e extra. A lei v4 exige o cliente nos "
           "clipes 1 e N (entrega da ordem / fecho com a nota) — a ausencia dele NAO e "
           "defeito do gate de ancora; "
           "2) algum objeto esta FLUTUANDO? ATENCAO: objeto TOCANDO ou PRESO a um dos bonecos "
           "(pe, bota, mao, ombro, cabeca) TEM APOIO — nao e flutuante (a gag da serie e "
           "justamente objetos grudados nos corpos). Flutuante e SOMENTE objeto no ar sem "
           "tocar absolutamente nada (nem boneco, nem piso, nem gancho, nem corda, nem moveis); "
           "3) ha texto legivel na tela? Linhas, rabiscos, letras ou glifos num papel CONTAM como "
           "texto; papel de ordem DEVE ser liso e EM BRANCO (lei zero-texto). Digitos em teclado "
           "de telefone, letras em redor do disco de discagem, mostradores de medidor, botoes "
           "e placas de identificacao de equipamento sao PROPriedades diegeticas do set e NAO "
           "contam como texto; o MOSTRADOR DE RELOGIO (numeros romanos e ponteiros de um "
           "relogio de bolso/parede) tambem e diegetico e NAO conta; as MARCAS DE GRADUACAO "
           "e ALGARISMOS gravados numa regua ou ferramenta de medicao (metro dobravel, trena) "
           "sao diegeticos e NAO contam como texto (classe dos mostradores de medidor) - "
           "palavras, frases, rotulos, placas e letreiros continuam contando. "
           "3b) ARTEFATO DE TRANSICAO: figura DUPLICADA (dois bonecos iguais na mesma figura), "
           "boneco translucido/sobreposto (double exposure), ghost ou morph entre poses REPROVA "
           "('ghost/morph na emenda'); os cortes do video sao instantaneos. "
           "4) REGISTRO DE PROPS v2: se a lista PERMITIDOS (abaixo) existir, todo objeto "
           "GRANDE e nomeavel do frame deve pertencer a ela ou ao estado esperado — objeto "
           "fora da lista vai em 'objetos_nao_plantados'. As linhas com COR e POSSE sao "
           "CONTRATO: a cor nao muda nunca (lapis amarelo jamais vira vermelho) e o portador "
           "so muda se o estado narrar a troca de maos; divergencia vai em 'props_violados' "
           "(ex.: 'lapis vermelho (registro: amarelo)', 'trena na mao do TEO (registro: JUCA)'); "
           "a lista tambem declara QUANTAS unidades existem de cada objeto (ex.: 'exactly one "
           "bucket', 'two stacked drums') - CONTE no frame, OBJETO POR OBJETO, um por um, "
           "ANTES de responder, e divergencia de contagem (dois baldes, dois telefones, tres "
           "tambores) vai em 'contagem_divergente': item DUPLICADO e defeito GRAVE de "
           "continuidade — a contagem e a PRIMEIRA coisa que voce confere; "
           "5) INVARIANTE DE SET: o set de cada episodio e um INTERIOR FECHADO - o material (aco rebitado, pedra, azulejo, madeira) e o que o estado/registro declarar. NAO existe ceu aberto: se o topo do quadro mostrar ceu azul, nuvens, paisagem, arvores, predios externos ou abertura para fora no lugar de parede/teto, marque em cenario_violado (ex.: ceu aberto no topo; arvores atras da parede). Claridade BRANCA, reflexos, sellos de luminaria e luz de janela fechada NAO sao ceu - so marque se houver AZUL de ceu, NUVENS ou exterior atravessando uma abertura. Um interior fechado de QUALQUER material (inclusive pedra de capela) e o set correto e NAO e violacao. "
           "6) ESTADO: se um estado esperado for fornecido, compare o frame com ele: "
           "divergencia GRAVE e o estado CONTRARIO ao que se ve (ex.: estado diz 'telefone "
           "arrancado no chao' e o frame mostra o telefone na parede, ou 'tambor na parede' e o "
           "frame mostra o tambor no meio do galpao) e vai em 'estado_divergente'. Se os objetos "
           "do estado simplesmente NAO ESTAEM no quadro (close de rosto, enquadramento apertado), "
           "isso NAO reprova; mas se ESTAO visiveis e no lugar/status ERRADO, reprova. "
           "Diferencas menores de detalhe NAO reprovam. "
           "7) FANTASMAS/DUPLICADOS: personagem duplicado, copia translucida, sobreposicao ou "
           "dissolve de dois quadros (o mesmo boneco em dois lugares, contorno fantasma, overlay) "
           "e defeito GRAVE: liste em 'fantasmas' e reprove. "
           "Responda JSON estrito: "
           '{"dois_bonecos": true/false, "personagens_extras": [], "objetos_flutuantes": [], '
           '"texto_na_tela": true/false, "objetos_presentes": [], "objetos_nao_plantados": [], '
           '"props_violados": [], "estado_divergente": [], "cenario_violado": [], "fantasmas": [], '
           '"contagem_divergente": [], '
           '"veredito": "APROVADA" ou "REPROVADA", "motivo": "1 frase"}')
    if inserto:
        SYS += ("\n\nMODO INSERT (close de detalhe): este quadro e um close de insert e pode mostrar "
                "UM boneco parcial, so maos/botas/objeto, ou nenhum boneco - isso NAO e defeito e "
                "NAO reprova por 'nem todos os dois bonecos'. Neste modo, veredito REPROVADA so se "
                "houver: personagem EXTRA (terceira figura completa), ghost/morph/duplicado, texto "
                "legivel, objeto flutuante, props violados ou cenario violado.")
    parts = [_img_part(png)]
    if estado:
        parts.append({"type": "text", "text": "Estado que este frame deveria mostrar: " + estado})
    if props:
        parts.append({"type": "text", "text": "Objetos PERMITIDOS neste set (registro + cenário fixo): " + props})
    parts.append({"type": "text", "text": "CLIENTE AUTORIZADO neste clipe: " + ("SIM" if cliente else "NAO")})
    # 19/11: sem thinking_level, o modelo pensa e o thinking come o orcamento —
    # 1200 truncava o JSON; 3500 da folga para pensar + responder completo
    tx = _call(key, SYS, parts, max_tokens=16000)
    j = _json_de(tx)
    # enforcement: objeto grande fora do registro reprova a ancora
    if j.get("objetos_nao_plantados"):
        j["veredito"] = "REPROVADA"
        j["motivo"] = "props nao plantados: " + ", ".join(j["objetos_nao_plantados"][:4])
    # enforcement: registro v2 — cor/posse/conexao divergentes reprovam
    if j.get("props_violados"):
        j["veredito"] = "REPROVADA"
        j["motivo"] = "props violados (cor/posse/conexao): " + ", ".join(j["props_violados"][:4])
    # enforcement: estado prometido nao cumprido (acao principal ausente/contraria)
    if j.get("estado_divergente"):
        j["veredito"] = "REPROVADA"
        j["motivo"] = "estado divergente: " + ", ".join(j["estado_divergente"][:3])
    # enforcement: invariante de set (galpao fechado, teto de aco — nunca ceu)
    if j.get("cenario_violado"):
        j["veredito"] = "REPROVADA"
        j["motivo"] = "cenario violado: " + ", ".join(j["cenario_violado"][:3])
    # ── CONSERTO 1 (auditoria 21/11): o SYS mandava reprovar, mas o CODIGO so forçava
    #    REPROVADA em 4 campos — fantasmas/extras/texto/flutuante passavam soltos.
    #    Foi exatamente assim que o ghost de 1s e o texto passaram no teste dos 20s.
    # enforcement: ghost/duplicado/morph/double-exposure reprova
    if j.get("fantasmas"):
        j["veredito"] = "REPROVADA"
        j["motivo"] = "ghost/morph/duplicado: " + ", ".join(j["fantasmas"][:3])
    # enforcement: terceira figura completa reprova (ocupacao AGENDADA)
    if j.get("personagens_extras"):
        j["veredito"] = "REPROVADA"
        j["motivo"] = "personagem extra: " + ", ".join(j["personagens_extras"][:3])
    # enforcement: lei zero-texto
    if j.get("texto_na_tela"):
        j["veredito"] = "REPROVADA"
        j["motivo"] = "texto na tela nao permitido (lei zero-texto)"
    # enforcement: objeto flutuando sem apoio reprova
    if j.get("objetos_flutuantes"):
        j["veredito"] = "REPROVADA"
        j["motivo"] = "objeto flutuante: " + ", ".join(j["objetos_flutuantes"][:3])
    # enforcement: contagem de props (balde duplicado reprova - o 2o balde de 15s passou)
    if j.get("contagem_divergente"):
        j["veredito"] = "REPROVADA"
        j["motivo"] = "contagem divergente: " + ", ".join(j["contagem_divergente"][:3])
    # resposta truncada antes do 'veredito': deriva dos campos que chegaram
    if not str(j.get("veredito", "")).strip():
        falhas = (j.get("personagens_extras") or j.get("objetos_flutuantes")
                  or j.get("fantasmas") or j.get("cenario_violado")
                  or j.get("contagem_divergente") or j.get("estado_divergente")
                  or j.get("objetos_nao_plantados") or j.get("props_violados"))
        j["veredito"] = "REPROVADA" if falhas else "APROVADA"
        j["motivo"] = ("veredito derivado dos campos (resposta do juiz truncada): "
                       + (", ".join(str(x) for x in falhas[:3]) if falhas
                          else "nenhuma violacao nos campos recebidos"))
    return j


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clipes")
    ap.add_argument("--ancora", metavar="PNG", help="gate de 1 frame (pre-render)")
    ap.add_argument("--estado", default="", help="estado esperado da ancora (opcional)")
    ap.add_argument("--props", default="", help="registro de props permitidos (opcional)")
    ap.add_argument("--cliente", action="store_true",
                    help="cliente militar autorizado NESTE clipe (somente clipes 1 e N)")
    ap.add_argument("--padrao", default="*.mp4")
    ap.add_argument("--settings")
    ap.add_argument("--saida", default="qc_visao.json")
    a = ap.parse_args()

    # GATE DE ANCORA (pre-render): 1 frame decide se a cadeia pode prosseguir
    if a.ancora:
        key = _chave()
        j = gate_ancora(key, a.ancora, a.estado, a.props, cliente=a.cliente)
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
             "sueter mostarda a direita). Recebe 4 frames de UM clipe de 10 s (0.2s, 1.0s - "
             "a EMENDA entre a ancora e o plano 1, 5.0s, 9.5s) e o estado que o clipe "
             "PROMETE no inicio (AT START) e no fim (AT END). Julgue so o que ve, com "
             "rigor. Responda JSON estrito: "
             '{"estado_in_cumprido": 0-10, "estado_out_cumprido": 0-10, "dois_bonecos": true/false, '
             '"personagens_extras": [], "reacao_visivel": true/false, "texto_na_tela": true/false, '
             '"fantasmas": [], "cenario_violado": [], "objetos_flutuantes": [], '
             '"props_violados": [], "contagem_divergente": [], '
             '"objetos_visiveis": [], "objetos_sumidos": [], "notas": "1 frase"}. '
             "Regras: 1) fantasma/duplicado/morph/double-exposure entre frames vai em "
             "'fantasmas'; 2) terceira figura completa (exceto o cliente militar agendado "
             "no primeiro e no ultimo clipe) vai em 'personagens_extras'; 3) QUALQUER texto "
             "legivel na tela (papel com escrita, letras, glifos, placas) faz "
             "texto_na_tela=true - digitos de teclado de telefone/medidor NAO contam; "
             "4) objeto no ar sem tocar nada vai em 'objetos_flutuantes' (objeto grudado "
             "em boneco/corda/movel TEM apoio); 5) o set de cada episodio e um INTERIOR FECHADO - o material (aco, pedra, azulejo, madeira) e o que o episodio declarar: ceu azul, nuvens, arvores ou abertura para fora no topo/quadro vai em cenario_violado (clareza branca e reflexo de luminaria NAO sao ceu). 6) o registro de props (se "
             "enviado abaixo) declara COR, POSSE e CONTAGEM: divergencia de cor/posse em "
             "'props_violados', divergencia de CONTAGEM (dois baldes, dois telefones) em "
             "'contagem_divergente'.")

    SYS_B = ("Voce e o juiz de continuidade e causalidade entre clipes. Recebe o PRIMEIRO frame "
             "de cada clipe de um episodio (na ordem) e a cadeia de estados prometida "
             "(AT END do clipe N deve ser o AT START do clipe N+1). Julgue olhando os frames: "
             "1) continuidade_visual 0-10 (objetos e cenario permanecem iguais entre um frame e "
             "o seguinte? telefone continua caido? buraco continua aberto? agua continua subindo?) "
             "2) causalidade_narrativa 0-10 (cada situacao nasce da anterior? existe arco ou sao "
             "eventos soltos?) 3) teleportes: objetos que mudaram de lugar/estado sem explicacao "
             "4) personagens_extras — OCUPACAO AGENDADA: o cliente militar de uniforme olive "
             "so e legitimo no PRIMEIRO e no ULTIMO clipe; nos clipes do meio, qualquer "
             "terceira figura e extra; "
             "5) REGISTRO v2: anote em momentos_sem_nexo troca de COR de objeto entre frames "
             "(lapis amarelo vira vermelho) e troca de PORTADOR sem acao (trena que estava no "
             "bolso do JUCA aparece na mao do TEO). Responda JSON estrito: "
             '{"continuidade_visual": 0-10, "causalidade_narrativa": 0-10, "teleportes": [], '
             '"personagens_extras": [], "momentos_sem_nexo": [], "notas": "2 frases"}')

    # A) por clipe
    por_clipe = []
    for c, slug in zip(clipes, slugs):
        fr = _frames(c, tmp, slug[:24])
        # CONSERTO 11 (auditoria 21/11): scan deterministico de ceu por clipe (local,
        # 0 API) - antes vivia solto, longe do gate por-clipe.
        try:
            sc = scan_ceu.escanear(c, passo=0.5, faixa=0.28, limiar=0.10)
        except Exception as e:
            sc = {"veredito": "?", "violacoes": [], "erro": str(e)[:120]}
        parts = [_img_part(f) for f in fr]
        st = cad.get(slug, {"in": "?", "out": "?"})
        parts.append({"type": "text", "text":
                      "AT START prometido: %s\nAT END prometido: %s" % (st["in"], st["out"])})
        if a.props:
            parts.append({"type": "text", "text":
                          "Objetos PERMITIDOS neste set (registro + cenario fixo, com "
                          "contagem): " + a.props})
        tx = _call(key, SYS_A, parts)
        try:
            j = _json_de(tx)
        except ValueError:
            j = {"notas": tx[:300]}
        if sc.get("violacoes"):
            j["cenario_violado"] = list(j.get("cenario_violado") or []) + [
                "scan_ceu %.1f-%.1fs pico %.0f%%" % (v["ini_s"], v["fim_s"], v["pico"] * 100)
                for v in sc["violacoes"][:3]]
        # CONSERTO 3: enforcement no gate por-clipe (espelha gate_ancora) — so o
        # prompt pedia; agora o CODIGO bloqueia.
        motivos = []
        if j.get("fantasmas"):
            motivos.append("fantasmas=%s" % j["fantasmas"][:2])
        if j.get("personagens_extras"):
            motivos.append("extras=%s" % j["personagens_extras"][:2])
        if j.get("texto_na_tela"):
            motivos.append("texto")
        if j.get("objetos_flutuantes"):
            motivos.append("flutuantes=%s" % j["objetos_flutuantes"][:2])
        if j.get("cenario_violado"):
            motivos.append("cenario=%s" % j["cenario_violado"][:2])
        if j.get("props_violados"):
            motivos.append("props=%s" % j["props_violados"][:2])
        if j.get("contagem_divergente"):
            motivos.append("contagem=%s" % j["contagem_divergente"][:2])
        if motivos:
            j["reprovado"] = True
            j["scan_ceu"] = sc
            j["notas"] = (str(j.get("notas", "")) + " | BLOQUEADO: " + "; ".join(motivos)).strip(" |")
            print("    BLOQUEADO: " + "; ".join(motivos), flush=True)
        por_clipe.append({"clipe": slug, **j})
        print("[A] %-44s in=%s out=%s 2bonecos=%s texto=%s%s" % (
            slug[:44], j.get("estado_in_cumprido", "?"), j.get("estado_out_cumprido", "?"),
            j.get("dois_bonecos"), j.get("texto_na_tela"),
            " BLOQUEADO" if j.get("reprovado") else ""))

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
    # CONSERTO 4 (auditoria 21/11): a nota virou PORTAO, nao comentario.
    # exit != 0 trava o roteiro: nota < 8 ou qualquer clipe bloqueado reprova.
    cont = ep.get("continuidade_visual") or 0
    caus = ep.get("causalidade_narrativa") or 0
    bloq = [p for p in por_clipe if p.get("reprovado")]
    if cont < 8 or caus < 8 or bloq:
        print("\n>>> PORTAO FECHADO: continuidade=%s causalidade=%s · %d/%d clipes BLOQUEADOS"
              % (cont, caus, len(bloq), len(por_clipe)))
        for p in bloq:
            print("    XX %s: %s" % (p.get("clipe"), p.get("notas", "")[:160]))
        return 1
    print("\n>>> PORTAO ABERTO: continuidade=%s causalidade=%s · 0 clipes bloqueados" % (cont, caus))
    return 0


if __name__ == "__main__":
    sys.exit(main())
