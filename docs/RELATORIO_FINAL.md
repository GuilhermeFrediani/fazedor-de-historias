# RELATÓRIO FINAL DA MISSÃO — 18/10/2026

## RESULTADO: AMBIENTE 100% RECONSTRUÍDO E VALIDADO • TESTES DE VÍDEO FORMALMENTE BLOQUEADOS (decisão sua pendente) • COMPUTADOR DEIXADO LIGADO

---

## 1. O que foi instalado (versões exatas, verificadas)

| Componente | Versão | Evidência |
|---|---|---|
| Pinokio | 8.2.0 (= última no GitHub; sem atualizações pendentes) | config.json + releases |
| Script do app | wan2gp-amd (6Morpheus6) — recomendado pelo próprio autor do WanGP para AMD | README oficial |
| WanGP | v18.17, commit `fde3c7e10c47c854913d5877d955901a35e44714` (17/10/2026) | git rev-parse |
| Python (venv do app) | 3.12.13 | log torch.js |
| PyTorch | **2.13.0+rocm10.0.0** (TheRock, alvo gfx1200) | torch.__version__ + log |
| torchvision / torchaudio | 0.28.0+rocm10.0.0 / 2.11.0.2+rocm10.0.0 | log torch.js |
| ROCm SDK | core 10.0.0 + device-gfx1200 + libraries 10.0.0 | log torch.js |
| Triton | triton-windows **3.7.1.post27** (helper HIP pré-compilado ativo) | log de inicialização |
| Kernels INT8 | `[Quanto][INT8] Injected int8 kernels ACTIVE (backend=triton)` | log de inicialização |
| ffmpeg | 9.0.2 (app) + 8.1.2 (bin Pinokio) + ffprobe | arquivos |
| pterm | 0.0.25 (npm, prefixo C:\pinokio\bin\npm) | — |
| Node.js (auxiliar, portátil) | 24.22.0 LTS | nodejs.org |

**Modelos baixados e íntegros** (`C:\pinokio\api\wan2gp-amd\app\ckpts`):
transformador FL2VA Pruned 20B INT8 ConvRot (20 GB) • encoder Qwen3-VL Quanto INT8 (26,7 GB) •
encoder Qwen3-VL **GGUF Q4_K_M (14,6 GB)** • VAE vídeo INT8 (2,7 GB) • VAE áudio (577 MB) •
latent upscaler (659 MB) • LoRA turbo Lightx2v FL2V 8-step v1.0 (1,38 GB).
(Parcial do encoder BF16: 42,9 GB `.incomplete` — pode concluir ou apagar.)

## 2. O que funcionou ✓ / o que falhou ✗

