# PACOTE COMPLETO V6 — arquivos íntegros
Commit de referência: `88a903a` (main).
Os arquivos abaixo são cópias **byte a byte** dos originais, sem alteração.

| Arquivo no pacote | Origem | Bytes | SHA-256 |
|---|---|---:|---|
| `fazedor_app.py` | `fazedor_app/fazedor_app.py` | 69420 | `deecc6042f3ef3ecfc6724662449dda17e334d9f456657c88ed457a41564dda3` |
| `regras_v4.py` | `fazedor_app/regras_v4.py` | 30451 | `8d269b60bdc59e266fc75e668eb49aa128dbbda98c789845bd48a55d055c9c92` |
| `regras_v6.py` | `fazedor_app/regras_v6.py` | 27939 | `644bbdb8da83ec82ee01a783fdb9c8861cab1423ef1dd846ebaabdd299e36d5d` |
| `qc_visao.py` | `pipeline/qc_visao.py` | 33656 | `b0c0532d27860d7140af944b944bb0bc778ce591e8abdfa6a7ed35777006d921` |
| `PROMPT_SISTEMA_v6.txt` | `PROMPT_SISTEMA_v6.txt` | 26707 | `2533eb089147ebe9d025b48e664ecb5f673f7181ad2e50a04c13ecf5c62d49e5` |
| `auditor_v6.py` | `fazedor_app/auditor_v6.py` | 8310 | `1e110f1c413e9e0d9b518922e384290da340abda84ab2f957223748b18d36002` |

## Observações
- `fazedor_app.py`: sistema, extrator, `SOM_NOMEADO`, `VERBOS_GAG`, `validar_dossie()`, `agentrouter_responses()` com `sistema` explícito.
- `regras_v4.py`: `montar_prompt_v4()` (contrato H3) e `validar_montagem()`.
- `regras_v6.py`: `PROMPT_MESTRE_V6` — PARTE 10 linha 447, PARTE 13 linha 549, PARTE 14 linha 655.
- `qc_visao.py`: gate de visão (terceira camada) e modelos AgentRouter.
- `PROMPT_SISTEMA_v6.txt`: cópia canônica do prompt, byte-igual ao módulo.
- `auditor_v6.py`: prompt do auditor e `mensagem_usuario()`.
