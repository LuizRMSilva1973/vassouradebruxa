## Contribuindo

Obrigado por contribuir! Siga estas orientações rápidas:

- Abra uma issue descrevendo o objetivo antes de um PR significativo.
- Use branches descritivas (ex.: `feat/…`, `fix/…`, `docs/…`, `chore/…`).
- Siga o estilo dos scripts existentes; mantenha mudanças focadas.
- Evite commitar arquivos grandes/resultados (veja `.gitignore`).

### Fluxo sugerido
1. Fork/branch a partir de `main`.
2. Implementa e testa localmente: `./run_docking.sh` e `python3 topn_by_target.py`.
3. Atualize docs se necessário (`README.md`, `QUICKSTART.md`).
4. Abra PR vinculando à issue e descrevendo mudanças/impacto.

### Qualidade
- Shell: prefira `bash`, `set -euo pipefail`, mensagens claras.
- Python: use `argparse`, mensagens de erro úteis e CSVs consistentes.

