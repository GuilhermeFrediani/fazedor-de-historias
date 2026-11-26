# -*- coding: utf-8 -*-
"""render_supervisor.py — vigia e retomada automática do SMOKE 60 s.

Por que existe: em 26/11/2026 o render morreu às 12:35 porque o processo era
filho da sessão do servidor (um restart matou app + render). O banco só era
gravado DEPOIS do gate, então o c02 tinha mp4 pronto mas não estava bancado.
Este supervisor roda DESTACADO da sessão e:

  1. monitora o PID do render e a atividade real (mtime dos logs/heartbeat);
  2. se o processo morrer, recupera clipes já renderizados e não bancados
     (mp4 válido + frame 9.9 -> smoke_bancados.json), sem re-renderizar;
  3. reinicia o smoke_60s.py, que pula o banco e continua do clipe seguinte;
  4. se o processo travar (sem atividade por N min), mata a árvore e reinicia;
  5. repete até o <slug>_SMOKE60.mp4 existir; se estourar o limite, grava
     ALERTA.txt e para (não fica em loop infinito).

Uso:
  # produção nova (lança o smoke e vigia)
  python render_supervisor.py --slug MEU_EPISODIO

  # anexar a um render já em execução
  python render_supervisor.py --attach-pid 1234 --since "2026-11-26 13:15:10"

  # só status
  python render_supervisor.py --status

  # teste de uma volta
  python render_supervisor.py --once --attach-pid 1234

O supervisor em si deve ser lançado com Start-Process (ou pythonw) para não
morrer quando a sessão do agente reiniciar. Logs/estado em
EPISODIOS/<slug>/automation/.
"""
import argparse
import ctypes
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
APP = Path(__file__).resolve().parent
EPIS = APP / "EPISODIOS"
META = EPIS / "_smoke_meta.json"
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")
FFMPEG = Path(r"C:\pinokio\api\wan2gp-amd\app\ffmpeg_bins\ffmpeg.exe")
FFPROBE = Path(r"C:\pinokio\api\wan2gp-amd\app\ffmpeg_bins\ffprobe.exe")

CFG_APP = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
STILL_ACTIVE = 259


def agora(t=None):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def log(msg, path=None):
    line = "[%s] %s" % (agora(), msg)
    print(line, flush=True)
    if path:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


def atomic_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _h(pid):
    return ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))  # QUERY_LIMITED


def vivo(pid):
    if not pid:
        return False
    try:
        h = _h(pid)
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return bool(ok) and code.value == STILL_ACTIVE
    except Exception:
        return False


def codigo_saida(pid):
    try:
        h = _h(pid)
        if not h:
            return None
        code = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value if ok else None
    except Exception:
        return None


def matar_arvore(pid):
    if not pid:
        return
    try:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                       capture_output=True, text=True, timeout=30)
    except Exception:
        pass


def matar_orfaos(slug):
    """Mata gen_test.py órfãos que ficaram com a GPU (o pai morreu)."""
    try:
        cmd = (
            "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
            "Where-Object { $_.CommandLine -like '*gen_test.py*' -and "
            "$_.CommandLine -like '*%s*' } | ForEach-Object { $_.ProcessId }" % slug
        )
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                           capture_output=True, text=True, timeout=60)
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if line.isdigit():
                matar_arvore(int(line))
    except Exception:
        pass


def mtime(p):
    try:
        return Path(p).stat().st_mtime
    except Exception:
        return 0.0


def atividade(ep, extra=()):
    p = ep / "automation"
    fontes = [ep / "smoke_run.log", ep / "smoke_resume.log",
              p / "heartbeat.json", p / "supervisor.log"]
    fontes += [Path(x) for x in extra]
    return max([mtime(x) for x in fontes] or [0.0])


def duracao(p):
    try:
        r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries",
                            "format=duration", "-of", "default=nw=1:nk=1", str(p)],
                           capture_output=True, text=True, timeout=30)
        return float((r.stdout or "").strip().replace(",", "."))
    except Exception:
        return None


def frame(mp4, png, ts="9.9"):
    try:
        png.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(FFMPEG), "-y", "-v", "error", "-ss", ts,
                        "-i", str(mp4), "-frames:v", "1", str(png)],
                       capture_output=True, timeout=60)
        return png.exists()
    except Exception:
        return False


