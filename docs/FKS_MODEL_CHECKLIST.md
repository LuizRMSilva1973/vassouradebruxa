## Checklist — Gerar/Obter `targets/FKS.pdb`

Meta: obter um modelo coerente para a β‑1,3‑glucano‑sintase (FKS) de C. theobromae para uso em docking exploratório.

### 1) Sequência
- [ ] Extrair a sequência de FKS (proteoma de C. theobromae), anotando ID, comprimento e domínios (FKS1‑like).
- [ ] Verificar topologia multipasse (helices TM) e motivos conservados.

### 2) Modelagem
- Opção A (predição estrutural): usar um preditor de estrutura (e.g., método moderno de predição) para gerar o monômero.
- Opção B (homologia): alinhar contra FKS de fungos basidiomicetos com estruturas ou modelos públicos; construir o modelo por homologia.
- [ ] Validar qualidade (métrica de confiança, cobertura de laços catalíticos).

### 3) Orientação em Membrana
- [ ] Posicionar em bicamada (orientação) com base em predição de TM e topologia.
- [ ] Exportar em PDB único (sem águas/íons supérfluos) para docking.

### 4) Sítio de Ligação / Caixa
- [ ] Identificar cavidade de ligação putativa (com base em motivos e alinhamento com FKS alvo de echinocandinas).
- [ ] Ajustar `targets/FKS.box` (center_*, size_*) — ver `docs/BOX_TUNING.md`.

### 5) Sanidade para Docking
- [ ] Checar protonação básica, remoção de moléculas pequenas indesejadas.
- [ ] Salvar `targets/FKS.pdb` e executar o pipeline com 2 ligantes piloto.

Notas: manter a abordagem conceitual e usar apenas dados públicos/permitidos. Este checklist é para uso computacional e não envolve ensaios laboratoriais.

