# ATUALIZAÇÃO DO PIPELINE — 24/11/2026

Atualização completa pedida pelo usuário ("atualize TUDO para a última versão").
Tudo foi feito de forma **reversível** (backups + snapshot do ambiente).

## O que foi atualizado

| Componente | Antes | Depois |
|---|---|---|
| **Pinokio (app)** | 8.4.0 | **8.4.1** (release oficial `pinokiocomputer/pinokio`, sha512 conferido) |
| **Wan2GP (código)** | `fde3c7e1` | **`de32e90c` (v20.12)** — git pull do `deepbeepmeep/Wan2GP` |
| **wan2gp-amd (wrapper)** | `8944a73` (com patches locais) | merge `9ab7649` — patches preservados + pin novo |
| **PyTorch** | 2.13.0+rocm10.0.0 | **2.15.0+rocm10.2.0** (device-gfx1200, cp312, TheRock) |
| **torchvision** | 0.28.0+rocm10.0.0 | **0.29.2+rocm10.2.0** |
| **torchaudio** | 2.11.0.2+rocm10.0.0 | **2.11.1+rocm10.2.0** |
| **ROCm SDK** | 10.0.0 (rocm-sdk-core/libraries/device-gfx1200) | **10.2.0 completo** (TheRock `therock-10.2`) |
| **HIP runtime** | 7.15.26333 | 7.17.26434 |
| **GPU** | RX 9060 XT (gfx1200, 15,9 GB) | inalterada (RDNA4/GDDR6 — o patch do `torch.js` já cobria) |
| **Python** | 3.12.13 | inalterado |

Deps novas instaladas no venv (exigidas pelo Wan2GP 20.12):
`zyphra-textnorm==0.2.0`, `ddgs 9.16.1`, `pypdf 7.1.1`, `playwright 1.65.2`, `kaldifst 1.9.0`
(nota: o `install.js` do upstream escreve `kladifst==1.9.0` — **typo**: o nome no PyPI é `kaldifst`).

## Onde estão os backups (rollback)

- `C:\Users\Guilherme\AppData\Local\Temp\opencode\pip_freeze_pre_update.txt` — snapshot de 310 pacotes (versões exatas antes)
- `C:\Users\Guilherme\AppData\Local\Temp\opencode\gen_test_pre_update.py` — cópia do driver
- `...\Programs\pinokio\Pinokio.exe.v840.bak` — executável Pinokio 8.4.0 (restaurável em 1 comando)
- Rollback do torch: `pip install torch[device-gfx1200]==2.13.0+rocm10.0.0 torchvision[device-gfx1200]==0.28.0+rocm10.0.0 torchaudio==2.11.0.2+rocm10.0.0 --index-url https://stable.repo.amd.com/rocm/whl-next/`

## Verificação

- [x] GPU: matmul 2048 f16 OK (checksum conferido), `torch.cuda.is_available()`, gfx1200 reconhecido
- [x] Pinokio 8.4.1 sobe (ProductVersion 8.4.1)
- [x] Wan2GP 20.12 importa (`shared/api` intacto — `gen_test.py` compatível)
- [x] **render de fumaça 2 s APROVADO** (smoke_rocm102_test.mp4, 7,3 MB) — stack novo ponta a ponta
- [x] triton compila e roda no ROCm 10.2 (INT8/FP8 backends ativos)
- [x] knob novo: --max-ram 24 no _cli_extra (sem ele o load do encoder 32B estoura o commit da maquina — WinError 1455; page file fixo 32 GB, sem admin)

## Próximo

- Render de fumaça de 60 s (`cadeia_smoke60`) retomando do c03 com o stack novo.