def carregar_ep(slug=None):
    m = {}
    if META.exists():
        try:
            m = json.loads(META.read_text(encoding="utf-8"))
        except Exception:
            m = {}
    s = slug or m.get("slug")
    if not s:
        raise SystemExit("XX sem slug: passe --slug ou gere _smoke_meta.json")
    ep = Path(m.get("pasta")) if (m.get("slug") == s and m.get("pasta")) else EPIS / s
    if not (ep / "episodio.json").exists():
        raise SystemExit("XX episodio ausente em %s" % ep)
    e = json.loads((ep / "episodio.json").read_text(encoding="utf-8"))
    return s, ep, e


def recuperar_nao_bancados(ep, slug, total, desde, logf):
    """Se o render morreu depois de gravar o mp4 e antes de bancar, transforma
    esse mp4 em fallback bancado (frame 9.9 como âncora de saída)."""
    banco_f = ep / "smoke_bancados.json"
    try:
        banco = json.loads(banco_f.read_text(encoding="utf-8")) if banco_f.exists() else {}
    except Exception:
        banco = {}
    banco.setdefault("clipes", {})
    mudou = False
    for i in range(1, total + 1):
        curto = "c%02d" % i
        if curto in banco["clipes"]:
            continue
        cands = [p for p in OUT.glob("%s_%s_*_sm*.mp4" % (slug, curto))
                 if p.stat().st_mtime >= desde - 120 and p.stat().st_size > 1_000_000
                 and "_smoke" not in p.name]
        if not cands:
            continue
        mp4 = max(cands, key=lambda p: p.stat().st_mtime)
        dur = duracao(mp4)
        if dur is None or not (7.5 <= dur <= 12.5):
            log("recuperacao: %s tem mp4 mas duracao invalida (%s) - nao banco"
                % (curto, dur), logf)
            continue
        png = ep / "refs" / ("ancora_smoke_%s.png" % curto)
        if not frame(mp4, png, "9.9"):
            log("recuperacao: %s sem frame 9.9 - nao banco" % curto, logf)
            continue
        banco["clipes"][curto] = {
            "slug": mp4.stem, "curto": curto, "mp4": str(mp4),
            "aprovado": False, "fallback": True,
            "recuperado_sem_gate": True,
            "ancora_out": str(png),
            "tentativas": [{"slug": mp4.stem, "mp4": str(mp4),
                            "dur_min": round(dur / 60.0, 2),
                            "recuperado_em": agora()}],
        }
        mudou = True
        log("recuperacao: %s bancado como fallback (%s, %.1fs) sem re-render"
            % (curto, mp4.name, dur), logf)
    if mudou:
        atomic_json(banco_f, banco)


def ler_cauda(ep, n=12000):
    txt = ""
    try:
        txt = (ep / "smoke_run.log").read_text(encoding="utf-8", errors="replace")[-n:]
    except Exception:
        pass
    return txt


def gate_caiu(ep):
    txt = ler_cauda(ep)
    pos = txt.rfind("largada ")
    if pos >= 0:
        txt = txt[pos:]
    return ("CADEIA PAUSADA" in txt) or ("gate indisponivel por 30 min" in txt)


