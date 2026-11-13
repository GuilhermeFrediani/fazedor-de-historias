# AUDITORIA SOMENTE-LEITURA — PACOTE PILOTO B + RELATÓRIO VEDA (19/10/2026)

**Escopo:** os 8 arquivos de `PILOTO_B_O_QUARTO_QUE_NAO_EXISTIA\` + `VEDA_AB_RELATORIO.md`.
**Método:** leitura integral + verificação programática (word-counts por regex, somas
"Gerar→usar" por plano, cross-check de tags CHAIN/REF, cobertura 02↔03, stills 04↔02/03).
**Nada foi alterado.** Scripts de análise ficaram fora do pacote (temp).

---

## PARTE 1 — VERIFICAÇÕES ESTRUTURAIS (o que CONFIRMA)

| Verificação | Resultado |
|---|---|
| 37 planos no 02 ↔ 37 prompts no 03 | ✓ cobertura perfeita, nenhum órfão em nenhum sentido |
| Beats do roteiro somam 300 s (25+40+45+50+55+50+35) | ✓ |
| Estrutura narrativa (gancho→desenvolvimento→clímax→conclusão+gancho 17) | ✓ presente e adequada |
| Disciplina anti-texto ("17"/placa/crachá sempre na pós) | ✓ consistente em 01/02/03/04 (negações de texto nos prompts: 5 no 03, 3 no 04) |
| Estratégia sem lip-sync (mãe nunca em cena; Miguel fala de perfil/penumbra) | ✓ mantida em todos os prompts |
| Bíblia visual ↔ prompts (blocos verbatim: Miguel/quarto/telefone/chave/cenários) | ✓ descritores batem |
| Stills ST-01..07: definidos no 04 ↔ citados no 02/03 | ✓ nenhum citado-indefinido, nenhum definido-não-citado |
| Watchdog/regras de segurança respeitados no pacote (custos [M]/[E]/[P] separados) | ✓ |
| Riscos de geração têm alternativa documentada por plano (02) | ✓ inclusive os 5 de risco máximo |
| VEDA_AB_RELATORIO: separação fatos/hipóteses/projeções (§10) | ✓ presente e correta |
| VEDA: distinção seletor (observado) / kernel (não testado) / ganho (não medido) | ✓ as três camadas estão distintas |

## PARTE 2 — LISTA PRIORIZADA DE PROBLEMAS (não corrigidos — conforme instrução)

### P1 — BLOQUEIAM o avanço ao G1

**P1-1. O tempo do roteiro não fecha em 300 s — o filme como escrito dura ~6:15-6:30.**
- **Arquivo/seção:** `01_ROTEIRO_NARRADO.md` (linhas "Palavras Bx" + tabela "Resumo
  técnico"); janelas dos beats; reflexo em `02` (títulos C04/C05/C06/C07) e `06` (tabela timeline).
- **Evidência (contagem programática real):** total falado **709 palavras** (declara ~690):
  B4 = 129 (35 narr + 94 diál.) e B7 = 132 — em 140/110 wpm + pausas marcadas:
  **B4 73,3 s vs 50 s (+23) • B5 70,2 vs 55 (+15) • B6 56,9 vs 50 (+7) • B7 63,1 vs 35 (+28)**
  → fala+pausas ≈ **372 s** + cartela ≈ 10 s ≈ **6:22**. Mesmo em leitura rápida (150/120 wpm): ~5:45.
  Causa-raiz: os "~Xs" por beat aplicam ritmo único de NARRAÇÃO a trechos de DIÁLOGO.
- **Impacto:** ou o filme passa do alvo (~80 s), ou a edição corta conteúdo sem plano —
  e o próprio 01 proíbe acelerar a voz para caber.
- **Recomendação (decisão de direção sua):** aparar ~90–110 palavras concentradas em
  B4 (regra da mãe) e B7 (narrata final) **ou** re-alvo documentado ~5:20–5:30. A
  "Pauta de leitura" do 01 (ler em voz alta e cortar B7 se passar de 5:10) já intui o
  problema — mas só cobre B7.

**P1-2. Contagens contraditórias DENTRO do 01 (mascaram P1-1).**
- **Arquivo/seção:** `01`, linha inline B7 ("**Palavras B7: 128 → ~50 s**") **vs** tabela
  ("B7 | 35 s | 108") **vs** real (**132** palavras → ~63 s); B4 tabela 118 vs real 129.
- **Impacto:** a tabela alimenta o plano de produção; três valores diferentes para o
  mesmo beat impedem ver o estouro de tempo.
- **Recomendação:** recálculo programático na revisão (o script de auditoria é reutilizável).

**P1-3. Deficit de IMAGEM nos beats de diálogo (mesmo usando 100% do gerado).**
- **Arquivo/seção:** `02` (resumo por cena vs janelas dos beats) e `06` (tabela que
  assume "~40 s" por beat cheio de clipes).
- **Evidência:** demanda vs máximo gerado: **B3 45→39 (−6) • B4 50→32 (−18) • B5 55→44
  (−11) • B6 50→38 (−12)**; o "usado planejado" (193 s) deixa 107 s de holds na timeline.
- **Impacto:** a edição precisará de takes longos/reuso — pode FUNCIONAR para uma
  conversa telefônica, mas é uma escolha de estilo que os documentos não declaram;
  risco de B4 arrastado com 24 s planejados para 50 s de janela.
- **Recomendação:** decidir explicitamente: (a) aceitar holds documentados (subir "usar"
  ao máximo gerado), (b) +4–6 inserts de reação (~+40–60 s de geração ≈ +1–1,7 h), ou
  (c) encurtar beats (combina com P1-1).

### P2 — Corrigir ANTES de gerar (sem decisão criativa)

**P2-4. Contradição 02↔03 no primeiro rosto do filme (C01_P02).**
- `02` (C01_P02) promete "REF: ST-01 + CORRIDOR"; `03` (C01_P02) não tem tag nenhuma.
- Impacto: a primeira aparição de Miguel sem âncora de identidade — deriva começa no
  plano 2. Recomendação: adicionar `[REF: ST-01 + ST-02]` ao prompt.

**P2-5. Plano mais delicado sem referência existente (C06_P05 "a parede lisa").**
- `02` pede "REF: **ST-02 SEM porta**"; `04` define ST-02 **COM** porta — a variante
  "sem porta" não existe na tabela de stills (nenhum "ST-08" definido).
- Impacto: o plano que PROVA o desaparecimento da porta não tem placa aprovável no G1.
- Recomendação: definir ST-08 (corredor SEM porta) no 04 e no fluxo G1 — ou documentar
  derivação (crop de C01_P03, corredor sem porta).

**P2-6. Quatro planos com Miguel sem âncora de identidade.**
- Evidência (auditoria de tags): **C04_P04 e C06_P03** chain do cômodo VAZIO (C02_P03) —
  Miguel "aparece" sem fonte de rosto; **C07_P01** chain da parede (C06_P05); e C01_P02 (P2-4).
- Impacto: troca de rosto = os regens mais caros (planos de 8–10 s com atuação).
- Recomendação: regra explícita no 03: todo plano com rosto cita ST-01 (direto ou chain
  cujo upstream tenha ST-01); chain apenas para continuação da MESMA composição.

**P2-7. Semântica CHAIN/REF ambígua em 4 pontos.**
- `03`: C05_P04 e C07_P03 ("CHAIN: X **→** REF ST-01" — dois mecanismos sem precedência);
  C02_P06 ("CHAIN: C02_P03 **(crop)**" — crop do quê?); C03_P06 (chain entre composições
  diferentes — chain força a composição anterior, inviável para insert novo).
- Impacto: o operador vai improvisar na hora = gerações desperdiçadas.
- Recomendação: dicionarar no 03: CHAIN = mesma composição; REF = nova composição;
  "CHAIN, fallback REF X" quando ambos.

### P3 — Médios/baixos

**P3-8. Erros aritméticos no resumo do 02 (propagados ao 00 e 07).**
- Tabela do 02: C03 "43 gerados" (soma real **39**); C04 "25 usados" (real **24**);
  total "265/194" (real **261/193**); 07 repete "265 s" e diz "média 7,2 s/clip" (real 7,05).
- Impacto: ~1,5% no plano de custo — baixo, mas corrige a base de todos os cálculos.

**P3-9. Relógio interno do filme quebrado no plano final.**
- `03` C07_P03: "first hint of pale morning light" + "distant early tram" — a história
  começa às 3h17 e dura minutos (~3h30 da madrugada); luz matinal é impossível no mundo.
- Impacto: erro sutil de continuidade no plano de fechamento. Recomendação (decisão
  de direção): "deep night blue".

**P3-10. Narração B5 ("café coando") vs prompt C05_P01 ("stirring a pot").**
- Ouvido e olho discordam levemente. Alinhar texto ou visual na revisão.

**P3-11. Prompts das stills ST-02..07 não escritos.**
- `03` escreve integral só a ST-01 e remete as demais aos blocos do `04`. O G1 não é
  turnkey; ~30 min de trabalho completam os 6 prompts.

**P3-12. Plano reserva (C01_P06) sem orçamento de geração.**
- Não entra nas somas (37 pares extraídos). Orçar (6→4 s) ou marcar "fora do custo".

**P3-13. Mapa de áudio (05): B7 inicia em C06_P05, mas o 02 posiciona C06_P05 no B6
(4:04–4:12).** Reflexo do P1-3; resolver junto.

## PARTE 3 — AUDITORIA DO VEDA_AB_RELATORIO (pontos 5–6 da sua ordem)

**Separação evidência × inferência:** ✓ adequada (§10 "Fatos × hipóteses × projeções").
As três camadas exigidas estão distintas e corretamente rotuladas:
1. **Bloqueio do seletor AMD/ROCm = OBSERVADO** (evento `info` do braço B + linha de
   código `shared/attention.py:37` `not torch.version.hip` + `torch.version.hip = "7.15.26333"`
   medido no ambiente + `generated_files=[]`).
2. **Funcionamento do kernel = NÃO TESTADO** (corretamente como hipótese: "com patch de
   disponibilidade, o kernel compilaria no triton 3.7.1 — não verificada").
3. **Ganho de desempenho = NÃO MEDIDO** ("INCONCLUSIVO quanto ao ganho"; projeções
   condicionais explícitas).
**Uma nuance a registrar:** a frase "recusa em vez de fallback silencioso" é uma
**inferência forte** (de success=True + zero arquivos + evento info), não um fato bruto
— sugerimos rotular como inferência na próxima edição. Também é inferência (boa, com
verificação aritmética: 2 âncoras em 339 s = ~170 s) o "passo-âncora ~170 s" do A.

**Comparabilidade do baseline 837 s (ponto 6):** ✓ comparável — cluster histórico
apertado: **T1 846,0 s (fast, wrapper) • P3 836,4 s (strict+preload) • A 837,0 s
(strict, produção)** → dispersão ~1,1% entre condições diferentes do mesmo pipeline.
**Condições que impedem generalizar linearmente para 5 min** (documentadas e corretas):
nº de janelas (21), custo quadrático C(W) medido, áudio a ~11,7 s/s, pico de VRAM
16,05 GB observado na emenda do T3, variância de conteúdo/seed, e amostra única por
configuração. O relatório não extrapola o baseline — correto.

## PARTE 4 — RECOMENDAÇÃO FINAL

**PRECISA DE REVISÃO CRIATIVA (delimitada) antes de avançar ao G1.**

- O **sistema de produção** (prompts, bíblia, gates, alternativas de risco, custos
  rotulados) está sólido e 100% reaproveitável — não é um "refazer".
- Mas o pacote **não** pode passar pelo G1 com: (1) timing que não fecha (+~72 s de
  fala vs 300 s), (2) três contagens contraditórias do mesmo beat, (3) deficit de
  imagem não decidido nos beats de diálogo, e (4) 4–7 gaps de âncora/tag que
  desperdiçariam as gerações mais caras (as de rosto).
- **Caminho mínimo para destravar** (estimado 1–2 h de revisão + 1 decisão sua):
  1. Decisão de direção: aparar B4/B7 (recomendado, ~90–110 palavras) ou re-alvo 5:20–5:30.
  2. Recalcular tabela do 01 + resumo do 02 (script pronto).
  3. Corrigir tags: ST-01 no C01_P02; definir ST-08 (parede sem porta); âncoras de
     identidade nos 4 planos; dicionarar CHAIN/REF.
  4. Escrever os 6 prompts de stills; orçar a reserva; corrigir "morning light" e
     "café coando".
- Alternativa complementar: **sua leitura em voz alta** do roteiro (prevista no 01)
  mede o overflow real antes de qualquer corte — recomendável antes da revisão.

**Nenhuma ação foi executada além de leitura e análise; nenhum arquivo do projeto foi
alterado. Aguardando sua decisão.**
