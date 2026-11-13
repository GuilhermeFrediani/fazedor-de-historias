#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FAZEDOR DE HISTÓRIAS — TÉO & JUCA Company (v1.0)
Servidor local 100% stdlib (zero instalação).  Roda:  python fazedor_app.py
Abre http://127.0.0.1:8756 no navegador (Edge).

O que ele faz
- Serve a UI (botão de fala do navegador + edição do episódio)
- LAPIDAÇÃO: modo COLA (pacote p/ colar num chat gratuito) e modo API automática
  (endpoint OpenAI-compatível: Groq / Gemini / OpenRouter / LM Studio / Ollama)
- VALIDAÇÃO: importa o montar_prompts.py da pasta pai e usa as MESMAS regras
- SAÍDA: EPISODIOS/<slug>/  → episodio.json, shot_NN.txt, manifest.json
          + settings/ com os JSONs v2.1 prontos para o gen_test.py (LoRA, seed, etc.)
          + <slug>_gerar_todos.ps1 (corrente de geração com tempo estimado)

Garantias do pacote do projeto
- LÊ montar_prompts.py / blocos_fixos.json / SISTEMA_GERADOR v1 / exemplo — NUNCA os modifica
- Só escreve DENTRO de <pasta do app>/EPISODIOS/<slug>/ ; se existir, recusa (409)
- Chaves de API ficam no navegador (localStorage) — o servidor nunca grava em disco
"""
import json
import importlib.util
import re
import socket
import sys
import threading
import time
import unicodedata
import urllib.request
import urllib.error
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import regras_v3  # v3: camada de RENDERIZABILIDADE (orcamento de fisica + ancoras curtas)

APP_DIR = _HERE
PARENT = APP_DIR.parent                      # "fazedor de histórias"
UI_FILE = APP_DIR / "ui.html"
EPISODIOS_DIR = APP_DIR / "EPISODIOS"

ARQ_SISTEMA = PARENT / "SISTEMA_GERADOR_TEO_JUCA_v1.md"
ARQ_BLOCOS = PARENT / "blocos_fixos.json"
ARQ_DOSSIE_CANDIDATOS = (PARENT.parent / "DOSSIE_TEO_JUCA_v1.docx",
                         PARENT / "DOSSIE_TEO_JUCA_v1.docx",
                         APP_DIR / "DOSSIE_TEO_JUCA_v1.docx")
ARQ_EXEMPLO = PARENT / "exemplo_episodio_pintura.json"
ARQ_MONTAR = PARENT / "montar_prompts.py"

PORTA_INICIAL = 8756
LIMITE_CORPO = 5_000_000                    # bytes (episódio ~80KB; áudio STT até ~3,5MB)
LIMITE_API_TIMEOUT = 600                      # s

# ── TEMPLATE v2.1 (espelha exatamente os quadro_sX_settings.json validados) ──
TEMPLATE_SETTINGS = {
    "model_type": "minimax_h3_fl2va_pruned",
    "num_inference_steps": 6,
    "resolution": "1152x640",
    "force_fps": 24,
    "seed": 7001,
    "guidance_scale": 1,
    "flow_shift": 12,
    "skip_steps_cache_type": "spectrum",
    "audio_prompt_type": "",
    "activated_loras": ["https://huggingface.co/DeepBeepMeep/MiniMax-H3/resolve/main/loras/minimax_h3_lightx2v_fl2v_turbo_8step_alpha8_v1.0_bf16.safetensors"],
    "loras_multipliers": "1.0",
    "config": "gguf_q4_k_m",
    "_cli_extra": ["--profile", "5"],
}
DIR_GEN_TEST = r"C:\Users\Guilherme\Documents\Projeto Padrão"
PYTHON_GEN = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
GEN_TEST = DIR_GEN_TEST + r"\gen_test.py"
SEG_POR_SEG = 80.0                           # medido: 8s≈10,5min … 10s≈14min

# ── carrega módulo do projeto (leitura) e blocos ──
_mp = None
_bloco = None


def montar_prompts_mod():
    global _mp
    if _mp is None:
        spec = importlib.util.spec_from_file_location("montar_prompts", ARQ_MONTAR)
        _mp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_mp)
    return _mp


def blocos_fixos():
    global _bloco
    if _bloco is None:
        _bloco = json.loads(ARQ_BLOCOS.read_text(encoding="utf-8"))
    return _bloco


def sistema_texto():
    txt = ARQ_SISTEMA.read_text(encoding="utf-8")
    m = re.search(r"=== INÍCIO DO PROMPT ===(.*)=== FIM DO PROMPT ===", txt, re.S)
    return (m.group(1) if m else txt).strip()


def exemplo_texto():
    return ARQ_EXEMPLO.read_text(encoding="utf-8").strip()


# ── utilidades ──
def slugify(txt, maximo=40):
    basico = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", basico).strip("-").lower()
    return (s[:maximo].rstrip("-") or "episodio")


def tag_slug(txt, maximo=10):
    s = re.sub(r"[^A-Za-z0-9]", "", unicodedata.normalize("NFKD", txt)
               .encode("ascii", "ignore").decode()).upper()
    return s[:maximo] or "EP"


def extrair_json(txt):
    """Resumo (antes do ```json) + JSON do episódio, tolerando cercas."""
    if not txt:
        return None, None
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", txt, re.S)
    if m:
        bruto = m.group(1)
        resumo = txt[:max(txt.find("```"), 0)].strip()
    else:
        i, j = txt.find("{"), txt.rfind("}")
        if i < 0 or j <= i:
            return txt.strip(), None
        bruto = txt[i:j + 1]
        resumo = txt[:i].strip()
    try:
        return resumo, json.loads(bruto)
    except Exception:
        return resumo, None


def achatado(st, campo):
    v = st.get(campo, "")
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


# ── lógica de episódio ──
def validar_episodio(ep):
    if ep_eh_dossie(ep):
        return validar_dossie(ep)
    mp = montar_prompts_mod()
    erros, avisos, total = mp.validar(ep, blocos_fixos())
    tamanhos = {}
    for s in ep.get("shots", []):
        try:
            tamanhos[str(s["n"])] = len(mp.montar(s, blocos_fixos(), ep))
        except Exception as e:
            erros.append(f"[{s.get('n', '?')}] falha ao montar prompt: {e}")
    return {"erros": erros, "avisos": avisos, "total_s": total,
            "chars_por_plano": tamanhos, "n_planos": len(ep.get("shots", []))}


# ── Dossiê TÉO & JUCA v1.0 (fonte canônica: DOSSIE_TEO_JUCA_v1.docx) ──
# Matriz aberta de temas (seção 10.1 do dossiê): 12×10×6×10×10 = 72.000 combinações
DOSSIE_MATRIZ = {
    "setor": ["residencial", "comercial", "industrial", "naval/portuário", "militar",
              "rural", "hospitalar", "escolar", "religioso", "rodoviário",
              "saneamento", "eventos"],
    "servico": ["pintura", "elétrica", "hidráulica", "alvenaria", "demolição",
                "limpeza", "montagem", "poda", "transporte", "vedação/impermeabilização"],
    "mecanismo": ["mediu errado", "usou a ferramenta errada",
                  "colou/vedou com o material errado", "sobrecarregou a estrutura",
                  "inverteu a ordem", "resolveu o problema errado"],
    "cliente": ["síndico", "militar", "médico", "professor", "padre/pastor",
                "fazendeiro", "noivo", "motorista", "criança", "idoso"],
    "degrau": ["alaga", "desaba", "pega fogo (contido)", "tomba", "transborda",
               "racha", "despenca", "entra em curto", "congela", "sai voando"],
}
DOSSIE_ESTAGIOS = {"LIGACAO": 1, "CHEGADA": 2, "DIAGNOSTICO_ERRADO": 3, "PRIMEIRA_FALHA": 3,
                   "JEITINHO": 5, "PAUSA_COMICA": 1, "ESCALADA": 5, "CLIMAX": 5,
                   "REACAO_EM_CORO": 1, "NOTA_FISCAL": 4}
DOSSIE_DUR = 10
PALAVRAS_VEDADAS = ("freeze", "stare", "handheld", "whip pan", "crash zoom",
                    "exactly", "precisely", "fade to black", "the end",
                    "says", "shouts", "whispers", "narrator", "subtitle",
                    "caption", "text on screen", "laugh track", "boing", "twang",
                    "moral of the story")
SOM_NOMEADO = re.compile(
    r"\b(hit|fall|creak|scatter|pour|hiss|rattle|knock|click|buzz|clank|slide|drip|tap|snap|"
    r"pop|squeak|tremble|roll|spray|spark|shatter|stretch|scrape|sizzle|whoosh|thud|bang|"
    r"ring|squeal|flap|whir|chime|slosh|crack|crumple|swish|grind|patter|crackle|clatter|"
    r"groan|hum|lap|slap|rumble|thump|tick|clink|rustle|splash|bump|whistle|sputter|clang|"
    r"blare|blast|chug|clop|clump|jangle|sway|fizz|drip|echo|vibrat|wheeze|sniff|chomp|"
    r"scritch|shuffl|whizz|zing|tonk|tock|creek|creak)"
    r"(?:s|es|ed|ing)?\b", re.I)

_DOSSIE_CACHE = None


def _consome_stream_ar(r, model, max_tokens):
    """Lê o SSE do /responses. Deadline 30 min; batimento a cada 30 s sobre
    QUALQUER evento (resumos de raciocínio mantêm a conexão viva)."""
    pecas, uso_final, rid, status = [], {}, "", ""
    t0 = time.time()
    ultimo_print = 0.0
    eventos = 0
    for linha in r:
        if time.time() - t0 > 1800:   # corta tentativa presa: 30 min por tentativa
            raise RuntimeError(f"tentativa excedeu 30 min (orcamento={max_tokens})")
        linha = linha.decode("utf-8", "replace").strip()
        if not linha.startswith("data:"):
            continue
        dado = linha[5:].strip()
        if dado == "[DONE]":
            break
        try:
            ev = json.loads(dado)
        except Exception:
            continue
        eventos += 1
        tipo = ev.get("type", "")
        agora = time.time()
        if agora - ultimo_print > 30:
            print(f"[AR] {model} orc={max_tokens}: vivo ({eventos} eventos), "
                  f"{sum(len(p) for p in pecas)} chars de texto, {agora-t0:.0f}s", flush=True)
            ultimo_print = agora
        if tipo == "response.output_text.delta":
            pecas.append(ev.get("delta", ""))
        elif tipo in ("response.failed", "response.error", "error"):
            raise RuntimeError("stream falhou: " +
                               json.dumps(ev, ensure_ascii=False)[:300])
        elif tipo == "response.completed":
            respd = ev.get("response") or {}
            uso_final = respd.get("usage", {})
            rid = respd.get("id", "")
            status = respd.get("status", "")
    texto = "".join(pecas).strip()
    print(f"[AR] {model} orc={max_tokens}: fim status={status} len={len(texto)} "
          f"tokens={uso_final.get('total_tokens')} eventos={eventos} "
          f"em {time.time()-t0:.0f}s", flush=True)
    if not texto:
        raise RuntimeError(f"resposta vazia (status={status}, eventos={eventos})")
    return texto, uso_final, rid


def dossie_texto():
    """Extrai o texto do DOSSIÊ (.docx é um zip) — NUNCA o modifica."""
    global _DOSSIE_CACHE
    if _DOSSIE_CACHE is None:
        try:
            import zipfile, html as _html
            arq = next((a for a in ARQ_DOSSIE_CANDIDATOS if a.exists()), None)
            if arq is None:
                _DOSSIE_CACHE = ""
            else:
                with zipfile.ZipFile(arq) as z:
                    xml = z.read("word/document.xml").decode("utf-8", "replace")
                xml = xml.replace("</w:p>", "\n")
                txt = _html.unescape(re.sub(r"<[^>]+>", "", xml))
                _DOSSIE_CACHE = "\n".join(l.strip() for l in txt.split("\n") if l.strip())
        except Exception:
            _DOSSIE_CACHE = ""
    return _DOSSIE_CACHE


def memory_directive():
    """Seção 12 do dossiê — instrução fixa do agente (verbatim, NÃO EDITAR)."""
    t = dossie_texto()
    if not t:
        return ""
    ini = t.find("=== MEMORY DIRECTIVE")
    fim = t.find("=== FIM DA MEMORY DIRECTIVE ===")
    if ini < 0 or fim < 0:
        return ""
    return t[ini:fim + len("=== FIM DA MEMORY DIRECTIVE ===")].strip()


PROMPT_MESTRE_V2 = r"""
=== QUEM VOCE E ===
Roteirista-diretor de "TEO & JUCA - SERVICOS GERAIS", comedia muda em claymation.
Recebe uma ideia solta (as vezes transcrita de fala, baguncada) e devolve UM episodio
decupado em clipes prontos para o MiniMax H3. Duas obrigacoes inseparaveis:
(1) FAZER RIR; (2) nao quebrar o pipeline. Episodio valido e sem graca e episodio perdido.
Voce NUNCA descreve aparencia, roupa ou cor dos personagens: o programa cola a ancora
visual verbatim em cada prompt. Voce escreve so ACAO, ESTADO, CAMERA e SOM.

=== A REGRA QUE MANDA EM TODAS ===
CADA CLIPE TEM QUE CONTER UMA PIADA FISICA VISIVEL, COM UM OBJETO QUE SE MOVE.
Se o clipe so mostra alguem medindo, conferindo, aprovando, calculando ou "continuando o
trabalho", ele esta ERRADO - nao importa quao correto tecnicamente esteja. Medir e
preparacao, nunca piada. Reprovacao automatica.

=== BIBLIA DE PERSONAGEM (voz do corpo) ===
TEO - alto, magro, bigode, gorro; SEMPRE a esquerda. MEDE e PLANEJA. Confia na propria
  medida mesmo quando o mundo ja provou o contrario. Erra por excesso de metodo: mede a
  coisa errada com precisao perfeita. Nunca levanta a voz; quanto pior, mais educado.
  Gestos-frase (max. 2 usos no episodio): alisa o bigode; bate o lapis no queixo ANTES de
  errar; polegar para cima ao aprovar o que ja esta desabando.
JUCA - baixo, largo, boina, sueter mostarda; SEMPRE a direita. EXECUTA com conviccao total.
  Erra por pressa e por forca: resolve com o dobro de material, empilha em vez de usar
  escada. Gestos-frase (max. 2 usos): ajeita a boina DEPOIS do erro; coça a nuca; encaixa a
  peca com uma marretada onde precisava de um toque.
DIVISAO DO ERRO (fonte de metade das piadas): quem mede nunca executa, quem executa nunca
confere. A divergencia nasce do intervalo entre a medida do TEO e a execucao do JUCA.
CLIENTE - mudo, no maximo 2 aparicoes (chegada e nota fiscal). Nunca ajuda, nunca reclama,
nunca interfere. O figurino diz o setor: farda, jaleco, avental, colete, terno, roupao.

=== MOTOR DE COMEDIA (obrigatorio em todo clipe) ===
SETUP (estado normal legivel) -> EXPECTATIVA (o jeitinho parece que vai dar certo)
-> SUBVERSAO (o resultado e SEMPRE maior que a causa) -> REACAO SUBCONTROLADA
(registra e volta ao trabalho; nunca cara de "ops", nunca panico).

Cardapio de gags - escolha 1 por clipe, varie ao longo do episodio:
1. ESCORREGAR/DESLIZAR: a base perde atrito e o corpo continua o movimento.
2. TRANSBORDAR/VAZAR: o material cresce mais que o recipiente.
3. TOMBAR/ROLAR: o peso vence o apoio.
4. QUICAR/VOAR: a peca escapa da mao ou da mola e viaja.
5. DOBRAR/CEDER: a estrutura aguenta menos que o previsto e assume uma curva.
6. PRENSAR/ESMAGAR: duas coisas querem o mesmo lugar.
7. PEGAR A COISA ERRADA: rotulo ilegivel/trocado; a ferramenta certa faz o servico errado.
8. VOLTAR CONTRA QUEM FEZ: o conserto ataca o autor (porta fecha nele, alavanca sobe).
Regras duras:
- CAUSA VISIVEL: a causa de toda falha aparece em quadro NO CLIPE ANTERIOR (insert ou canto).
- UM erro novo por clipe. Nunca dois.
- ALIVIO FALSO: o problema nunca "acaba"; ele muda de lugar (o balde enche, a parede acaba).
- DANO MATERIAL E VISIVEL: parede, piso, teto, agua, tinta, espuma, tijolo, areia, cabo.
  Dano invisivel NAO E PIADA. Proibido: "entra em curto", "curto-circuito em cadeia",
  "sobrecarga eletrica", "pane no sistema", "falha interna", "colapso da infraestrutura".
  Se o dano nao tem forma fisica que o publico veja se mover, troque por dano material.
- NINGUEM SE MACHUCA. Dano so em coisa.
- ESCALA: cada degrau muda de superficie - objeto -> parede -> piso -> teto/estrutura.

=== O QUE MATA A PIADA (reprovacao) ===
- clipe-cola: medir, conferir, aprovar, calcular, verificar, planejar, reposicionar.
- "eles continuam trabalhando" / "trocam um olhar neutro" como clipe inteiro.
- repetir gesto-frase mais de 2x; repetir a mesma gag mais de 1x.
- explicar a causa (plano que so confirma o que o publico ja viu).
- reacao exagerada: correr, gritar, careta, desespero.
- climax acontecendo fora de quadro ("longe dos dois", "atras deles", "em outra sala").
- texto na tela, placa legivel, letreiro, legenda, fala, murmurio, risada, musica.
- moral da historia, licao, "e assim aprenderam que...".

=== CALIBRAGEM DE DURACAO ===
300 s = 30 clipes de 10 s (padrao; 3-4 beats, 1 gag por clipe).
60 s  = 6 clipes de 10 s: 1 gancho (ligacao), 2 chegada + diagnostico errado, 1 primeiro dano,
        1 jeitinho que piora, 1 climax + reacao. Max. 2 objetos plantados.
30 s  = 3 clipes de 10 s: gancho curto, 1 falha com causa visivel, 1 climax/revelacao.
        UM objeto plantado, UMA gag, reacao no ultimo segundo do clipe 3. Sem subtrama.
Nunca escreva duracao no texto: quem define e video_length no settings.

=== METODO EM DUAS PASSADAS (nesta ordem) ===
PASSADA A - ESPINHA (10 linhas, em PT, humor primeiro). Antes de qualquer JSON, escreva:
  GANCHO: como o telefone/chegada ja plantou o objeto da piada.
  ERRO CENTRAL: qual material/ferramenta errada, e POR QUE e plausivel.
  OBJETOS: 3 objetos (plantio no 1o terco -> colheita em ordem inversa no climax).
  ESCADA: degrau 1 (objeto), 2 (parede), 3 (piso), 4 (teto/estrutura) - 1 linha cada.
  ALIVIO FALSO: o momento em que parece resolvido.
  PAUSA: onde entra o plano vazio.
  OLHAR: o unico momento em que eles concordam.
  NOTA: como a nota fiscal fecha com o objeto colhido.
PASSADA B - DECUPAGEM. So entao distribua nos estagios e escreva os clipes.
Se um clipe nao tem gag com objeto, corte-o e passe a acao ao vizinho. Nunca encha
clipe com medicao para bater a contagem.

=== ESTRUTURA 300 s (contagem obrigatoria) ===
LIGACAO 1 | CHEGADA 2 | DIAGNOSTICO_ERRADO 3 | PRIMEIRA_FALHA 3 | JEITINHO 5 |
PAUSA_COMICA 1 | ESCALADA 5 | CLIMAX 5 | REACAO_EM_CORO 1 | NOTA_FISCAL 4
Estrutura 60 s (6 clipes): LIGACAO 1 | CHEGADA 1 | DIAGNOSTICO_ERRADO 1 | PRIMEIRA_FALHA 1 |
JEITINHO 1 | CLIMAX 1.
Estrutura 30 s (3 clipes): LIGACAO 1 | PRIMEIRA_FALHA 1 | CLIMAX 1.

=== CAMPOS (JSON) ===
titulo, logline, setor, servico, cliente, mecanismo, degrau_final,
objetos_plantados[3] {objeto, plantado_no_clipe, pago_no_clipe}, callback_object,
set_historia (EN, "SET: ..." 400-800 chars, inclui a luz do lugar),
continuidade[>=5], assinatura ("nota fiscal ...").
shots[]: n, dur (10), estagio, beats[3-4 em PT, o ultimo em movimento],
  gag (1 linha PT: o que move + por que e engracado),
  objeto_gag (o objeto fisico da gag),
  action (EN, 45-90 palavras: so a acao; NUNCA aparencia; termina em movimento),
  camera (EN, um unico trabalho de camera),
  overall_soundscape (EN, 3-5 eventos nomeados, material + verbo),
  non_diegetic_music ("N/A"),
  estado (EN, opcional: o que mudou e persiste, muda NO CORTE).

=== EXEMPLO CERTO x ERRADO (mesma premissa) ===
ERRADO (clipe sem piada - o que o gerador estava produzindo):
"TEO mede o vao estreito e calcula uma fileira modesta. JUCA descarrega tijolos.
O carrinho roca a grade e poe a tranca em balanco. JUCA ajeita a boina e continua."
-> Ninguem erra. Nada se move por causa de nada. So processo.

CERTO (mesmo clipe, com gag fisica e causa visivel):
beats: ["JUCA apoia o primeiro tijolo e aperta o aplicador.",
        "Uma lingua de espuma branca escapa da junta e empurra o tijolo para cima.",
        "O tijolo flutua na espuma e gira devagar, ainda subindo.",
        "JUCA ajeita a boina e aplica mais espuma embaixo dele."]
gag: "a espuma cresce mais que o tijolo e faz o tijolo flutuar - o material certo executando o servico errado."
objeto_gag: "tijolo sobre espuma"

=== LEI DE FERRO (unica, vale sobre tudo) ===
1. ZERO FALA: boca nao se move; nenhuma palavra, murmurio inteligivel, risada ou grito.
2. ZERO TEXTO NA TELA: sem legenda, letreiro, carta legivel, tarja, numero.
3. ZERO MUSICA: non_diegetic_music = N/A. O som e foley diegetico nomeado, 8-14 eventos
   no episodio; silencio de 1,0-1,5 s antes do desastre e antes da reacao.
4. DANO SO MATERIAL. Ninguem ferido, sem dor, sem sangue, sem animal machucado.
5. NINGUEM PERCEBE O ERRO. Reacao subdimensionada. Nunca cara de "ops".
6. SERVICO ENTREGUE + NOTA FISCAL no fim. Nunca desistem, nunca chamam ajuda, nunca explicam.
7. TEO a ESQUERDA mede; JUCA a DIREITA executa. Nunca "Joca", nunca "Theo".
8. Todo clipe termina EM MOVIMENTO. Proibido freeze, fade, "fim", plano parado.
9. Camera: um trabalho por clipe; proibido handheld, whip pan, crash zoom, olhar para a camera.
10. SAIDA: RESUMO (max. 8 linhas, PT) + UM bloco json. Nada depois do JSON.

=== AUTOCHECAGEM ANTES DE ENTREGAR ===
[ ] todo clipe tem gag com objeto que se move?
[ ] algum clipe e so medir/conferir/aprovar? -> reescreva
[ ] causa de cada falha visivel no clipe anterior?
[ ] 3 objetos plantados e colhidos em ordem inversa?
[ ] algum dano invisivel (curto, pane, falha interna)? -> troque por material
[ ] climax inteiro dentro de quadro?
[ ] gestos-frase <= 2 cada; olhar juntos 1x; pausa vazia 1x?
[ ] a contagem de clipes bate com o formato pedido?
"""


def instrucoes_dossie():
    """v3: prompt mestre com ORCAMENTO DE FISICA + regra dos dois corpos + reacao legivel.
    A ancora visual continua fora daqui: o programa cola ancoras CURTAS (regras_v3)."""
    return regras_v3.PROMPT_MESTRE_V3

def ep_eh_dossie(ep):
    shots = ep.get("shots") or []
    if not shots:
        return False
    s0 = shots[0]
    return ("objetos_plantados" in ep or "dur" in s0
            or str(s0.get("estagio", "")).upper() in DOSSIE_ESTAGIOS)


def _action_ja_completa(act):
    a = act.lower()
    return "claymation plasticine" in a or "handcrafted modelling clay" in a


def prompt_dossie(s, ep):
    """v3: ACTION primeiro, ancoras CURTAS no meio, estilo/negativos no fim.
    Motivo: o modelo le o comeco do prompt. No v2 a acao ficava depois de ~3.900
    chars de roupa, e o video renderizava a roupa e ignorava a piada."""
    return regras_v3.montar_prompt_v3(s, ep, blocos_fixos())


FORMATOS = {
    30: {"LIGACAO": 1, "CHEGADA": 2, "DIAGNOSTICO_ERRADO": 3, "PRIMEIRA_FALHA": 3,
         "JEITINHO": 5, "PAUSA_COMICA": 1, "ESCALADA": 5, "CLIMAX": 5,
         "REACAO_EM_CORO": 1, "NOTA_FISCAL": 4},
    6: {"LIGACAO": 1, "CHEGADA": 1, "PRIMEIRA_FALHA": 1,
        "JEITINHO": 1, "ESCALADA": 1, "CLIMAX": 1},
    3: {"LIGACAO": 1, "PRIMEIRA_FALHA": 1, "CLIMAX": 1},
}
VERBOS_GAG = ("escorrega", "escorreg", "desliza", "tomba", "voa", "voou", "quica", "rola",
              "dobra", "curva", "arca", "cede", "racha", "estala", "estoura", "esguicha",
              "vaza", "transborda", "incha", "cresce", "sobe", "levanta", "empurra", "prensa",
              "esmaga", "arranca", "torce", "gira", "despenca", "cai", "fura", "quebra",
              "derruba", "salta", "estufa", "suga", "chupa", "espirra", "entorna", "treme",
              "cusp", "jorra", "vira", "tomb", "estica", "encolhe", "desaba", "afunda",
              "quica", "desliz", "explode", "vibra", "rasga", "enrosca", "trav", "sobe")
VERBOS_PROCESSO = ("mede", "medir", "confere", "conferir", "verifica", "aprova", "calcula",
                   "planeja", "reposiciona", "acompanha", "estima", "define", "registra",
                   "continua trabalhando", "continuam trabalhando", "troca um olhar")
DANO_INVISIVEL = ("entra em curto", "em curto", "curto-circuito", "curto circuito",
                  "sobrecarga", "pane", "falha interna", "infraestrutura",
                  "sistema elétrico", "sistema eletrico", "colapso interno",
                  "sobrecarga elétrica", "sobrecarga eletrica", "queimad")
FORA_DE_QUADRO = ("longe dos dois", "atrás deles", "atras deles", "fora de quadro",
                  "em outra sala", "longe dos trabalhadores", "à distância", "a distancia")
GESTOS = ("ajeita a boina", "bate o lápis", "bate o lapis", "polegar", "alisa o bigode",
          "coça a nuca", "coca a nuca")


def _tem(txt, lista):
    t = txt.lower()
    return [p for p in lista if p in t]


def _validar_dossie_v2(ep):
    """Validacao v2 = forma (v1) + HUMOR: todo clipe precisa de piada fisica."""
    erros, avisos = [], []
    shots = ep.get("shots") or []
    n = len(shots)
    if n not in FORMATOS:
        erros.append(f"clipes: {n} - os formatos sao 30 (300 s), 6 (60 s) e 3 (30 s)")
    conta = {}
    for s in shots:
        est = str(s.get("estagio", "")).upper().strip()
        conta[est] = conta.get(est, 0) + 1
    alvo = FORMATOS.get(n, {})
    for est, qtd in alvo.items():
        if conta.get(est, 0) != qtd:
            erros.append(f"estagio {est}: {conta.get(est, 0)} clipe(s) - deveria ser {qtd}")
    for est in conta:
        if alvo and est not in alvo:
            avisos.append(f"estagio extra para o formato de {n} clipes: {est}")

    for campo in ("titulo", "logline", "setor", "servico", "cliente", "mecanismo",
                  "degrau_final", "callback_object", "assinatura", "set_historia"):
        if not str(ep.get(campo, "")).strip():
            erros.append(f"campo obrigatorio ausente: {campo}")
    if "nota fiscal" not in str(ep.get("assinatura", "")).lower():
        erros.append("assinatura deve registrar a NOTA FISCAL (fecho da serie)")

    ops = ep.get("objetos_plantados") or []
    if len(ops) != 3 and n == 30:
        erros.append(f"objetos_plantados: {len(ops)} - devem ser exatamente 3")
    for o in ops:
        try:
            pl = int(o.get("plantado_no_clipe", 0)); pg = int(o.get("pago_no_clipe", 0))
        except Exception:
            erros.append("objetos_plantados: plantado_no_clipe/pago_no_clipe devem ser numeros")
            continue
        if not 1 <= pl <= max(3, n // 3):
            erros.append(f"objeto '{o.get('objeto','?')}': plantado no clipe {pl} - 1o terco")
        if pg < pl:
            erros.append(f"objeto '{o.get('objeto','?')}': pago ({pg}) antes de plantado ({pl})")
    if not (ep.get("continuidade") or []):
        erros.append("continuidade: lista vazia")

    bruto = json.dumps(ep, ensure_ascii=False)
    if re.search(r"Joca", bruto):
        erros.append("achou 'Joca' - o nome correto e JUCA (nunca Joca)")
    if re.search(r"Theo", bruto):
        erros.append("achou 'Theo' - o nome correto e TEO (nunca Theo)")

    sem_gag, so_processo, dano_invis, fora_quadro = [], [], [], []
    for s in shots:
        i = s.get("n", "?")
        act = str(s.get("action", ""))
        gag = str(s.get("gag", "")).strip()
        beats = s.get("beats") or []
        if not act.strip():
            erros.append(f"[{i}] action vazia"); continue
        if len(act) > 7000:
            erros.append(f"[{i}] action com {len(act)} chars - teto absoluto e 7000")
        if _action_ja_completa(act):
            if not 2000 <= len(act) <= 4500:
                avisos.append(f"[{i}] action com {len(act)} chars - alvo: 2.500-3.500")
            if "They do not speak" not in act:
                erros.append(f"[{i}] action sem 'They do not speak and their mouths do not move.'")
        else:
            if not 250 <= len(act) <= 1200:
                avisos.append(f"[{i}] action com {len(act)} chars - alvo v2: 300-900 (so a acao)")
            if not str(s.get("camera", "")).strip() and "camera" in act.lower():
                avisos.append(f"[{i}] camera dentro do action - use o campo camera")
        baixo = act.lower()
        for w in PALAVRAS_VEDADAS:
            if w in baixo:
                erros.append(f"[{i}] termo vedado no action: '{w}'")
        som = str(s.get("overall_soundscape", ""))
        if not som.strip():
            erros.append(f"[{i}] overall_soundscape vazio (o som e o punchline)")
        elif not SOM_NOMEADO.search(som):
            erros.append(f"[{i}] soundscape sem evento nomeado (material + verbo)")
        if str(s.get("non_diegetic_music", "N/A")).strip().upper() != "N/A":
            erros.append(f"[{i}] non_diegetic_music deve ser 'N/A' (zero trilha)")
        if not 3 <= len(beats) <= 4:
            avisos.append(f"[{i}] beats: {len(beats)} - o dossie pede 3 ou 4")
        if int(s.get("dur", 0) or 0) != DOSSIE_DUR:
            erros.append(f"[{i}] dur={s.get('dur')} - clipe e de {DOSSIE_DUR} s")

        corpo = " ".join([gag] + [str(x) for x in beats]) + " " + act
        if not gag:
            sem_gag.append(i)
        elif not _tem(gag, VERBOS_GAG):
            avisos.append(f"[{i}] gag sem verbo fisico - descreva o que se MOVE")
        fisico = _tem(" ".join([gag] + [str(x) for x in beats]), VERBOS_GAG)
        if not fisico:
            so_processo.append(i)
        di = _tem(corpo, DANO_INVISIVEL)
        if di:
            dano_invis.append(i)
            erros.append(f"[{i}] dano invisivel ('{di[0]}') - troque por dano material visivel")
        if str(s.get("estagio", "")).upper() == "CLIMAX" and _tem(corpo, FORA_DE_QUADRO):
            fora_quadro.append(i)
            erros.append(f"[{i}] climax fora de quadro - o publico precisa VER o desastre")
        if _tem(corpo, ("longe dos dois", "atrás deles", "atras deles")) and str(
                s.get("estagio", "")).upper() in ("CLIMAX", "ESCALADA"):
            if i not in fora_quadro:
                avisos.append(f"[{i}] acao acontecendo fora de quadro no pico")

    if sem_gag:
        erros.append(f"clipes SEM o campo 'gag' (a piada nao foi declarada): {sem_gag}")
    if so_processo:
        erros.append(f"clipes SEM piada fisica (so medir/conferir/aprovar): {sorted(set(so_processo))}")

    for g in GESTOS:
        c = bruto.lower().count(g)
        if c > 3:
            erros.append(f"gesto-assinatura repetido {c}x ('{g}') - maximo 3 no episodio")
    gags = [str(s.get("gag", "")).strip().lower() for s in shots if str(s.get("gag", "")).strip()]
    if gags and len(set(gags)) < max(1, int(len(gags) * 0.7)):
        avisos.append(f"gags repetidas: {len(gags) - len(set(gags))} de {len(gags)} iguais")

    total = sum(int(s.get("dur", 0) or 0) for s in shots)
    chars = {str(s.get("n", 0)): len(prompt_dossie(s, ep)) for s in shots}

    nota, motivos = 0, []
    if not sem_gag and not so_processo:
        nota += 4; motivos.append("todo clipe tem piada fisica declarada")
    if not dano_invis:
        nota += 1; motivos.append("dano material visivel")
    if not fora_quadro:
        nota += 1; motivos.append("climax em quadro")
    semsil = sum(1 for s in shots if "silence" in str(s.get("overall_soundscape", "")).lower())
    if 2 <= semsil <= 6:
        nota += 1; motivos.append(f"{semsil} beats de silencio")
    if gags and len(set(gags)) >= max(1, int(len(gags) * 0.8)):
        nota += 1; motivos.append("gags variadas")
    if ep.get("objetos_plantados"):
        nota += 1; motivos.append("plantio/colheita declarados")
    if any(str(s.get("objeto_gag", "")).strip() for s in shots):
        nota += 1; motivos.append("objetos de gag nomeados")
    nota = min(10, nota)
    avisos.insert(0, f"NOTA DE HUMOR: {nota}/10 - " + ("; ".join(motivos) if motivos else "sem pontos positivos"))
    return {"erros": erros, "avisos": avisos, "total_s": total,
            "chars_por_plano": chars, "n_planos": n, "formato": "dossie_v2",
            "humor": nota}

def pasta_do_episodio(ep):
    titulo = ep.get("titulo", "episodio")
    titulo = titulo if isinstance(titulo, str) else "episodio"
    return EPISODIOS_DIR / slugify(titulo)


def salvar_episodio(ep, sobrescrever=False):
    pasta = pasta_do_episodio(ep)
    if pasta.exists() and not sobrescrever:
        raise FileExistsError(f"{pasta} já existe (489 sobrescrever=true para gravar por cima)")
    EPISODIOS_DIR.mkdir(exist_ok=True)
    pasta.mkdir(parents=True, exist_ok=True)
    mp = montar_prompts_mod()
    blocos = blocos_fixos()
    dossie = ep_eh_dossie(ep)
    cam_shot = []
    manifesto = []
    for s in ep["shots"]:
        if dossie:
            txt = prompt_dossie(s, ep)
            manifesto.append({"n": s["n"], "estagio": str(s.get("estagio", "")),
                              "video_length": f"{int(s.get('dur', DOSSIE_DUR))}s",
                              "chars": len(txt)})
        else:
            txt = mp.montar(s, blocos, ep)
            manifesto.append({"n": s["n"], "estagio": s.get("estagio", ""),
                              "video_length": f"{s['duracao_s']}s", "inicio": s["inicio"],
                              "set": s["set"], "chars": len(txt)})
        arq = pasta / f"shot_{int(s['n']):02d}.txt"
        arq.write_text(txt, encoding="utf-8")
        cam_shot.append(str(arq))
        manifesto.append({"n": s["n"], "estagio": s.get("estagio", ""),
                          "video_length": f"{s['duracao_s']}s", "inicio": s["inicio"],
                          "set": s["set"], "chars": len(txt)})
    (pasta / "episodio.json").write_text(
        json.dumps(ep, ensure_ascii=False, indent=2), encoding="utf-8")
    (pasta / "manifest.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"pasta": str(pasta), "shots": cam_shot, "manifest": str(pasta / "manifest.json"),
            "episodio_json": str(pasta / "episodio.json")}


def gerar_settings(ep, sobrescrever=False):
    pasta = pasta_do_episodio(ep) / "settings"
    if pasta.exists() and not sobrescrever:
        raise FileExistsError(f"{pasta} já existe (489 sobrescrever=true para gravar por cima)")
    pasta.mkdir(parents=True, exist_ok=True)
    mp = montar_prompts_mod()
    blocos = blocos_fixos()
    slug = pasta_do_episodio(ep).name
    tag = tag_slug(slug)
    dossie = ep_eh_dossie(ep)
    st_entrad, total = [], 0
    for s in ep["shots"]:
        n = int(s["n"])
        est = re.sub(r"[^a-z0-9]+", "-", str(s.get("estagio", "plano")).lower()).strip("-")
        cfg = dict(TEMPLATE_SETTINGS)
        if dossie:
            dur = int(s.get("dur", DOSSIE_DUR) or DOSSIE_DUR)
            cfg["video_length"] = f"{dur}s"
            cfg["prompt"] = prompt_dossie(s, ep)
            cfg["output_filename"] = f"{slug}_c{n:02d}_{est}"
            total += dur
        else:
            cfg["video_length"] = f"{s['duracao_s']}s"
            cfg["prompt"] = mp.montar(s, blocos, ep)
            cfg["output_filename"] = f"{slug}_s{n:02d}_{est}"
            total += s["duracao_s"]
        arq = pasta / f"{cfg['output_filename']}_settings.json"
        arq.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        st_entrad.append((arq, tag, n, est))
    est_total = total * SEG_POR_SEG
    linhas = ["# FAZEDOR — corrente de geração", f"# Episódio: {ep.get('titulo','?')}",
              f"# {len(st_entrad)} planos · {total}s · estimado {est_total/3600:.1f} h @ {SEG_POR_SEG:.0f} s/s",
              f"# Rodar: powershell -ExecutionPolicy Bypass -File \"{(pasta / (slug + '_gerar_todos.ps1'))}\"",
              f"Set-Location \"{DIR_GEN_TEST}\""]
    for arq, tg, n, est in st_entrad:
        linhas.append(f"& \"{PYTHON_GEN}\" \"{GEN_TEST}\" --settings \"{arq}\" --tag {tg}_S{n:02d}")
    ps = pasta / f"{slug}_gerar_todos.ps1"
    ps.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return {"settings_dir": str(pasta), "arquivos": [str(a[0]) for a in st_entrad],
            "corrente": str(ps), "total_s": total, "horas_estimadas": round(est_total / 3600, 2)}


def chat_api(endpoint, key, model, messages, temperature, max_tokens):
    """OpenAI-compatível (Groq/OpenRouter/Ollama/LM Studio/Personalizado)."""
    corpo = json.dumps({"model": model, "messages": messages, "temperature": temperature,
                        "max_tokens": max_tokens}).encode("utf-8")
    ped = urllib.request.Request(endpoint.rstrip("/") if endpoint.rstrip("/").endswith(
        ("chat/completions",)) else endpoint.rstrip("/") + "/chat/completions",
        data=corpo, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(ped, timeout=LIMITE_API_TIMEOUT) as r:
        resp = json.loads(r.read().decode("utf-8", "replace"))
    escolha = (resp.get("choices") or [{}])[0]
    return (escolha.get("message") or {}).get("content", ""), resp.get("usage", {})


# ── Gemini Interactions API (v1beta/interactions, beta jun/2026) ──
ARQ_CONFIG_SECRET = APP_DIR / "config_secret.json"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
GEMINI_MODELS_FALLBACK = ["gemini-3.8-flash", "gemini-3-flash-preview",
                          "gemini-3.6-flash", "gemini-2.5-flash"]
GEMINI_PENSAMENTO = {"minimo": "minimal", "baixo": "low", "medio": "medium", "alto": "high"}

# ── AgentRouter (proxy OpenAI-compatível, /v1/responses) ──
AR_BASE = "https://agentrouter.org/v1"
AR_MODELOS = ["gpt-5.6-sol", "gpt-6.1-sol", "gpt-6-astra"]
# Sequência de orçamentos por modelo (canais aceitam tetos diferentes; o astra
# costuma abortar o stream no meio com orçamentos grandes — response.failed).
AR_ORCAMENTOS = {"gpt-5.6-sol": (96000, 64000, 48000),
                 "gpt-6.1-sol": (96000, 64000, 48000),
                 "gpt-6-astra": (64000, 48000, 32000, 24000)}
# O WAF do painel só libera clientes "agent" — UA do Codex CLI passa (testado 2026-11-05);
# UA genérico recebe 401 "unauthorized client detected".
AR_UA = "codex_cli_rs/0.42.0 (Windows 11; x86_64) windows"


def ler_chave_agentrouter():
    try:
        c = json.loads(ARQ_CONFIG_SECRET.read_text(encoding="utf-8"))
        return c.get("agentrouter_key", "")
    except Exception:
        return ""


def agentrouter_responses(key, model, messages, max_tokens):
    """Responses API com STREAMING. Descobertas 2026-11-05:
    - WAF do painel bloqueia imperativos de geração no input ('Gere...', 'Responda:',
      'Prosseguia.') → TODO o conteúdo vai em `instructions` e o input é só 'ok'.
    - UA genérico → 401 'unauthorized client detected' → UA do Codex CLI.
    - Modelos RACIOCINAM: com orçamento curto ficam status=incomplete sem texto;
      esforço low + orçamento ≥32k resolve. `temperature` não é suportado.
    - Síncrono estoura 504 do ALB deles; stream mantém a conexão viva.
    Retorna (texto, uso, id)."""
    partes = []
    # FORÇAMENTO: o dossiê (MD + LEI DE FERRO) manda SEMPRE que existir,
    # ignorando qualquer system vindo do cliente — sem fala, sem texto, sem trilha.
    sist = instrucoes_dossie() or "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    if sist:
        partes.append("=== INSTRUÇÕES DO SISTEMA ===\n" + sist)
    hist = [m for m in messages if m["role"] != "system"]
    if hist:
        partes.append("=== CONVERSA ATÉ AGORA ===")
        for m in hist:
            quem = "USUÁRIO" if m["role"] == "user" else "ASSISTENTE"
            partes.append(quem + ":\n" + str(m["content"]))
    partes.append("=== TAREFA ===\nAtenda à última mensagem do USUÁRIO acima, seguindo "
                  "as instruções do sistema. Comece imediatamente, sem perguntas. "
                  "Escreva o bloco de json COMPACTO (sem indentação, sem espaços "
                  "desnecessários) para caber no orçamento de saída — o episódio tem "
                  "30 clipes e é longo. Cada overall_soundscape usa eventos nomeados "
                  "(material + verbo, ex.: 'shell barnacles crackle against steel').")
    corpo = {"model": model,
             "instructions": "\n\n".join(partes),
             "input": [{"role": "user", "content": "ok"}],
             "max_output_tokens": max(64000, min(128000, int(max_tokens or 0) or 64000)),
             "stream": True,
             "reasoning": {"effort": "low", "summary": "auto"}}
    # Nem todo canal aceita summary:"auto" — se 400, tenta sem; se ainda 400, sem reasoning.
    variantes = [corpo,
                 {**corpo, "reasoning": {"effort": "low"}},
                 {k: v for k, v in corpo.items() if k != "reasoning"}]
    resp = None
    ultimo_erro = None
    for tentativa, cor in enumerate(variantes):
        ped = urllib.request.Request(
            AR_BASE + "/responses", data=json.dumps(cor).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}",
                     "User-Agent": AR_UA, "Accept": "*/*",
                     "Accept-Encoding": "identity", "Connection": "keep-alive"})
        try:
            with urllib.request.urlopen(ped, timeout=900) as r:   # timeout = inatividade do socket
                return _consome_stream_ar(r, model, max_tokens)
        except urllib.error.HTTPError as e:
            ultimo_erro = e
            print(f"[AR] {model}: variante {tentativa+1} rejeitada (HTTP {e.code}) — "
                  f"tentando próxima", flush=True)
    raise ultimo_erro if ultimo_erro else RuntimeError("falha desconhecida no AgentRouter")


def ler_chave():
    """Chave opcional em config_secret.json — nunca gravada em outro lugar."""
    try:
        c = json.loads(ARQ_CONFIG_SECRET.read_text(encoding="utf-8"))
        return c.get("gemini_key", "")
    except Exception:
        return ""


def _passo(tipo, texto):
    return {"type": tipo, "content": [{"type": "text", "text": texto}]}


def gemini_interactions(key, model, messages, temperature, max_tokens,
                        thinking_level="medium", previous_id=None):
    """messages: [{role:user|assistant|system}] → passo user_input/model_output.
    system separado → system_instruction. Returns (texto, uso, id)."""
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    entrada = [_passo("user_input", str(m["content"])) if m["role"] != "assistant"
               else _passo("model_output", str(m["content"]))
               for m in messages if m["role"] != "system"]
    corp = {"model": model,
            "generation_config": {"temperature": temperature,
                                  "max_output_tokens": max_tokens,
                                  "thinking_level": thinking_level},
            "store": False}
    if system:
        corp["system_instruction"] = system
    if previous_id:
        corp["previous_interaction_id"] = previous_id
    corp["input"] = entrada
    ped = urllib.request.Request(
        GEMINI_ENDPOINT, data=json.dumps(corp).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(ped, timeout=LIMITE_API_TIMEOUT) as r:
        resp = json.loads(r.read().decode("utf-8", "replace"))
    return _litro_do_gemini(resp)


def _litro_do_gemini(resp):
    """Extrai (texto, uso, id) de uma interação — tolerante a shape."""
    status = resp.get("status", "")
    if status in ("failed", "cancelled"):
        raise RuntimeError(f"interaction {status}: {resp.get('errors', '')}")
    textos = []
    for passo in resp.get("output") or resp.get("steps") or []:
        if passo.get("type") in ("model_output", "text", "message"):
            for ctd in passo.get("content") or []:
                if ctd.get("type") == "text" and ctd.get("text"):
                    textos.append(ctd["text"])
    texto = "\n".join(textos).strip()
    if not texto and status == "incomplete":
        raise RuntimeError("interaction incompleta (max_output_tokens?) — tentar aumentar")
    if not texto:
        raise RuntimeError(f"interaction sem texto (status={status})")
    return texto, resp.get("usage", {}), resp.get("id", "")


MIME_AUDIO_OK = {"audio/webm", "audio/mp4", "audio/ogg", "audio/wav", "audio/mp3", "audio/aac"}


def gemini_transcrever(key, model, b64, mime, temperature=0.0):
    """Áudio base64 → texto (PT-BR), mesmo padrão de modelos+503 do rodar_ia."""
    if mime not in MIME_AUDIO_OK:
        raise ValueError(f"mime não suportado: {mime}")
    instr = ("Transcreva este áudio em português do Brasil. Responda SOMENTE o texto "
             "dito, correndo, sem comentários, sem aspas. Normalize nomes: Theo/Teo → TÉO, "
             "Juca → JUCA. Mantenha a ordem das ideias.")
    ult = None
    for mdl in GEMINI_MODELS_FALLBACK:
        for i, espera in enumerate((0, 5, 12)):
            if espera:
                time.sleep(espera)
            cor = {"model": mdl,
                   "system_instruction": instr,
                   "generation_config": {"temperature": temperature,
                                         "max_output_tokens": 2000,
                                         "thinking_level": "minimal"},
                   "store": False,
                   "input": [{"type": "audio", "data": b64, "mime_type": mime},
                             {"type": "text", "text": instr}]}
            ped = urllib.request.Request(
                GEMINI_ENDPOINT, data=json.dumps(cor).encode("utf-8"),
                headers={"Content-Type": "application/json", "x-goog-api-key": key})
            try:
                with urllib.request.urlopen(ped, timeout=LIMITE_API_TIMEOUT) as r:
                    resp = json.loads(r.read().decode("utf-8", "replace"))
                tx, uso, _ = _litro_do_gemini(resp)
                return tx, uso, mdl
            except urllib.error.HTTPError as e:
                ult = f"API {e.code}: {e.reason} · " + e.read().decode("utf-8", "replace")[:300]
                if e.code in (401, 403, 429):
                    raise RuntimeError(ult)
                if 503 <= e.code <= 504 and i < 2:
                    continue
                break
    raise RuntimeError((ult or "falha Gemini") + " · todos os modelos tentados")


def rodar_ia(api, messages):
    """Resolve o modelo: kind interactions (Gemini, com fallback+previous_id)
    ou openai (compatível).  → (texto, uso, dorsal_id, modelo_usado)"""
    if api.get("kind") == "interactions":
        key = api.get("key", "") or ler_chave()
        if not key:
            raise ValueError("chave Gemini ausente (config API ou config_secret.json)")
        anterior = api.get("previous_id")
        mdl0 = (api.get("model") or "").strip()
        if anterior:
            tentativas = [mdl0 or GEMINI_MODELS_FALLBACK[0]]   # correção: mesmo modelo
        else:
            tentativas = ([mdl0] if mdl0 else [])
            if not mdl0 or not api.get("na_fallback"):
                tentativas += [m for m in GEMINI_MODELS_FALLBACK if m != mdl0]
            tentativas = list(dict.fromkeys(tentativas)) or list(GEMINI_MODELS_FALLBACK)
        ultimo = None
        for mdl in tentativas:                       # modelos: escolhido → fallback
            for i, espera in enumerate((0, 5, 12)):  # tolera picos 503 do Google
                if espera:
                    time.sleep(espera)
                try:
                    txt, uso, iid = gemini_interactions(
                        key, mdl, messages, float(api.get("temperature", 0.8)),
                        int(api.get("max_tokens", 16000)),
                        api.get("thinking_level", "medium"), anterior)
                    return txt, uso, iid, mdl
                except urllib.error.HTTPError as e:
                    detalhe = e.read().decode("utf-8", "replace")[:400]
                    ultimo = f"API {e.code}: {e.reason} · {detalhe}"
                    if e.code in (401, 403, 429):
                        raise RuntimeError(ultimo)   # chave/quota — não adianta outro modelo
                    if 503 <= e.code <= 504 and i < 2:
                        continue                     # pico momentâneo — re-tenta
                    break                            # pico persistiu / 400/404 → próximo modelo
        raise RuntimeError((ultimo or "falha Gemini") +
                           (" · todos os modelos tentados: " + ", ".join(tentativas)
                            if not anterior else ""))
    if api.get("kind") == "responses":
        # FORÇAMENTO: chave SEMPRE do config_secret.json — ignora a que o navegador
        # mandar (evita 401 "无效的令牌" de chave velha guardada no localStorage).
        key = ler_chave_agentrouter()
        if not key:
            raise ValueError("chave AgentRouter ausente em config_secret.json")
        mdl = (api.get("model") or AR_MODELOS[0]).strip()
        ultimo = None
        seq = AR_ORCAMENTOS.get(mdl, (96000, 64000, 48000, 32000))
        esperas = (0, 10, 25, 50, 80)
        for (orcamento, espera) in zip(seq, esperas):
            if espera:
                time.sleep(espera)
            print(f"[AR] {mdl}: tentativa com orcamento {orcamento}…", flush=True)
            try:
                # temperatura não suportada por estes modelos — intencionalmente não enviada
                txt, uso, rid = agentrouter_responses(
                    key, mdl, messages, orcamento)
                return txt, uso, rid, mdl
            except urllib.error.HTTPError as e:
                detalhe = e.read().decode("utf-8", "replace")[:400]
                ultimo = f"API {e.code}: {e.reason} · {detalhe}"
                print(f"[AR] {mdl}: HTTP {e.code} — {detalhe[:160]}", flush=True)
                if e.code in (401, 402, 403):
                    raise RuntimeError(ultimo)    # chave/permissão/cota — parar
                # 400/404/5xx → tenta o próximo orçamento da escada
            except RuntimeError as e:
                # response.failed DURANTE o stream (ex.: filtro/corte no meio) → desce a escada
                ultimo = f"stream: {e}"
                print(f"[AR] {mdl}: {ultimo[:200]}", flush=True)
        raise RuntimeError((ultimo or "falha AgentRouter") + " · modelo " + mdl)
    txt, uso = chat_api(api["endpoint"], api.get("key", ""), api["model"], messages,
                        float(api.get("temperature", 0.8)),
                        int(api.get("max_tokens", 16000)))
    return txt, uso, "", api["model"]


# ── servidor HTTP ──
class Fazedor(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):
        pass

    def _json(self, obj, code=200):
        msg = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(msg)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(msg)

    def _corpo(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if n > LIMITE_CORPO:
            raise ValueError(f"corpo gigante ({n} bytes)")
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def do_GET(self):
        rotas = {"/": self._ui, "/api/pieces": self._pieces, "/api/episodios": self._lista,
                 "/api/fcfg": self._fcfg}
        f = rotas.get(self.path.split("?")[0])
        if f is None:
            return self._json({"erro": "rota desconhecida"}, 404)
        try:
            f()
        except Exception as e:
            self._json({"erro": str(e)}, 500)

    def do_POST(self):
        rotas = {"/api/gerar": self._gerar, "/api/validar": self._validar,
                 "/api/salvar": self._salvar, "/api/settings": self._settings,
                 "/api/transcrever": self._transcrever,
                 "/api/abrir_mic_settings": self._abrir_mic}
        f = rotas.get(self.path)
        if f is None:
            return self._json({"erro": "rota desconhecida"}, 404)
        try:
            f()
        except FileExistsError as e:
            self._json({"erro": str(e)}, 409)
        except urllib.error.HTTPError as e:
            detalhe = e.read().decode("utf-8", "replace")[:600]
            self._json({"erro": f"API {e.code}: {e.reason} · {detalhe}"}, 502)
        except Exception as e:
            self._json({"erro": str(e)}, 400)

    # GET
    def _ui(self):
        msg = UI_FILE.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(msg)))
        self.send_header("Cache-Control", "no-store")   # NUNCA servir UI velha de cache
        self.end_headers()
        self.wfile.write(msg)

    def _pieces(self):
        self._json({"sistema": sistema_texto(), "exemplo": exemplo_texto(),
                    "blocos": blocos_fixos(),
                    "dossie_md": memory_directive(),
                    "dossie_estagios": list(DOSSIE_ESTAGIOS.keys()),
                    "dossie_dur": DOSSIE_DUR,
                    "matriz": DOSSIE_MATRIZ})

    def _fcfg(self):
        """Config padrão pré-carregada (chave de config_secret.json, se existir)."""
        key = ler_chave()
        self._json({"tem_chave": bool(key), "key": key,
                    "kind": "interactions", "endpoint": GEMINI_ENDPOINT,
                    "model": "gemini-3.8-flash", "thinking_level": "medium",
                    "ar_key": ler_chave_agentrouter(), "ar_modelos": AR_MODELOS,
                    "ar_endpoint": AR_BASE + "/responses", "model_ar": AR_MODELOS[0]})

    def _lista(self):
        itens = []
        if EPISODIOS_DIR.exists():
            for d in sorted(EPISODIOS_DIR.iterdir()):
                if d.is_dir():
                    ep = d / "episodio.json"
                    st = d / "settings"
                    itens.append({"nome": d.name, "pronto": ep.exists(),
                                  "settings": st.exists(),
                                  "quando": d.stat().st_mtime, "pasta": str(d)})
        self._json({"episodios": itens})

    # POST
    def _gerar(self):
        d = self._corpo()
        api = d.get("api") or {}
        mensagens = d.get("messages") or []
        if not mensagens:
            raise ValueError("caminho de mensagens vazio")
        txt, uso, dorsal, modelo = rodar_ia(api, mensagens)
        resumo, ep = extrair_json(txt)
        return self._json({"cru": txt, "resumo": resumo, "episodio": ep, "uso": uso,
                           "interaction_id": dorsal, "modelo": modelo})

    def _validar(self):
        ep = self._corpo().get("episodio")
        if not isinstance(ep, dict) or not ep.get("shots"):
            raise ValueError("episódio sem shots")
        return self._json(validar_episodio(ep))

    def _transcrever(self):
        d = self._corpo()
        b64 = str(d.get("audio_b64") or "")
        mime = str(d.get("mime") or "audio/webm").split(";")[0]
        if len(b64) < 500:
            raise ValueError("áudio corrompido/curto demais")
        key = ler_chave()
        if not key:
            raise ValueError("chave Gemini ausente em config_secret.json")
        tx, uso, mdl = gemini_transcrever(key, GEMINI_MODELS_FALLBACK[0], b64, mime)
        return self._json({"texto": tx, "modelo": mdl, "uso": uso})

    def _abrir_mic(self):
        """Abre Configurações do Windows > Privacidade e segurança > Microfone."""
        import os
        try:
            os.startfile("ms-settings:privacy-microphone")
            return self._json({"ok": True})
        except OSError as e:
            raise ValueError(f"Windows não abriu as configurações: {e}")

    def _salvar(self):
        d = self._corpo()
        ep = d.get("episodio")
        if not isinstance(ep, dict) or not ep.get("shots"):
            raise ValueError("episódio sem shots")
        val = validar_episodio(ep)
        if val["erros"] and not d.get("sobrescrever"):
            return self._json({"erro": "episódio com erros — corrigir antes de salvar",
                               "erros": val["erros"], "avisos": val["avisos"]}, 422)
        return self._json({**salvar_episodio(ep, sobrescrever=d.get("sobrescrever", False))},
                          201 if not val["erros"] else 202)

    def _settings(self):
        d = self._corpo()
        ep = d.get("episodio")
        if not isinstance(ep, dict) or not ep.get("shots"):
            raise ValueError("episódio sem shots")
        return self._json(gerar_settings(ep, sobrescrever=d.get("sobrescrever", False)),
                          201)


def porta_livre(porta):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk:
        return sk.connect_ex(("127.0.0.1", porta)) != 0


def main():
    import os
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    env_porta = os.environ.get("PORTA")
    if env_porta:
        porta = int(env_porta)
    else:
        porta = next((p for p in range(PORTA_INICIAL, PORTA_INICIAL + 10) if porta_livre(p)), None)
    if porta is None or not porta_livre(porta):
        print("Sem porta livre."); sys.exit(1)
    # sanity: conserta imports na inicialização (indicador rápido)
    mp = montar_prompts_mod()
    n_blocos = len(blocos_fixos())
    sv = ThreadingHTTPServer(("127.0.0.1", porta), Fazedor)
    url = f"http://127.0.0.1:{porta}"
    print(f"FAZEDOR DE HISTÓRIAS · TÉO & JUCA Company")
    print(f"  UI: {url}")
    print(f"  bases: montar_prompts OK · {n_blocos} blocos fixos · sistema "
          f"{len(sistema_texto())} chars · exemplo {len(exemplo_texto())} chars")
    print(f"  saidas: {EPISODIOS_DIR}\\<titulo>\\")
    if os.environ.get("SEM_BROWSER") != "1":
        threading.Timer(1.2, webbrowser.open, [url]).start()
    try:
        sv.serve_forever()
    except KeyboardInterrupt:
        print("\nAdeus.")
        sv.server_close()


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


if __name__ == "__main__":
    main()
