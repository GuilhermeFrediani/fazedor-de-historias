# PLANO v6 — fechar continuidade ≥8 (DECISÃO FINAL após testes A/B)

## Veredicto dos testes de controle (17/11)
- **Teste A (plate móvel + ControlNet)**: clipe controlado rc=0 (41,8 min c/
  download), 3 planos ok, gate APROVADA — MAS o céu veio de HERANÇA: a âncora
  do c05 já nasce com céu (gate era cego ao teto) e o plate de 10s idle deriva
  (derruba o tambor, alarga o céu, seca o piso). O controle transmite a deriva
  fielmente. Gramática de planos achatou (close não acontece). f0.2 18,5 dB.
- **Teste B (guia estático do PNG)**: ABORTA no watchdog — o VAE Encoding de
  guias (10s E 5s) ratcheta o pool de VRAM até driver 0,0 nesta GPU (16 GB).
  Penhasco estrutural do caminho controlado aqui. max_split_size_mb adiou o
  abort para 15 min (VAE encoding do guia), não resolveu. Módulo em cache;
  caminho documentado como fallback futuro, não é o v6.

## A arquitetura v6 (provada peça por peça, sem penhasco)
1. **Cadeia fl2va com image_start** (26,8 dB provado, ~15 min/clipe, gramática
   v4 intacta — elogiada no resumo do v5)
2. **Gate DUPLO por clipe** (zero GPU extra — só 1 chamada de API a mais):
   âncora f9.9 + MEIO f5.0, ambos com registro de props + INVARIANTE DE TETO
   - PROVADO: c04 âncora REPROVADA (telefone/trena/painel reaparecidos)
   - PROVADO: c05 meio REPROVADO (extintor de incendio, painel eletrico — o
     fantasma exato do resumo)
   - PROVADO: ancora_calada REPROVADA pelo teto ("ceu aberto no topo")
   - as 3 classes de defeito de continuidade do resumo agora têm cerca
3. **Retry seed+1 ×2** ao reprovar; 3ª falha = cadeia para (regra da série —
   o bug está no TEXTO, nunca re-render às cegas)
4. Pós: trim de ar morto por plano (--cortar-meio, provado em síntese),
   loudnorm, punch-in

## Texto já corrigido junto (commits edb1388)
- cliente na CHEGADA com rosto (c02 shot 1 tilt-up)
- c06 re-ancorado à corrente no corte do plano; estado_out com gancho→tambor

## Custo estimado do episódio 60 s
6 clipes × ~15 min + 1-3 retries prováveis ≈ **1,8–2,3 h GPU** (dentro do
envelope aprovado). Portão: 2 episódios ≥8/8 antes dos 300 s.

## Lição permanente
A deriva de set entra pela ÂNCORA (estocástica) e é bloqueada por gate —
não por controle pesado. O gate é o componente barato e decisivo.
