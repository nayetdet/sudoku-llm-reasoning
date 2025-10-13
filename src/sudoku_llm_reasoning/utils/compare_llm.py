import logging
from typing import Dict, Set, Tuple
from src.sudoku_llm_reasoning.core.sudoku import Sudoku
from src.sudoku_llm_reasoning.schemas.sudoku_schemas import SudokuLLMSolutionSchema


def build_candidates_map(sudoku: Sudoku) -> Dict[Tuple[int, int], Set[int]]:
    """Cria um mapa (i,j) -> {candidatos possíveis}"""
    n = len(sudoku.grid)
    candidates = {}
    for i in range(n):
        for j in range(n):
            if sudoku.grid[i][j] == 0:
                candidates[(i, j)] = set(sudoku.naked_candidates(i, j))
    return candidates


def compare_llm_candidates(sudoku: Sudoku, llm_solution: SudokuLLMSolutionSchema):
    """
    Compara os candidatos calculados com os candidatos que a LLM disse ter
    antes de preencher cada célula.
    """
    real_cands = build_candidates_map(sudoku)

    logging.info("Comparando candidatos da LLM com os reais...")
    total_steps = len(llm_solution.steps)
    matches = 0
    errors = 0

    for step in llm_solution.steps:
        i, j = step.position
        llm_cands = set(step.candidates_before or [])
        true_cands = real_cands.get((i, j), set())

        if llm_cands == true_cands:
            matches += 1
        else:
            errors += 1
            missing = true_cands - llm_cands
            extra = llm_cands - true_cands
            logging.warning(
                f"Célula ({i},{j}): "
                f"LLM disse {sorted(llm_cands)}, "
                f"mas verdadeiros são {sorted(true_cands)}. "
                f"Faltando: {sorted(missing)}, Extras: {sorted(extra)}"
            )

    logging.info(
        f"Comparação finalizada: {matches}/{total_steps} passos corretos, {errors} incorretos."
    )
