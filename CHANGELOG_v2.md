# v2.0 — correção do gerador (humor)

## O que mudou no prompt (`fazedor_app/fazedor_app.py`)
- `instrucoes_dossie()` foi reescrita: prompt único autossuficiente de ~9.000 chars.
- REMOVIDO: duas "LEIS DE FERRO" contraditórias (a primeira proibia som de boca, a segunda
  autorizava "hm"/estalo de língua) — a IA recebia as duas ao mesmo tempo.
- REMOVIDO: as âncoras visuais (~3.500 chars) do prompt de sistema. Agora o programa cola
  estilo/set/âncoras/negativos no prompt final (`prompt_dossie`), e a IA escreve só a ação.
- ADICIONADO: bíblia de personagem com voz do corpo, gestos-frase contados e divisão do erro.
- ADICIONADO: motor de comédia (setup → expectativa → subversão → reação subcontrolada) e
  cardápio de 8 gags físicas.
- ADICIONADO: regra "todo clipe tem piada física com objeto que se move" + lista de verbos
  proibidos (mede, confere, aprova, calcula) e lista de danos invisíveis banidos
  (curto-circuito, pane, falha interna, colapso de infraestrutura).
- ADICIONADO: calibragem de 300 s / 60 s / 30 s com estrutura própria para cada duração.
- ADICIONADO: método em duas passadas (espinha em 10 linhas antes do JSON).
- ADICIONADO: exemplo certo × errado com a mesma premissa.
- ADICIONADO: autochecagem de 8 itens antes de entregar.

## O que mudou no validador
- `validar_dossie()` agora aceita 30, 6 e 3 clipes, com a estrutura de cada um.
- Novos erros: clipe sem campo `gag`; clipe sem piada física (só processo); dano invisível;
  clímax fora de quadro; gesto-assinatura repetido mais de 3×.
- Novo campo no JSON: `gag` e `objeto_gag` por clipe.
- Retorna `humor`: nota de 0 a 10 com os motivos.
- `prompt_dossie()` não duplica mais âncora: detecta action completo e respeita.

## Compatibilidade
- Episódios antigos (action completo, 30 clipes) continuam válidos: `_action_ja_completa()`
  pula a colagem e mantém 2.000–4.500 chars.
- Nomes de arquivo, pastas e interface não mudaram: basta substituir a pasta.
