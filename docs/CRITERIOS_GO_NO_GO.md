## Critérios Go/No-Go — Triagem Multiobjetivo

Objetivo: formalizar decisão de priorização integrando afinidade, seletividade e propriedades para mobilidade xilemática e síntese.

### Métricas-Chave
- Afinidade (`ΔG`, kcal/mol): mais negativo é melhor. Fonte: AutoDock Vina (melhor modo).
- Seletividade (`ΔΔG`, kcal/mol): ΔG(alvo) − ΔG(referência). Referência: alvo homólogo não desejado.
- Mobilidade xilemática (`XyMove`): índice heurístico baseado em logD(pH 5–6), TPSA, MW, pKa/carga, HBD/HBA.
- Sintetizabilidade (`SA`): escore 1–10 (menor é melhor) e contagem de passos (estimativa).
- Alertas: PAINS/indesejáveis, reatividade, flags toxicológicas iniciais.

### Limiares Sugeridos (ajustar conforme dados)
- `ΔG ≤ -7.0` (piloto); `≤ -8.0` (prioritário)
- `ΔΔG ≤ -1.0` contra referência (melhor que ref. por ≥1 kcal/mol)
- `XyMove ≥ 0.6` (escala 0–1)
- `SA ≤ 6.0`; sem alertas críticos

### Esquema de Pontuação (exemplo)
```yaml
weights:
  affinity: 0.35
  selectivity: 0.20
  xymove: 0.25
  synthesizability: 0.10
  alerts: 0.10
constraints:
  min_affinity_kcal_per_mol: -7.0
  min_ddg_kcal_per_mol: -1.0
  min_xymove: 0.6
  max_sa: 6.0
penalties:
  pains: 1.0
  reactive_flags: 1.0
```

### Decisão
- Go: cumpre constraints e score total ≥ 0.70
- Consider: cumpre constraints principais e score 0.55–0.70 (revisão)
- No-Go: viola constraints críticos ou score < 0.55

Obs.: parâmetros devem ser recalibrados após o primeiro lote de docking e análise de sensibilidade.
