import json
import logging
from typing import Dict, List, Set, Tuple, Any

from z3 import Int, Distinct, And, Or, Solver, sat

from src.sudoku_llm_reasoning.core.sudoku import Sudoku
from src.sudoku_llm_reasoning.schemas.sudoku_schemas import SudokuLLMSolutionSchema

def build_naked_candidates_map(sudoku: Sudoku) -> Dict[str, Set[int]]:
    """
    Retorna um dicionário "r,c" -> set(candidatos) usando sudoku.naked_candidates.
    (usa indexação 0-based como no restante do projeto)
    """
    n = len(sudoku)
    res: Dict[str, Set[int]] = {}
    for i in range(n):
        for j in range(n):
            if sudoku.grid[i][j] == 0:
                res[f"{i},{j}"] = set(sudoku.naked_candidates(i, j))
    return res

def is_candidate_globally_possible_with_z3(grid: Tuple[Tuple[int, ...], ...], r: int, c: int, v: int) -> bool:
    """
    Checa (lentamente) se existe uma solução completa do Sudoku com a restrição (r,c) == v.
    Usa Z3, cria modelo novo a partir do grid atual.
    """
    n = len(grid)
    n_isqrt = int(n**0.5)
    # variáveis
    X = [[Int(f"x_{i}_{j}") for j in range(n)] for i in range(n)]
    s = Solver()
    # domínio 1..n
    for i in range(n):
        for j in range(n):
            s.add(And(X[i][j] >= 1, X[i][j] <= n))
    # linhas
    for i in range(n):
        s.add(Distinct([X[i][j] for j in range(n)]))
    # colunas
    for j in range(n):
        s.add(Distinct([X[i][j] for i in range(n)]))
    # subgrids
    for bi in range(0, n, n_isqrt):
        for bj in range(0, n, n_isqrt):
            block = [X[ii][jj] for ii in range(bi, bi + n_isqrt) for jj in range(bj, bj + n_isqrt)]
            s.add(Distinct(block))
    # células pré-preenchidas
    for i in range(n):
        for j in range(n):
            if grid[i][j] != 0:
                s.add(X[i][j] == grid[i][j])
    # força (r,c) == v
    s.add(X[r][c] == v)
    return s.check() == sat

def compare_llm_vs_candidates(
    sudoku: Sudoku,
    llm_solution: SudokuLLMSolutionSchema,
    z3_verify: bool = False
) -> Dict[str, Any]:
    """
    Compara candidatos calculados com os candidatos que a LLM informou em cada passo.
    Retorna um relatório com:
      - per_step: lista com análise por etapa
      - summary: estatísticas (matches, missing_count, extra_count, conflicts_count)
    Parâmetro z3_verify: se True, para cada candidato faz checagem Z3 (lentíssimo para muitos candidatos).
    """
    logging.info("Construindo mapa de candidatos (naked) via Sudoku.naked_candidates()")
    true_candidates_map = build_naked_candidates_map(sudoku)
    per_step = []
    matches = 0
    missing_count = 0
    extra_count = 0
    conflicts_count = 0

    for step in llm_solution.steps:
        pos = tuple(step.position)  # [i, j]
        key = f"{pos[0]},{pos[1]}"
        llm_cands = set(step.candidates_before or [])
        true_cands = true_candidates_map.get(key, set())

        
        z3_invalid = []
        if z3_verify and true_cands:
            refined = set()
            grid = sudoku.grid
            for v in sorted(true_cands):
                ok = is_candidate_globally_possible_with_z3(grid, pos[0], pos[1], v)
                if ok:
                    refined.add(v)
                else:
                    z3_invalid.append(v)
            true_cands = refined

        miss = sorted(list(true_cands - llm_cands))
        extra = sorted(list(llm_cands - true_cands))
        single_conflict = None
        if len(step.candidates_before or []) == 1:
            val = (step.candidates_before or [None])[0]
            if val not in true_cands:
                single_conflict = val

        per_step.append({
            "step": step.step,
            "position": pos,
            "llm_candidates": sorted(list(llm_cands)),
            "true_candidates": sorted(list(true_cands)),
            "missing": miss,
            "extra": extra,
            "single_value_conflict": single_conflict,
            "z3_invalid_filtered_out": z3_invalid if z3_verify else []
        })

        if not miss and not extra:
            matches += 1
        missing_count += len(miss)
        extra_count += len(extra)
        if single_conflict is not None:
            conflicts_count += 1

    summary = {
        "total_steps": len(llm_solution.steps),
        "exact_matches": matches,
        "missing_total": missing_count,
        "extra_total": extra_count,
        "single_value_conflicts": conflicts_count,
    }

    report = {
        "per_step": per_step,
        "summary": summary
    }

    return report

def save_report(report: Dict[str, Any], path: str = "llm_candidates_report.json") -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logging.info(f"Relatório salvo em {path}")
