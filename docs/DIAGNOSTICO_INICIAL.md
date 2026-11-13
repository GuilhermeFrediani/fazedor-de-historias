# DIAGNÓSTICO INICIAL — 00_DIAGNOSTICO_INICIAL.md

**Data/hora:** 18/10/2026, ~19:00 (horário local)
**Missão:** Reconstruir ambiente, validar MiniMax H3 (Wan2GP) e entregar 3 vídeos de teste.

---

## 1. SISTEMA OPERACIONAL

| Item | Valor medido |
|---|---|
| SO | Windows 11 Pro |
| Versão/Build | 10.0.26200 (build 26200) |
| Disco C: | 999 GB total, **901 GB livres** (91,9 GB usados) |
| Outros drives | Nenhum (somente C:) |

## 2. CPU / RAM

| Item | Valor medido |
|---|---|
| CPU | AMD Ryzen 7 7700, 8 núcleos / 16 threads |
| RAM total | 15,90 GB (15.900.696 KB) |
| RAM livre no diagnóstico | ~9,1 GB |
| Pagefile | `C:\pagefile.sys`, **2.944 MB alocados**, uso atual 0 MB |
| Limite de commit | 18.413 MB (~18,4 GB) |
| Commit livre | ~9,3 GB no diagnóstico |

> ⚠️ **RISCO 1 (documentado, sem ação):** o pagefile atual (2,9 GB) é muito menor que o
> anterior (~40 GB). O limite de commit total é ~18,4 GB. Gerações de vídeo podem
> pressionar o commit. Conforme regras da missão, **não será alterado sem autorização**.
> Monitorarei commit continuamente; interrompo geração se margem < 5 GB.

## 3. GPU

| Item | Valor medido |
|---|---|
| GPU dedicada | AMD Radeon RX 9060 XT |
| Device ID | PCI\VEN_1002&DEV_7590 (família gfx1200 / RDNA4) |
| VRAM | **17.095.983.104 bytes = 15,93 GiB** (16 GB nominais) |
| Driver AMD | **32.0.31041.1004** (Adrenalin atual instalado) |
| iGPU | AMD Radeon Graphics (Raphael, DEV_164E), 512 MB — presente, não usada no fluxo |

## 4. SOFTWARE EXISTENTE

| Item | Estado |
|---|---|
| Pinokio | **INSTALADO** — v8.2.0, modo desktop, home `C:\pinokio` |
| Pinokio.exe | `C:\Users\Guilherme\AppData\Local\Programs\Pinokio\Pinokio.exe` (211 MB) |
| Pinokio em execução | NÃO (nenhum processo ativo no diagnóstico) |
| Pasta `C:\pinokio\api` | **VAZIA** — nenhum app instalado (criada em 16/10/2026) |
| Wan2GP | **AUSENTE** — caminho antigo `C:\pinokio\api\wan2gp-rocm10\app` não existe |
| Modelos/checkpoints | **AUSENTES** — sem cache HuggingFace, sem pastas de modelos |
| OpenCode | **INSTALADO** — Desktop app v2.0.31 em `AppData\Local\Programs\@opencodedesktop`, em execução |
| ffmpeg (PATH global) | **AUSENTE** — será usado o do Wan2GP ou do Pinokio |
| git (PATH global) | **AUSENTE** — Pinokio traz git embutido (`C:\pinokio\scripts\git`) |
| Python global | A confirmar (ambiente Python será gerenciado pelo Pinokio/Wan2GP) |
| PyTorch/ROCm | **AUSENTE** — nada instalado ainda |

## 5. BUSCA PELO PRINT DA CONFIGURAÇÃO ANTERIOR (limite: 1 passada)

Locais verificados com filtros por imagens/documentos (png/jpg/jpeg/bmp/webp/md/txt):

- `C:\Users\Guilherme\Desktop` → só atalhos (.lnk/.url), nenhuma imagem
- `C:\Users\Guilherme\Pictures` → vazio
- `C:\Users\Guilherme\Downloads` → vazio
- `C:\Users\Guilherme\Documents` → vazio (somente "Projeto Padrão" vazio e scripts PS)
- `C:\Users\Guilherme\Videos` → vazio

**RESULTADO: print NÃO encontrado.** A formatação apagou as capturas.
→ Conforme protocolo: seguir com a **configuração de referência documentada** (seção 6),
marcando claramente o que é valor histórico (a redescobrir empiricamente) versus fato medido.

## 6. CONFIGURAÇÃO DE REFERÊNCIA (histórica — valores a revalidar)

Estes são os valores da instalação ANTERIOR, registrados como referência, não como ordem:

- Wan2GP (deepbeepmeep/Wan2GP), WanGP v17.10, commit `ec9566a`
- MiniMax H3 FL2VA (vídeo+áudio integrados)
- Transformer INT8 quantizado, Preload 6000
- Resolução 1152×640 @ 24 fps nativos, RIFE ×2 → 48 fps
- 6 passos de difusão, LoRA turbo 8 passos, SDPA (SageAttention ficou ~49%/passo mais lento — NÃO ativar)
- T-FUSE ativo, Spectrum ativo (~2 passos ignorados em 6)
- Seed 7001, exportação H.264/AAC
- Versões antigas: Python 3.12.10, PyTorch 2.13.0+rocm10.0.0 (TheRock), Triton-Windows 3.7.1.post27
- Instalação antiga: `C:\pinokio\api\wan2gp-rocm10\app` (não existe mais)

**Valores CONFIRMADOS por medição hoje:** apenas hardware e OS (seções 1–4).
**Valores a REDESCOBRIR empiricamente:** versões atuais compatíveis de WanGP/PyTorch/ROCm
para gfx1200, funcionamento de Spectrum/T-FUSE nesta versão, tempos de geração.

## 7. VERIFICAÇÕES PENDENTES (FASE B)

1. Abrir o Pinokio e verificar atualizações pendentes.
2. Instalar Wan2GP pelo Pinokio (repositório oficial deepbeepmeep).
3. Ambiente Python + PyTorch ROCm com suporte a gfx1200 (RX 9060 XT).
4. Teste mínimo: `torch` reconhece a GPU e executa operação simples.
5. Download dos modelos MiniMax H3 FL2VA (+ INT8, LoRA turbo, RIFE).
6. Verificação de integridade dos arquivos baixados.
7. Verificação de ffmpeg dentro do ambiente Wan2GP.
8. Medição de memória em carga curta antes da primeira geração completa.

## 8. CONCLUSÃO DA FASE A

- ✅ Hardware confirmado e íntegro (GPU 16 GB, CPU 8C/16T, disco 901 GB livres)
- ✅ Pinokio 8.2.0 instalado (reinstalado ontem após formatação)
- ❌ Wan2GP ausente → instalar (FASE B)
- ❌ Modelos ausentes → baixar (FASE B)
- ⚠️ Pagefile pequeno (2,9 GB) → risco de commit, monitorar, não alterar sem autorização
- ❌ Print da configuração antiga não encontrado → usar referência documentada

**Decisão:** ambiente básico NÃO passou em todas as verificações (Wan2GP/modelos ausentes),
portanto NÃO iniciar geração de vídeo ainda. Prosseguir para FASE B (instalação incremental).
