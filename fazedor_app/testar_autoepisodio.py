# -*- coding: utf-8 -*-
"""Teste do 🎲 Autoepisódio: sorteia tema (matriz do dossiê) e lapida pelo caminho real.
Espelha EXATAMENTE o payload que a UI envia (system = MEMORY DIRECTIVE, user = ideia)."""
import json, io, sys, time, random, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://127.0.0.1:8756"
CF = "```"


def pega(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def post(url, obj, timeout=3600):
    ped = urllib.request.Request(url, data=json.dumps(obj).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(ped, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


p = pega(BASE + "/api/pieces")
M = p["matriz"]
pick = lambda a: random.choice(a)
setor, servico, cliente = pick(M["setor"]), pick(M["servico"]), pick(M["cliente"])
degrau, mecanismo = pick(M["degrau"]), pick(M["mecanismo"])
molde = random.choice(["A", "B", "C"])
abertura = {"A": "o cliente não aparece — eles chegam sozinhos ao local, carregando tudo",
            "B": "dois clientes discordam um do outro sobre como o serviço deve ficar",
            "C": "o prazo é curtíssimo e é anunciado por gestos apressados"}[molde]
ideia = (f"Contratados para um serviço de {servico} num lugar do tipo {setor}, "
         f"para um cliente {cliente}. Abertura: {abertura}. "
         f'O erro central nasce porque "{mecanismo}", e a escalada termina quando '
         f"tudo {degrau} (dano só material). "
         f"TÉO mede e planeja à esquerda; JUCA executa com confiança total à direita; "
         f"ninguém percebe nada.")
resumo_tema = (f"{servico.upper()} · {setor.upper()} · cliente {cliente.upper()} · "
               f'"{mecanismo}" → {degrau.upper()} (molde {molde})')
print("TEMA SORTEADO:", resumo_tema)
print("IDEIA:", ideia)
print()

mensagens = [
    {"role": "system", "content": p["dossie_md"] or p["sistema"]},
    {"role": "user", "content": "IDEIA DO USUÁRIO:\n" + ideia +
                                "\n\nResponda com RESUMO (máx 8 linhas, PT) + um único bloco "
                                + CF + "json" + CF + " no TEMPLATE DE SAÍDA da MEMORY DIRECTIVE. "
                                "Nada depois do JSON."},
]
t0 = time.time()
j = post(BASE + "/api/gerar", {"api": {"kind": "responses", "endpoint":
        "https://agentrouter.org/v1/responses", "key": pega(BASE + "/api/fcfg")["ar_key"],
        "model": "gpt-5.6-sol", "temperature": 0.8, "max_tokens": 96000,
        "na_fallback": True}, "messages": mensagens})
print("LAPIDAÇÃO: %.1fs · modelo=%s · cru=%d chars" %
      (time.time() - t0, j.get("modelo"), len(j.get("cru", ""))))
ep = j.get("episodio")
if not (isinstance(ep, dict) and ep.get("shots")):
    io.open(r"C:\Users\Guilherme\AppData\Local\Temp\opencode\ar_auto_cru.txt", "w",
            encoding="utf-8").write(j.get("cru", ""))
    print("FALHOU extração — cru salvo")
    sys.exit(1)
v = post(BASE + "/api/validar", {"episodio": ep})
print("VALIDAÇÃO: erros=%d avisos=%d | clipes=%d | total=%ss | título=%s"
      % (len(v["erros"]), len(v["avisos"]), v["n_planos"], v["total_s"],
         ep.get("titulo", "?")))
for e in v["erros"][:6]:
    print("  ✗", e)
for a in v["avisos"][:4]:
    print("  !", a)
io.open(r"C:\Users\Guilherme\AppData\Local\Temp\opencode\ar_auto_episodio.json", "w",
        encoding="utf-8").write(json.dumps(ep, ensure_ascii=False, indent=2))
print("episódio salvo em Temp\\opencode\\ar_auto_episodio.json")
