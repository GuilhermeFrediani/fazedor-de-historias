# PONTOS A ARRUMAR — v7 (seu dossiê × consertos)

Dossiê recebido em 2026-11-20. Seu veredito (5,5/6 contra o meu 8/9) está certo:
**o gate automatizado era frouxo na AMOSTRAGEM**, não na régua. Abaixo, cada defeito
com causa raiz, conserto e status. **Nenhum GPU queimado nesta rodada.**

---

## 1. Conflito de leis: a ocupação absoluta matou o cliente ✅

**Defeito:** todos os prompts mandavam `"no other people or animals appear"` enquanto
o Shot 3 do c06 pedia o cliente — o modelo obedece a proibição e o cliente nunca existe.

**Conserto — ocupação AGENDADA (2 bonecos + cliente só nas pontas):**
- **Prompts:** c01 e c06 agora dizem *"The military client in olive uniform appears ONLY
  in the shot that names him, silent, no dialogue"*; c02–c05 mantêm a lei absoluta
  (correto nos clipes do meio).
- **Gate:** `gate_ancora(..., cliente=bool)` + linha explícita
  `CLIENTE AUTORIZADO neste clipe: SIM/NAO`; sem autorização, qualquer terceira figura
  é `personagens_extras`.
- **Juiz episódico (SYS_B):** cliente legítimo só no PRIMEIRO e no ÚLTIMO clipe.
- **Roteiro:** c01 Shot 1 = cliente entrega a ordem (papel dobrado); c06 Shot 3 =
  cliente fecha com a nota fiscal.

## 2. Céu 43–54 s (12 s, pior que os ~6 s anteriores) — o gate amostrava demais pouco ✅

**Causa raiz corrigida:** NÃO é máscara do `image_end` (o `image_end` está MORTO na
cadeia desde o pivô solo-entry). O céu nasce **dentro** do render, e o gate duplo só
olhava **2 frames por clipe** (âncora f9.9 + meio f5.0) — o céu inteiro viveu entre as
amostras.

**Conserto — rede densa local (0 GPU, 0 API):** `pipeline/scan_ceu.py`
- 1 frame a cada **0,5 s**, faixa superior (28% da altura), métrica azul-céu
  (`B>150, B>R+25, B>G+15`).
- **Calibração provada com os olhos** (`refs/calibracao_scan/`): ruído estrutural do set
  (janela atrás da cortina, aço azulado) = **0–8%**; céu real = **17–31%**.
  Limiar **10%** separa com 2× de margem em cada lado.
- **Validação cega contra o v6a:**

```
c01 ok   c02 ok   c03 ok   c04 ok
c05  CÉU! 1,6–3,6 s  pico 28%   <- insert para o teto
c06  CÉU! 0,6–2,6 s  pico 31%   <- telhado aberto
```

  Exatamente as zonas do seu dossiê, **zero falso positivo**.

**Falta:** chamar o `scan_ceu` DENTRO do loop da cadeia (reprova antes do gate semântico).
Entra junto do próximo render.

## 3. Registro v2: cor / posse / conexão ✅

**Defeitos:** lápis amarelo→vermelho; trena na mão do TÉO (dossiê: bolso do JUCA);
maleta sem plantio.

**Conserto:**
- Gate SYS: *"as linhas com COR e POSSE são CONTRATO: a cor não muda nunca e o portador
  só muda se o estado narrar a troca de mãos"*; novo campo `props_violados` no JSON +
  enforcement (REPROVADA).
- `PROPS` da cadeia agora carrega cor/posse:
  *"YELLOW carpenter pencil (TEO's; never red)"*, *"steel tape measure (JUCA's chest
  pocket - never TEO's hand)"*, *"green document case (inside the sealed drum in c06)"*.
- **c03:** TÉO mede com o **lápis amarelo**; a trena fica no bolso do JUCA.
- **c05:** o lápis AMARELO é cravado no olho do gancho como pino — a gag que você aprovou,
  agora intencional e travada por cor.

