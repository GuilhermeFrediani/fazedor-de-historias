# AMBIENTE E VERSÕES — Pesquisa e Decisão de Instalação

**Data:** 18/10/2026
**Objetivo:** escolher a combinação estável e compatível para RX 9060 XT (gfx1200), com base em evidências.

---

## 1. VERSÕES DOS COMPONENTES PRINCIPAIS (pesquisadas em 18/10/2026)

| Componente | Versão encontrada | Fonte |
|---|---|---|
| Pinokio | 8.2.0 (instalada) = **última** ( lançada 02/09/2026) | GitHub releases |
| WanGP (deepbeepmeep/Wan2GP) | **v18.17** (15/10/2026) — era v17.10 na instalação antiga | README master |
| pterm (CLI Pinokio) | 0.0.25 | npm |
| Node.js (portátil, ferramenta auxiliar) | 24.22.0 LTS "Krypton" | nodejs.org |
| PyTorch (estável TheRock p/ gfx1200) | **2.13.0+rocm10.0.0** (cp310–cp314 win_amd64) | stable.repo.amd.com/rocm/whl-next |
| torchvision estável correspondente | 0.28.0+rocm10.0.0 (cp312 win) | idem |
| torchaudio estável correspondente | 2.11.0.2+rocm10.0.0 (conforme guia oficial) | idem |
| Python requerido (guia AMD oficial) | **3.12** (o índice ROCm só carrega NumPy p/ 3.12+) | docs/AMD-INSTALLATION.md |
| Triton (AMD/Windows) | triton-windows 3.7.x (compatível c/ PyTorch 2.13) | guia AMD oficial |
| SageAttention (AMD) | 1.0.6 (opcional; SDPA foi mais rápido na instalação antiga) | guia AMD oficial |

## 2. CAMINHO DE INSTALAÇÃO ESCOLHIDO

O README oficial do WanGP diz textualmente:

> "It is recommended to use in Pinokio the Community Scripts *wan2gp* or *wan2gp-amd*
> by **Morpheus** rather than the official Pinokio install."

Para GPU AMD (RX 9060 XT, RDNA4), o script indicado é o **wan2gp-amd**
(https://github.com/6Morpheus6/wan2gp-amd), que:
- clona deepbeepmeep/Wan2GP dentro de `app/`;
- cria venv `app/env`;
- instala PyTorch/torchvision/torchaudio conforme o alvo GFX detectado (via `torch.js`);
- instala `requirements.txt` + `hf-xet setuptools numpy==1.26.4`;
- start.js roda `python wgp.py --multiple-images --advanced` (daemon Gradio).

## 3. PROBLEMA IDENTIFICADO NO SCRIPT ATUAL (evidência)

O `torch.js` do wan2gp-amd (branch main, commit atual) instala, para RDNA4
(gfx1200/gfx1201):

```
uv pip install --pre torch torchvision torchaudio --index-url https://rocm.nightlies.amd.com/v2-staging/gfx120X-all
```

O índice `v2-staging/gfx120X-all` foi verificado hoje:
- Última wheel publicada: `torch-2.10.0+rocm7.13.0a20260514` (**14/05/2026 — 5 meses parado**)
- Ou seja: PyTorch 2.10.0 nightly com ROCm 7.13 — **mais antigo** que o estável 2.13.0+rocm10.0.0.

O guia oficial atual do WanGP (docs/AMD-INSTALLATION.md, master, out/2026) manda usar
o índice **estável**:

```
pip install "torch[device-gfx1200]==2.13.0+rocm10.0.0" "torchvision[device-gfx1200]==0.28.0+rocm10.0.0" torchaudio==2.11.0.2+rocm10.0.0 --index-url https://stable.repo.amd.com/rocm/whl-next/
```

E ainda alerta: ambientes criados com os índices `rocm.nightlies.amd.com/v2` antigos
devem ser **substituídos**.

A instalação antiga do usuário (comprovadamente funcional) usava exatamente:
**PyTorch 2.13.0+rocm10.0.0, Triton 3.7.1.post27, SageAttention 1.0.6, Python 3.12.10**.

## 4. DECISÃO

Instalar o wan2gp-amd via Pinokio (caminho recomendado), com **patch mínimo e
documentado** em 2 pontos, alinhando-o ao guia oficial e à instalação antiga
comprovada:

1. `install.js`: `venv_python: "3.11"` → **"3.12"** (guia oficial exige 3.12;
   instalação antiga usava 3.12.10).
2. `torch.js` (caso RDNA4): índice nightly v2-staging → **índice estável
   stable.repo.amd.com/rocm/whl-next com versões fixas** (torch 2.13.0+rocm10.0.0,
   torchvision 0.28.0+rocm10.0.0, torchaudio 2.11.0.2+rocm10.0.0, device-gfx1200).

Justificativa: priorizar combinação estável e comprovada em vez de nightly
estagnada, conforme regra da missão ("Não instale uma versão mais nova apenas por
ser mais nova"). Backup dos arquivos originais + diff registrados em LOGS/.
Alteração reversível (reset.js do próprio app reverte para o estado original).

Diferenças em relação à instalação antiga (a documentar durante o processo):
- Pasta: `C:\pinokio\api\wan2gp-amd` (antes: `wan2gp-rocm10`) — nome atual do repo.
- WanGP v18.17 (antes v17.10): novos recursos H3 (H3 Veda Sparse, H3 LightVAE,
  perfis TaoMate 3-step, WGPKernels INT8 para RDNA4).
- Python: exato (3.12) será o que o uv baixar (registrarei a versão real).
- Triton/SageAttention: o script do Morpheus não instala explicitamente
  Triton/Sage (verificarei após o requirements e instalará se necessário conforme guia).

## 5. FLUXO DE TESTES PREVISTO (FASES C/D)

1. Instalação via Pinokio (install.js com patch).
2. Verificar: torch.cuda.is_available() == True e device = RX 9060 XT.
3. Iniciar via start.js (Gradio). Descobrir API (Gradio/MCP/filas headless).
4. Carregar MiniMax H3 FL2VA (INT8) + LoRA turbo quando aplicável.
5. Testes 1→2→3 progressivos (10–20 s), seed 7001, 1152×640, 6 passos, SDPA.
6. Inspeção de frames + áudio + memória (regras da seção 12 da missão).