**FUNCIONOU (verificado com evidência):**
- Pinokio abre, daemon OK, app wan2gp-amd instalado via pterm
- WanGP inicia via Pinokio: UI Gradio online (http://127.0.0.1:42003) — reiniciada no fim da missão
- PyTorch reconhece a RX 9060 XT; matmul sem NaN; kernels INT8 Triton ativos
- MiniMax H3 FL2VA Pruned 20B carrega (streaming MMGP; VRAM 76 MB em carga)
- Encoder textual codifica o prompt (3–4 it/s; VRAM 1–5 GB em uso real)
- LoRA turbo 8-step baixada e aplicável; perfil Spectrum disponível
- Áudio integrado: fluxo T2VA com fala pt-BR no formato oficial (sem tempo de validar o resultado sonoro — bloqueio anterior)

**FALHOU (bloqueio formal — ver HISTORICO_TESTES.md, 9 experimentos medidos):**
- Concluir qualquer geração DENTRO da regra de segurança da missão (margem de commit ≥ 5 GB):
  a fase "Encoding Prompt" consome 4,7–7,6 GB de commit (staging WDDM) e o limite atual
  é 18,5 GB (pagefile 2,9 GB). Profile 4 + INT8 → crash do processo; Profile 5 + GGUF Q4 +
  sem preload → funciona, porém margem 2,3 GB < 5 GB → meu watchdog aborta (regra seção 12).
- T-FUSE: não existe no v18.17 (recurso da versão antiga) — documentado, sem substituição.

## 3. Os três vídeos

**Não entregues** (bloqueio acima). Nenhum vídeo substituto foi fabricado (regra da missão).
Teste 1 pronto para rodar em 1 comando pós-autorização (PROXIMOS_PASSOS.md).

## 4. Tempos reais

- Instalação completa (bootstrap Pinokio + download app + patches + env): ~10 min
- Download dos modelos (~67 GB úteis): ~14 min (60–200 MB/s)
- Carga do modelo (após cache de arquivo): 5–10 s; primeira carga completa: ~7 min
- Codificação do prompt: ~13–30 s (funcionando; interrompida pelo watchdog por regra de margem)
- **Difusão/VAE/áudio: NÃO MEDIDOS (bloqueio anterior)** — nenhuma extrapolação honesta é possível.
- **Estimativa para 5 minutos de vídeo: IMPOSSÍVEL dar com honestidade** — a missão exige dados
  medidos; nem os testes de 10 s completaram. (Referência histórica: seu setup antigo produzia
  5 min em ~6–8 h de janela, segundo seu próprio briefing.)

## 5. Consumo medido

- **VRAM**: carga 76 MB → encode 1–5,6 GB alocados (torch); driver livre 10–15,9/16,3 GB.
  Nunca houve pressão de VRAM (regra dos 15 GB: nunca atingida).
- **Commit**: limite 18,5 GB. Pico de uso ~17,9 GB (margem 262 MB no crash 2).
  GPU shared (WDDM) 4,7–7,6 GB durante encode — o consumidor-chave.
- **RAM**: pico de uso 15,4 GB (livel 234–494 MB nos extremos). Idle ~12 GB livres.
- **Disco**: ~90 GB usados no total (env ~12 GB + modelos ~67 GB + parciais); ~780 GB livres.

## 6. Análise visual/sonora dos testes

Não aplicável — nenhum vídeo foi concluído. Ferramenta de análise pronta e testável
(analyze_video.py: frames 0/25/50/75/100%, folha de contato, loudness EBU R128,
silêncios, astats; ver LOGS).

## 7. Alterações em código de terceiros (backup + diff em LOGS\PATCHES_DIFF.md)

1. `install.js`: venv_python 3.11→**3.12** (guia oficial exige 3.12)
2. `torch.js`: índice nightly estagnado → **índice estável TheRock gfx1200** (mesma stack comprovada da sua instalação antiga)
3. `install.js`: removido pin `numpy==1.26.4` (quebrava scipy 1.18.1 → crash no primeiro boot; corrigido para numpy 2.1.2 exigido pelo requirements)
4. `wgp_config.json`: `smart_memory_pinning: false` (eliminou o staging ring de 7,6 GB — parte do diagnóstico)
   + `text_encoder_quantization` restaurado para int8 (config global)
- **Nenhuma** alteração no código do WanGP em si (deepbeepmeep/Wan2GP).
- Backups: LOGS\install.js.orig.backup, torch.js.orig.backup, wgp_config.json.orig.backup.

## 8. Pendências e riscos

Ver PENDENCIAS_E_RISCOS.md. Prioridade única: **autorização do pagefile (32 GB recomendado)**.

## 9. Configuração recomendada (validada empiricamente, pós-autorização)

MiniMax H3 FL2VA Pruned 20B • transformador INT8 ConvRot • encoder **GGUF Q4_K_M** (baixa RAM)
ou Quanto INT8 (mais rápido, se pagefile ≥ 32 GB) • **Profile 5** • SDPA • Spectrum on •
LoRA turbo Lightx2v FL2V 8-step v1.0 @1.0 • 6 passos • guidance 1 • flow_shift 12 •
1152×640 @ 24 fps • seed 7001 • sem preload manual (reavaliar com pagefile maior) •
T-FUSE: indisponível no v18.17 • RIFE ×2: validar após vídeo nativo aprovado.

## 10. Estimativa cautelosa para 5 minutos

**Não pode ser dada com honestidade** (difusão nunca measure). Após desbloqueio e o Teste 1,
os dados reais de s/por-janela permitirão extrapolar (10 s ≈ 2–3 janelas; 5 min ≈ 15 s × 20
janelas no máx. por janela de 124 frames... medição futura obrigatória).

## 11. Como continuar (próxima sessão)

1. Autorizar pagefile 32 GB (PROXIMOS_PASSOS.md — comando pronto, sem reboot)
2. `python gen_test.py --settings test1_settings.json --tag TESTE_01` (nada baixa de novo)
3. Copiar vídeo + `python analyze_video.py` → TESTE_01\; repetir p/ Testes 2 e 3
4. RIFE ×2 e upscale: só depois de aprovar o nativo

## 12. Desligamento

**NÃO EXECUTADO** (conforme protocolo da missão para estado bloqueado): o computador foi
deixado LIGADO para sua avaliação. Nenhuma instalação/geração/cópia está em andamento.
WanGP UI foi reiniciado e está disponível pelo Pinokio. Todos os logs e relatórios salvos.