## 4. Causalidade: maleta antes do barril → beat de retirada ✅

**Defeito:** insert da maleta aos 54 s ANTES do tambor selar (55–57) — ordem invertida.

**Conserto — Plano A do seu dossiê, c06 reescrito:**
- **Shot 1 (0–3,5 s):** insert do **tambor ainda pendurado**, tampa com trava de latão
  (planta a tampa que vai saltar).
- **Shot 2 (3,5–7 s):** queda + selo do ralo + tampa salta e flutua.
- **Shot 3 (7–10 s):** TÉO vira a tampa e alcança **dentro do tambor** → a maleta está lá
  → o cliente pega a folha molhada e deita sobre a maleta **como nota fiscal**.

Agora: selo (causa) → tampa abre → maleta dentro (retirada) → nota (payoff).

## 5. Travesseiro: swap rolo→travesseiro + teleporte + pedal fantasma ✅

**Conserto c04:**
- Shot 1: **o próprio JUCA** puxa o rolo de pads do carrinho e pisa nele (entrada por ação).
- Shot 2: *"that same roll swells into one fat pillow"* — o MESMO objeto incha.
  **Mata o swap rolo→travesseiro na raiz.**
- Pedal de lavagem **removido** do roteiro e do registro (era o objeto não plantado).

## 6. Lápis no gancho / queda da bota / ar morto ✅ (parcial)

- **Lápis no gancho:** texto explícito no c05 Shot 1, cor travada. ✅
- **Queda 25→26 não mostrada:** c03 Shot 2 ganhou *"one clear continuous fall"*
  (arco único e visível do plug). Física continua loteria de render. ✅ (texto)
- **Trims 0–1 s e 51–53 s:** são do CORTE, não do roteiro. O `--cortar-meio` já remove
  congelamento real; esses dois trechos são movimento lento que o freezedetect não pega
  → **poda manual anotada para o corte v7**. ⏳

## 7. Artefato "cuts to the camera cuts to" ✅

Eliminado nos 5 moldes (11 ocorrências). `--dry`: `prompt ok=True` em c04/c05/c06
e SET cirurgiado 1× por prompt.

---

## O que o próximo teste precisa (NÃO iniciado — sua ordem: sem render por ora)

1. **Cadeia v7 de 5 clipes:** c01, c03, c04, c05, c06 (o c02 fica — 9/10 no seu dossiê),
   ponte FL2VA, seeds-base 7001/7002/7102/7202/7200, retry ≤2.
2. **scan_ceu no loop** — reprova céu antes do gate semântico (custo: ~30 s de CPU).
3. **Emenda:** c01 + c02 (v5) + c03..c06 → `--cortar-meio` → poda manual 0–1 s / 51–53 s
   → gate episódico.
4. **Aceite do seu dossiê:** continuidade ≥8 · causalidade ≥8 · 0 não plantados ·
   cliente nas duas pontas · invariante de set 100% · 12 perguntas do DOSSIE_v4 = sim —
   exigido em **2 episódios consecutivos** antes de negociar os 300 s.

## Arquivos tocados nesta rodada (0 GPU)

| Arquivo | Mudança |
|---|---|
| `pipeline/scan_ceu.py` | rede densa de céu, calibrada e provada |
| `pipeline/qc_visao.py` | ocupação agendada (`cliente=`), registro v2 (`props_violados`), SYS_B cor/posse |
| `pipeline/conserta_prompts_v7.py` | cirurgia dos 5 moldes (asserção de contagem) |
| `settings/*_c01/c03/c04/c05/c06_*.json` | prompts v7 (cliente, lápis, pads, maleta, artefato) |
| `cadeia_patch_v6.py` | PROPS v2 + flag `cliente` por clipe |
| `refs/calibracao_scan/` | prova visual da calibração (5 recortes) |