def lancar(ep, logf):
    reg = ep / "automation"
    reg.mkdir(parents=True, exist_ok=True)
    f = open(ep / "smoke_resume.log", "a", encoding="utf-8", buffering=1)
    p = subprocess.Popen(
        [PY, str(APP / "smoke_60s.py")],
        cwd=str(APP), stdout=f, stderr=subprocess.STDOUT,
        creationflags=CFG_APP, close_fds=False,
    )
    try:
        (reg / "render.pid").write_text(str(p.pid), encoding="utf-8")
    except Exception:
        pass
    log("render lançado: PID %d" % p.pid, logf)
    return p.pid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug")
    ap.add_argument("--attach-pid", type=int, default=0)
    ap.add_argument("--since", default="")
    ap.add_argument("--max-restarts", type=int, default=10)
    ap.add_argument("--stale-min", type=float, default=45.0)
    ap.add_argument("--interval", type=float, default=30.0)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    slug, ep, e = carregar_ep(a.slug)
    total = len(e.get("shots") or [])
    reg = ep / "automation"
    reg.mkdir(parents=True, exist_ok=True)
    logf = reg / "supervisor.log"
    statef = reg / "status.json"
    alertaf = reg / "ALERTA.txt"
    stopf = reg / "STOP"

    if a.status:
        if statef.exists():
            print(statef.read_text(encoding="utf-8"))
        else:
            print("sem status ainda")
        return 0

    inicio = time.time()
    if a.since:
        try:
            since = datetime.strptime(a.since, "%Y-%m-%d %H:%M:%S").timestamp()
        except Exception:
            since = inicio
    else:
        since = inicio - 60

    final = ep / (slug + "_SMOKE60.mp4")

    # lock: um supervisor por episódio
    lock = reg / "supervisor.lock"
    try:
        if lock.exists():
            antigo = int(lock.read_text(encoding="utf-8").strip() or 0)
            if antigo and antigo != os.getpid() and vivo(antigo):
                print("XX supervisor já ativo (PID %d)" % antigo)
                return 1
        lock.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass

    state = {
        "slug": slug, "episodio": str(ep), "supervisor_pid": os.getpid(),
        "inicio": agora(inicio), "desde": agora(since),
        "modo": "8/640", "status": "iniciando", "render_pid": None,
        "restarts": 0, "max_restarts": a.max_restarts,
        "stale_min": a.stale_min, "ultima_atividade": None,
        "final": str(final), "gate_indisponivel": False, "historico": [],
    }

    def salvar(status=None):
        if status:
            state["status"] = status
        state["agora"] = agora()
        state["render_pid"] = pid
        state["final_existe"] = final.exists()
        try:
            state["ultima_atividade"] = agora(atividade(ep))
        except Exception:
            pass
        atomic_json(statef, state)

    def sucesso():
        state["status"] = "concluido"
        state["fim"] = agora()
        state["video"] = str(final)
        atomic_json(statef, state)
        log("CONCLUIDO: %s" % final, logf)
        return 0

    try:
        pid = a.attach_pid or 0
        if not pid:
            rp = reg / "render.pid"
            if rp.exists():
                try:
                    cand = int(rp.read_text(encoding="utf-8").strip())
                    if vivo(cand):
                        pid = cand
                except Exception:
                    pass
        if not pid:
            pid = lancar(ep, logf)
        log("supervisor iniciado | slug=%s | anexado=%s | since=%s | pid=%s"
            % (slug, a.attach_pid or "nao", agora(since), pid), logf)

        while True:
            if stopf.exists():
                log("STOP encontrado - encerrando e matando render", logf)
                matar_arvore(pid)
                salvar("parado")
                return 0

            if final.exists() and final.stat().st_mtime >= since - 120:
                return sucesso()

            alive = vivo(pid)
            ult = atividade(ep)
            state["render_vivo"] = alive
            state["ultimo_log"] = agora(ult) if ult else None
            age_min = (time.time() - ult) / 60.0 if ult else 999.0

            if alive and age_min <= a.stale_min:
                salvar("rodando")
                if a.once:
                    return 0
                time.sleep(a.interval)
                continue

            if alive:
                log("HANG: PID %d vivo mas sem atividade há %.1f min - matando árvore"
                    % (pid, age_min), logf)
                matar_arvore(pid)
                matar_orfaos(slug)
                state["historico"].append({"evento": "hang", "em": agora(),
                                           "idade_min": round(age_min, 1)})
                pid = 0
            else:
                code = codigo_saida(pid) if pid else None
                log("MORTO: PID %s saiu (rc=%s) sem final" % (pid, code), logf)
                state["historico"].append({"evento": "morto", "em": agora(),
                                           "rc": code})
                pid = 0

            matar_orfaos(slug)

            if gate_caiu(ep):
                state["gate_indisponivel"] = True
                with open(alertaf, "a", encoding="utf-8") as f:
                    f.write("[%s] gate AgentRouter indisponível; supervisor aguardando\n"
                            % agora())
                log("gate indisponível - aguardando 5 min antes de tentar de novo", logf)
                salvar("gate_indisponivel")
                if a.once:
                    return 0
                time.sleep(300)

            if state["restarts"] >= a.max_restarts:
                with open(alertaf, "a", encoding="utf-8") as f:
                    f.write("[%s] ALERTA: %d restarts sem final. Intervenção necessária.\n"
                            % (agora(), state["restarts"]))
                log("ALERTA: limite de %d restarts" % a.max_restarts, logf)
                salvar("alerta")
                return 2

            recuperar_nao_bancados(ep, slug, total, since, logf)
            if final.exists() and final.stat().st_mtime >= since - 120:
                return sucesso()

            state["restarts"] += 1
            state["historico"].append({"evento": "restart", "em": agora(),
                                       "tentativa": state["restarts"]})
            salvar("reiniciando")
            log("RESTART %d/%d - retomando do banco" %
                (state["restarts"], a.max_restarts), logf)
            pid = lancar(ep, logf)
            salvar("rodando")
            if a.once:
                return 0
            time.sleep(a.interval)
    finally:
        try:
            if lock.exists() and lock.read_text(encoding="utf-8").strip() == str(os.getpid()):
                lock.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
