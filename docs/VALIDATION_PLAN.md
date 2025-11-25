# Plano de Validação — Vassoura‑de‑Bruxa (C. theobromae)

Objetivo: levar candidatos identificados in silico até evidência experimental (in vitro → estacas/tecido → casa de vegetação → campo piloto), de forma reprodutível e regulatória.

## 1) Triagem in silico (este repositório)
- Alvos: CHS, FKS (prioritários), depois AGS/GEL/CDA.
- Docking: AutoDock Vina (parâmetros reprodutíveis; caixas versionadas).
- Seleção: ΔG, ΔΔG (vs alvo de referência), XyMove, Pareto e shortlist.
- Saídas: `docking_results/` (CSV, gráficos, shortlist, Pareto).

## 2) Preparação de compostos
- Aquisição: catálogo (analíticos) ou síntese sob demanda (rotas simples primeiro).
- Controle positivo: quitosana/nanoquitosana; negativos: solvente/veículo.
- Qualidade: pureza por HPLC/LC‑MS; estabilidade em solvente/estoque.

## 3) Ensaios in vitro (mínimo)
- Crescimento micelial (C. theobromae): MIC por microdiluição (96‑well), gradiente 0.25× a 8× do alvo.
- Germinação de esporos/hifas: avaliação microscópica com CFU/hifa.
- Pareamento com quitosana: curva de dose‑resposta comparativa.
- Métricas: MIC50/MIC90, CI (synergy) se combinação.

## 4) Ensaios em tecido/estacas (ex vivo)
- Estacas de mandioca inoculadas; aplicação de candidato por via xilemática (injeção ou imersão).
- Leitura: carga fúngica (qPCR), sintomas visuais, fitotoxicidade.

## 5) Casa de vegetação (in vivo)
- Delineamento: randomizado com replicações (n≥6 por tratamento).
- Tratamentos: 2–3 doses/candidato + controles; frequência de aplicação definida por meia‑vida observada.
- Métricas: severidade, incidência, vigor da planta, carga por qPCR.

## 6) Formulação e aplicação
- Solventes/co‑solventes compatíveis (pH, tensão superficial); adesivantes e penetrantes.
- Ensaios de compatibilidade e estabilidade (temperatura/luz).

## 7) Segurança e registros
- Avaliar alertas (PAINS/reatividade) e perfis toxicológicos preliminares.
- Regulatório: mapear exigências locais para testes em campo piloto.

## 8) Decisão Go/No‑Go
- Critérios em `docs/CRITERIOS_GO_NO_GO.md` + `config/scoring.yaml` calibrado.
- Dossiê de candidatos: pose, ΔG/ΔΔG, XyMove, MIC, notas de formulação e custo.

