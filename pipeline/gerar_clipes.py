"""Piloto B — Geracao de clipes (v2.1 — PREPARADA; NAO EXECUTAR SEM APROVACAO EXPLICITA).

v2.1 (21/10/2026) — apos o diagnostico do borrão do v1:
  1. LoRA turbo 8-step anexado EXPLICITAMENTE em todos os settings (causa raiz do
     borrão: o lote v1 rodou SEM ele — "activated_loras":[] na metadata embutida;
     6 steps sem LoRA = sub-denoisado, -60% de acutancia vs os testes com LoRA).
  2. Gate novo validar_lora(): confere o LoRA na metadata EMBUTIDA de cada clipe
     gerado; clipe sem LoRA => rejeitado (a falha nunca mais passa despercebida).
  3. Saida em PRODUCAO\\CLIPES_V2\\ — os 38 clipes v1 (PRODUCAO\\CLIPES) ficam
     intocados (regra permanente do projeto: nao sobrescrever originais).

Lê os planos (ID, duracao_s, prompt) e gera sequencialmente com validacao.
Pula clipes ja gerados em CLIPES_V2 (resume capability).
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

APP_ROOT = Path(r"C:\pinokio\api\wan2gp-amd\app")
sys.path.insert(0, str(APP_ROOT))

_GIT = r"C:\pinokio\bin\miniforge\Library\ucrt64\bin\git.exe"
os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = _GIT
os.environ["PATH"] = r"C:\pinokio\bin\miniforge\Library\ucrt64\bin;" + os.environ.get("PATH", "")
os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")
os.environ.setdefault("HF_HOME", r"C:\pinokio\cache\HF_HOME")
os.environ.setdefault("TORCH_HOME", r"C:\pinokio\cache\TORCH_HOME")

from shared.api import init  # noqa: E402

FFMPEG = str(APP_ROOT / "ffmpeg_bins" / "ffmpeg.exe")
FFPROBE = str(APP_ROOT / "ffmpeg_bins" / "ffprobe.exe")

# v2.1 — LoRA turbo 8-step OBRIGATORIO (mesma URL validada nos testes/pilb_teste).
TURBO_LORA_8STEP = "https://huggingface.co/DeepBeepMeep/MiniMax-H3/resolve/main/loras/minimax_h3_lightx2v_fl2v_turbo_8step_alpha8_v1.0_bf16.safetensors"

# v2.1 — saida em pasta propria: os 38 clipes v1 em ...\PRODUCAO\CLIPES ficam intocados.
OUT = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\PILOTO_B_O_QUARTO_QUE_NAO_EXISTIA\PRODUCAO\CLIPES_V2")
STILLS = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\PILOTO_B_O_QUARTO_QUE_NAO_EXISTIA\PRODUCAO\STILLS")


def now():
    return time.strftime("%H:%M:%S")


# Todos os 38 planos do 02 v2 (ID, duracao_s, prompt)
# (copiado dos prompts do 03_PROMPTS v2 — sem REF/CHAIN pois T2VA puro por enquanto)
PLANOS = [
    # C01 — A PORTA IMPOSSÍVEL
    ("C01_P01", 6, "integrated_multimodal_description: [Shot 1] The facade of a small old city hotel at night, one warm lit window on the ground floor, a quiet empty street, slow drifting clouds crossing the moon. The camera pushes in slowly toward the lit window. Live-action cinematic realism, practical amber lighting, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: A distant city hush, a light breeze, and a single car passing far away.\nnon_diegetic_music: N/A"),
    ("C01_P02", 6, "integrated_multimodal_description: [Shot 1] An old hotel reception at night. A 32-year-old Brazilian man, short dark brown hair, clean-shaven, wearing a navy-blue night porter uniform with a small round brass name tag, sits at a dark wooden front desk under a warm desk lamp, slowly sorting a small stack of paper cards under the amber light. The camera pans left very slowly across the desk. Live-action cinematic realism, practical amber lighting, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: A quiet lobby hum, paper cards sliding softly, a wall clock ticking faintly.\nnon_diegetic_music: N/A"),
    ("C01_P03", 7, "integrated_multimodal_description: [Shot 1] An old hotel corridor at night, dark wood wainscoting, aged brass wall sconces casting small pools of amber light, worn burgundy carpet, faded sepia damask wallpaper. A 32-year-old Brazilian man, short dark brown hair, clean-shaven, wearing a navy-blue night porter uniform, walks slowly along the corridor carrying a small portable lamp, its warm light gliding across the wallpaper. The camera tracks alongside him at a slow, steady pace. Live-action cinematic realism, deep natural shadows, muted contrast, filmic grain. He does not speak.\noverall_soundscape: Soft footsteps on worn carpet and the low hum of the empty corridor.\nnon_diegetic_music: N/A"),
    ("C01_P04", 6, "integrated_multimodal_description: [Shot 1] Same old hotel corridor at night. The same Brazilian night porter in navy-blue uniform stops walking and slowly raises his portable lamp toward a wall ahead, his head tilting with quiet curiosity, his face calm and alert. Static shot, medium distance, amber practical light. Live-action cinematic realism, deep natural shadows, muted contrast, filmic grain. He does not speak.\noverall_soundscape: His footsteps stop; only the lamp's faint buzz remains.\nnon_diegetic_music: N/A"),
    ("C01_P05", 5, "integrated_multimodal_description: [Shot 1] A plain faded damask wallpapered wall in an old hotel corridor at night, lit by a warm portable lamp from the left edge of the frame. A dark wood door with a small aged blank brass plate stands flush in the middle of the wall, closed, patient, casting a soft shadow. Static shot. The door does not move. No readable text anywhere. Live-action cinematic realism, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: A held silence with the faint buzz of the lamp.\nnon_diegetic_music: N/A"),
    # C02 — O QUARTO
    ("C02_P01", 5, "integrated_multimodal_description: [Shot 1] The same corridor wall at night. The dark wood door with the blank brass plate opens slowly inward, and warm amber light spills from the gap into the dim corridor, sliding across the worn carpet. The camera does not move. The door keeps opening slowly until the doorway glows amber. Live-action cinematic realism, deep natural shadows, muted contrast, filmic grain. No people visible.\noverall_soundscape: A faint warm hum drifting from inside, distant and calm.\nnon_diegetic_music: N/A"),
    ("C02_P02", 6, "integrated_multimodal_description: [Shot 1] A 32-year-old Brazilian man, short dark brown hair, clean-shaven, wearing a navy-blue night porter uniform, steps slowly through an open dark wood doorway into a small warm room and pauses just inside, seen from behind, silhouetted against amber light. Static shot from inside the room. Live-action cinematic realism, deep natural shadows, muted contrast, filmic grain. He does not speak.\noverall_soundscape: His slow footsteps on carpet stop, replaced by a deep quiet warmth.\nnon_diegetic_music: N/A"),
    ("C02_P03", 8, "integrated_multimodal_description: [Shot 1] A small warm room with dark wood paneling: a dark wooden table in the center, a single wooden chair facing it, an amber desk lamp glowing on the table, beige curtains hanging flat against the back wall, an old black rotary telephone sitting on the left side of the table with a coiled cord. The camera pushes in very slowly from the doorway. Nothing moves except the light breathing in the lamp. Live-action cinematic realism, practical amber lighting, deep natural shadows, muted contrast, filmic grain. No people visible.\noverall_soundscape: A soft lamp hum and a stillness that feels attentive, like held breath.\nnon_diegetic_music: N/A"),
    ("C02_P04", 5, "integrated_multimodal_description: [Shot 1] Close insert of an old black bakelite rotary telephone with a round metal fingerwheel and a heavy handset resting on top, a brown coiled cord neatly curled, sitting on a dark wooden table under warm amber side light. Static shot. Nothing moves. Live-action cinematic realism, shallow depth of field, filmic grain, muted contrast.\noverall_soundscape: Deep quiet with a faint lamp hum.\nnon_diegetic_music: N/A"),
    ("C02_P05", 7, "integrated_multimodal_description: [Shot 1] The same small warm room. The same Brazilian night porter in navy-blue uniform walks slowly around the dark wooden table without touching anything, examining the room, while the camera arcs slowly with him, keeping the table and the amber lamp in frame. His face shows quiet disbelief contained behind professional calm. He does not speak. Live-action cinematic realism, practical amber lighting, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: Slow soft footsteps on carpet and the lamp's steady hum.\nnon_diegetic_music: N/A"),
    ("C02_P06", 5, "integrated_multimodal_description: [Shot 1] Close insert of beige curtains hanging perfectly flat against a dark wood paneled wall, warm amber light grazing their folds from the left. The fabric is completely still. No window is visible behind them. Static shot. Live-action cinematic realism, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: Silence with a barely audible hum.\nnon_diegetic_music: N/A"),
    ("C02_P07", 6, "integrated_multimodal_description: [Shot 1] The same small warm room. The Brazilian night porter pulls the wooden chair back a little and sits down slowly at the dark wooden table, facing the doorway, hands resting on his knees. Medium shot, slightly high angle. He does not speak. Live-action cinematic realism, practical amber lighting, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: The chair scrapes very softly on the floor, then quiet.\nnon_diegetic_music: N/A"),
    # C03 — A VOZ
    ("C03_P01", 6, "integrated_multimodal_description: [Shot 1] Close insert of the old black rotary telephone on the dark wooden table. The heavy handset trembles slightly on its cradle, vibrating with each ring, the coiled cord shivering. Warm amber light from the left. Static shot. Live-action cinematic realism, shallow depth of field, muted contrast, filmic grain.\noverall_soundscape: Three spaced rings of an old electric bell telephone, muffled and bright at once, in a small silent room.\nnon_diegetic_music: N/A"),
    ("C03_P02", 6, "integrated_multimodal_description: [Shot 1] The Brazilian night porter sits at the dark wooden table in the warm room, eyes wide open toward the old rotary telephone, completely still, one hand half raised, frozen mid-motion. The camera pushes in very slightly. His face shows contained alarm, not panic. He does not speak. Live-action cinematic realism, practical amber lighting, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: The muffled telephone rings twice more while he does not move.\nnon_diegetic_music: N/A"),
    ("C03_P03", 6, "integrated_multimodal_description: [Shot 1] Close side view of a man's hand slowly lifting the black bakelite handset of the old rotary telephone from its cradle and raising it toward the edge of the frame, the coiled cord stretching gently. Warm amber light, deep shadow behind. Static shot. The face stays out of focus. Live-action cinematic realism, shallow depth of field, muted contrast, filmic grain.\noverall_soundscape: The handset lifts with a soft plastic click; the ringing stops.\nnon_diegetic_music: N/A"),
    ("C03_P04", 10, "integrated_multimodal_description: [Shot 1] Close three-quarter view of the Brazilian night porter holding the old telephone handset to his ear, listening, perfectly still. His eyes widen for a moment, then soften into something older than surprise, a contained disbelief without a single word. Warm amber light from the desk lamp sculpts his face against deep shadow. The camera does not move. He does not speak and his lips stay closed. Live-action cinematic realism, shallow depth of field, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: A soft phone-line hiss under a held silence, as if the room itself is listening.\nnon_diegetic_music: N/A"),
    ("C03_P05", 5, "integrated_multimodal_description: [Shot 1] The amber desk lamp on the dark wooden table, warm light glowing, tiny dust motes drifting slowly through the beam in the still air. Static shot, close. Live-action cinematic realism, shallow depth of field, muted contrast, filmic grain.\noverall_soundscape: The lamp hums softly, and a faint line hiss continues underneath.\nnon_diegetic_music: N/A"),
    ("C03_P06", 6, "integrated_multimodal_description: [Shot 1] Close insert of the brown coiled cord of the old telephone, stretched slightly between the handset in a man's hand and the phone on the dark table, the coils pulling taut and trembling faintly, warm amber light along its curve. Static shot. Live-action cinematic realism, shallow depth of field, muted contrast, filmic grain.\noverall_soundscape: The cord creaks almost inaudibly; the line hiss keeps breathing.\nnon_diegetic_music: N/A"),
    # C04 — O PREÇO
    ("C04_P01", 10, "integrated_multimodal_description: [Shot 1] Medium-wide of the warm room: the Brazilian night porter seated at the dark wooden table, elbows on the table, holding the black telephone handset to his ear, listening carefully, lips closed, face calm and tense at once, the amber lamp glowing to his right. Static shot from the doorway side. He does not speak. Live-action cinematic realism, practical amber lighting, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: A soft line hiss and the lamp hum, no voices, like a call waiting.\nnon_diegetic_music: N/A"),
    ("C04_P02", 6, "integrated_multimodal_description: [Shot 1] Close insert of a man's fingers gently winding and unwinding the brown coiled telephone cord around his index finger, slow and repetitive, knuckles slightly whitening. Warm amber side light, dark wooden table edge in soft focus. Static shot. Live-action cinematic realism, shallow depth of field, muted contrast, filmic grain.\noverall_soundscape: The cord's plastic coils squeak softly under the line hiss.\nnon_diegetic_music: N/A"),
    ("C04_P03", 10, "integrated_multimodal_description: [Shot 1] Close three-quarter of the Brazilian night porter with the telephone handset at his ear; he closes his eyes for a long moment and takes one slow, controlled breath through the nose, jaw setting with quiet resolve. He does not speak, lips closed. Warm amber light, deep shadow behind. Static shot. Live-action cinematic realism, shallow depth of field, muted contrast, filmic grain.\noverall_soundscape: A single slow breath over the quiet line hiss.\nnon_diegetic_music: N/A"),
    ("C04_P05", 8, "integrated_multimodal_description: [Shot 1] Close of a man's hand gripping the black bakelite handset of the old rotary telephone pressed to his ear, knuckles slightly tightening, the coiled cord swaying gently with a small tremor. Warm amber light, deep shadow behind. Static shot. Live-action cinematic realism, shallow depth of field, muted contrast, filmic grain.\noverall_soundscape: The faint creak of the cord and a soft, warm line hiss.\nnon_diegetic_music: N/A"),
    ("C04_P04", 10, "integrated_multimodal_description: [Shot 1] From the open doorway, a wide view of the small warm room: the Brazilian night porter small in frame on the wooden chair at the dark table, telephone to his ear, the amber desk lamp glowing beside him. Midway, the lamp light dims briefly and gently once, like a slow blink, then returns to full warmth. Static shot. Live-action cinematic realism, practical amber lighting, deep natural shadows, muted contrast, filmic grain. He does not speak.\noverall_soundscape: The lamp hum dips softly with the light and steady silence holds.\nnon_diegetic_music: N/A"),
    # C05 — O QUE NUNCA DISSE
    ("C05_P01", 8, "integrated_multimodal_description: [Shot 1] A modest 1990s Brazilian kitchen at early dawn: a middle-aged woman seen only from behind, brewing coffee in an old pot on a white stove, steam rising gold in the soft window light, a small radio on the counter, faded floral curtains. The camera pushes in very slowly toward her back. Her face is never visible. Gentle filmic grain slightly heavier than reality, warm faded tones, dreamlike stillness. Live-action cinematic realism.\noverall_soundscape: Coffee percolating softly, a spoon circling inside a pot, a radio murmuring an old song far away.\nnon_diegetic_music: N/A"),
    ("C05_P02", 8, "integrated_multimodal_description: [Shot 1] Side medium of the Brazilian night porter at the dark wooden table, forehead resting on his open hand, elbow on the table, the telephone handset pressed to his ear, eyes closed, shoulders heavy. The amber lamp glows behind him. Static shot. He does not speak. Live-action cinematic realism, practical amber lighting, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: A held breath and the soft line hiss.\nnon_diegetic_music: N/A"),
    ("C05_P03", 8, "integrated_multimodal_description: [Shot 1] Very close profile of the Brazilian night porter's eye region, lashes wet and shining, the lid firm, refusing to blink more than once, warm amber light catching the moisture. Static shot, extreme shallow focus. He does not speak. Live-action cinematic realism, muted contrast, filmic grain.\noverall_soundscape: Silence with a faint lamp hum.\nnon_diegetic_music: N/A"),
    ("C05_P04", 8, "integrated_multimodal_description: [Shot 1] Three-quarter view of the Brazilian night porter with the telephone handset at his ear, half of his face falling into deep shadow so his mouth is barely visible, head tilting down slightly, the smallest movement of a man speaking with his eyes lowered. His lips stay mostly hidden in shadow and move minimally. Warm amber edge light. Static shot. Live-action cinematic realism, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: The lamp hum under a quiet, warm line hiss.\nnon_diegetic_music: N/A"),
    ("C05_P05", 15, "integrated_multimodal_description: [Shot 1] Medium frontal of the Brazilian night porter seated at the dark wooden table with the telephone handset lowered to his shoulder, slowly straightening his back, his shoulders easing down, his face loosening into quiet relief, eyes glistening, lips closed. The amber lamp warms his face. The camera pushes in very slowly. Live-action cinematic realism, practical amber lighting, deep natural shadows, muted contrast, filmic grain. He does not speak.\noverall_soundscape: The quiet room receives a long, settling exhale.\nnon_diegetic_music: N/A"),
    # C06 — A DESPEDIDA
    ("C06_P01", 10, "integrated_multimodal_description: [Shot 1] Close three-quarter of the Brazilian night porter with the telephone handset at his ear, listening with the smallest wet smile, eyes soft and shining, perfectly still. Warm amber light. Static shot. Lips closed. Live-action cinematic realism, shallow depth of field, muted contrast, filmic grain.\noverall_soundscape: A faint warm hiss, like a voice about to end.\nnon_diegetic_music: N/A"),
    ("C06_P02", 6, "integrated_multimodal_description: [Shot 1] Close of two hands gently lowering the black bakelite handset onto the telephone cradle, slow and careful, like laying down something sleeping, the coiled cord easing. Warm amber light, deep shadow. Static shot. Live-action cinematic realism, shallow depth of field, muted contrast, filmic grain.\noverall_soundscape: A soft final click, then true silence.\nnon_diegetic_music: N/A"),
    ("C06_P03", 10, "integrated_multimodal_description: [Shot 1] The Brazilian night porter stands beside the wooden chair, seen from behind, looking slowly around the small warm room — the dark table, the amber lamp, the beige curtains — taking it in one last time. The camera pulls back very slowly. He does not speak. Live-action cinematic realism, practical amber lighting, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: A silent room, warm and still.\nnon_diegetic_music: N/A"),
    ("C06_P04", 8, "integrated_multimodal_description: [Shot 1] From the dim corridor, the open dark wood doorway glows amber as the Brazilian night porter steps out into the corridor, and the door slowly swings shut by itself behind him, softly, until it closes flush with the wall. Static shot from the corridor. No readable text. Live-action cinematic realism, deep natural shadows, muted contrast, filmic grain.\noverall_soundscape: A soft wooden thud of the door meeting its frame, then corridor hum.\nnon_diegetic_music: N/A"),
    ("C06_P05", 8, "integrated_multimodal_description: [Shot 1] The plain faded damask wallpapered wall in the corridor at night, empty and seamless, with no door at all, exactly as it always was. The Brazilian night porter stands facing it and places his palm slowly against the wallpaper, holding it there. The camera pushes in slowly toward his hand on the empty wall. Live-action cinematic realism, deep natural shadows, muted contrast, filmic grain. He does not speak. There is no door on the wall.\noverall_soundscape: A faint touch on paper and the corridor's low hum.\nnon_diegetic_music: N/A"),
    # C07 — A CHAVE 17
    ("C07_P01", 7, "integrated_multimodal_description: [Shot 1] Medium of the Brazilian night porter in the dim corridor looking down at his own hand as it slowly pulls something small from his trouser pocket, closing around it. Warm sconce light from the left, deep shadows. Static shot. He does not speak. The object stays hidden in his fist. Live-action cinematic realism, muted contrast, filmic grain.\noverall_soundscape: Fabric shifting softly, then quiet.\nnon_diegetic_music: N/A"),
    ("C07_P02", 8, "integrated_multimodal_description: [Shot 1] Macro of an open palm holding a small aged brass key with a simple flat bow, plain and unmarked. The fingers slowly turn the key in the warm amber light, metal glinting softly. No engraving, no digits, no text. Static macro shot, extreme shallow depth of field. Live-action cinematic realism, muted contrast, filmic grain.\noverall_soundscape: A faint metallic slide against skin.\nnon_diegetic_music: N/A"),
    ("C07_P03", 7, "integrated_multimodal_description: [Shot 1] Close three-quarter of the Brazilian night porter looking down at the small brass key in his palm, a small confused smile forming, eyes glistening, while the deep blue of late night persists in the corridor's amber glow. Static shot. He does not speak. Live-action cinematic realism, night ambience, muted contrast, filmic grain.\noverall_soundscape: A distant early tram passing far away, very quiet.\nnon_diegetic_music: N/A"),
    ("C07_P04", 8, "integrated_multimodal_description: [Shot 1] A dim apartment at night: a wooden nightstand beside a rain-streaked window, blurred city lights through the rain. A closed adult hand rests on the nightstand and slowly opens, revealing a small aged brass key, plain and unmarked, identical to a lost memory. No face in frame. Static shot. Live-action cinematic realism, cool blue night light against warm brass, muted contrast, filmic grain.\noverall_soundscape: Steady soft rain against glass and the low murmur of a sleeping city.\nnon_diegetic_music: N/A"),
    ("C07_P05", 6, "integrated_multimodal_description: [Shot 1] Macro of the small aged brass key resting on the open palm in the nightstand's shadow, rain light rippling over it, the hand perfectly still. The camera pulls back very slightly and the image breathes toward darkness. No text, no engraving. Live-action cinematic realism, muted contrast, filmic grain.\noverall_soundscape: Soft rain, then only the room.\nnon_diegetic_music: N/A"),
]


def validar(video_path):
    """Valida decode e duração do clipe."""
    if not Path(video_path).exists():
        return False, "arquivo inexistente"
    r = subprocess.run([FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "json", video_path], capture_output=True, text=True, timeout=15)
    try:
        d = float(json.loads(r.stdout)["format"]["duration"])
        return True, f"{d:.2f}s"
    except Exception:
        return False, "ffprobe falhou"


def validar_lora(video_path):
    """v2.1 — gate: confere na metadata EMBUTIDA se o LoRA turbo foi aplicado.

    Recibo da propria geracao (WanGP grava 'activated_loras' no comment do MP4).
    Sem LoRA => (False, motivo) => clipe rejeitado pelo lote.
    """
    r = subprocess.run([FFPROBE, "-v", "quiet", "-show_entries", "format_tags=comment",
                        "-of", "json", str(video_path)], capture_output=True, text=True, timeout=15)
    try:
        comment = json.loads(r.stdout)["format"]["tags"].get("comment", "")
    except Exception:
        return False, "sem metadata embutida"
    m = re.search(r'"activated_loras":(\[[^\]]*\])', comment)
    arr = m.group(1) if m else "[]"
    if "turbo" not in arr:
        return False, f"LoRA turbo AUSENTE na metadata (activated_loras={arr})"
    return True, "LoRA turbo OK no metadata"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    log_path = OUT / "clipes_log.jsonl"

    with open(log_path, "a", encoding="utf-8") as log:
        def ev(kind, data):
            log.write(json.dumps({"t": now(), "kind": kind, "data": data}, ensure_ascii=False, default=str) + "\n")
            log.flush()

        ev("start", {"total_planos": len(PLANOS)})

        session = init(
            root=APP_ROOT,
            cli_args=["--attention", "sdpa", "--profile", "5"],
            console_output=False,
        )

        total_t0 = time.time()
        aprovados, erros = [], []

        for plano_id, dur, prompt in PLANOS:
            # v2.1 — resume correto: o arquivo real chama-se pilb_<plano> (o v1 checava
            # "<plano>_v1.mp4", que nunca existia => resume quebrado, fix incluido).
            out_file = OUT / f"pilb_{plano_id}.mp4"
            if out_file.exists():
                ev("skip", {"id": plano_id, "motivo": "ja existe"})
                print(f"[SKIP] {plano_id} — já existe")
                aprovados.append(plano_id)
                continue

            settings = {
                "model_type": "minimax_h3_fl2va_pruned",
                "num_inference_steps": 6,
                "resolution": "1152x640",
                "force_fps": 24,
                "video_length": f"{dur}s",
                "seed": 7001,
                "guidance_scale": 1,
                "flow_shift": 12,
                "skip_steps_cache_type": "spectrum",
                "audio_prompt_type": "",
                # v2.1 — A JUSTIFICATIVA DE TUDO: sem este campo o lote v1 rodou sem
                # o LoRA turbo (metadata: "activated_loras":[]) e saiu sub-denoisado.
                "activated_loras": [TURBO_LORA_8STEP],
                "loras_multipliers": "1.0",
                "output_filename": f"pilb_{plano_id}",
                "config": "gguf_q4_k_m",
                "prompt": prompt,
            }

            t0 = time.time()
            ev("generating", {"id": plano_id, "duracao_alvo": f"{dur}s", "t0": t0})
            print(f"[GEN] {plano_id} ({dur}s)...")

            try:
                job = session.submit_task(settings)
                result = job.result()
                gen_time = time.time() - t0

                if not result.success or not result.generated_files:
                    ev("error", {"id": plano_id, "tempo": round(gen_time), "errors": [str(e) for e in result.errors]})
                    print(f"[ERRO] {plano_id}: {result.errors}")
                    erros.append(plano_id)
                    continue

                src = result.generated_files[0]
                ok, info = validar(src)
                if ok:
                    # v2.1 — gate do LoRA: rejeita clipe gerado sem o turbo
                    ok_lora, info_lora = validar_lora(src)
                    if not ok_lora:
                        ok, info = False, info_lora
                    else:
                        info = f"{info} | {info_lora}"
                if ok:
                    subprocess.run(["robocopy", str(Path(src).parent), str(OUT), Path(src).name, "/mov", "/njh", "/njs", "/ndl", "/nc", "/ns"], capture_output=True, timeout=60)
                    ev("ok", {"id": plano_id, "tempo_s": round(gen_time), "info": info, "arquivo": str(out_file)})
                    print(f"[OK] {plano_id} — {gen_time:.0f}s — {info}")
                    aprovados.append(plano_id)
                else:
                    ev("validacao_falhou", {"id": plano_id, "motivo": info})
                    print(f"[ERRO VAL] {plano_id}: {info}")
                    erros.append(plano_id)

            except Exception as exc:
                ev("exception", {"id": plano_id, "erro": str(exc)[:300]})
                print(f"[EXCEPTION] {plano_id}: {exc}")
                erros.append(plano_id)

        total_dur = time.time() - total_t0
        ev("done", {"aprovados": aprovados, "erros": erros, "total_s": round(total_dur)})

    print(f"\nLOTE CONCLUIDO: {len(aprovados)}/{len(PLANOS)} aprovados em {total_dur/60:.0f} min")
    if erros:
        print(f"ERROS: {erros}")
    # salvar lista de aprovados para o proximo passo
    (OUT / "aprovados.json").write_text(json.dumps(aprovados, indent=2))
    print(f"Lista: {OUT / 'aprovados.json'}")


if __name__ == "__main__":
    main()
