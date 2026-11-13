# PENDÊNCIAS E RISCOS

## RISCO 1 — Pagefile pequeno — ✅ RESOLVIDO (18/10/2026, sessão de recuperação)

- **Resolvido:** com sua autorização, aplicado **pagefile fixo de 32 GB**
  (LOGS\PAGEFILE_APLICACAO.log; rollback em LOGS\ROLLBACK_PAGEFILE.txt).
- **Medição:** limite de commit **18,04 GB → 47,16 GB** (confirmado após reboot).
- **Prova de eficácia:** o Teste 1 rodou com margem de commit mínima de **22,8 GB**
  (critério de parada: 5 GB) e produziu o primeiro vídeo válido (TESTE_01).
- Observação: com o limite ampliado, o encoder **Quanto INT8** (mais rápido que o GGUF,
  3–4 it/s vs ~1 it/s) voltou a ser uma opção a validar em teste futuro; a configuração
  atual validada usa GGUF Q4_K_M.

## RISCO 2 — Modelo 33B completo incompatível com 16 GB de RAM

- O modelo FL2VA 33B (INT8 ≈ 33 GB) não cabe nem em RAM+commit atual. A escolha validada
  foi o **Pruned 20B** (INT8 ≈ 21 GB, com streaming MMGP). Se você quiser o 33B, será
  necessário aumentar RAM e/ou pagefile substancialmente.

## PENDÊNCIA 3 — T-FUSE não existe no v18.17

- Recurso presente na instalação antiga (v17.10) não encontrado no código atual.
- Substituído funcionalmente por otimizações internas (fused QKV/split, VAE otimizada).
- Nenhuma ação forçada foi tomada (regra da missão: se Spectrum/T-FUSE não funcionar,
  registrar e seguir).

## PENDÊNCIA 4 — RIFE ×2 a validar separadamente

- A missão pede RIFE ×2 (24→48 fps) SOMENTE após validar a geração nativa.
- Ver HISTORICO_TESTES.md para o status da validação de pós-processamento.

## RISCO 5 — WGPKernels-AMD experimental

- Wheel INT8 próprio do WanGP para RDNA4 (rocm100) é explícito "unvalidated on AMD".
- Decisão: manter INT8 "auto" (Comfy Kitchen HIP / Triton), documentado.

## RISCO 6 — Avaliação subjetiva de áudio

- Eu não tenho alto-falantes/ouvido. A avaliação de áudio foi OBJETIVA (canais, taxa,
  loudness EBU R128, picos, silêncios, espectrograma + fala detectada).
- A apreciação subjetiva (naturalidade da voz em pt-BR) fica pendente para você ouvir.

## PENDÊNCIA 7 — Pinokio "Disk Saver"

- O Pinokio 8.2.0 tem o recurso "Universal Disk Saver" (deduplicação de bibliotecas).
- O script wan2gp-amd oferece "Save Disk Space" (link.js). Não executado nesta missão
  (não é necessário agora; disco com espaço amplo). Se quiser economizar dezenas de GB,
  rodar depois pelo menu do app no Pinokio.

## PENDÊNCIA 8 — Node.js portátil (ferramenta auxiliar)

- Para automação via `pterm` foi usado Node.js 24.22.0 portátil (zip oficial) em
  `C:\Users\Guilherme\AppData\Local\Temp\opencode\nodejs` + `pterm` 0.0.25 instalado em
  `C:\pinokio\bin\npm`. Se a pasta Temp for limpa, reinstalar o Node (ou usar o nodejs
  24.18.0 que o Pinokio baixou em `C:\pinokio\bin`) para rodar pterm.
