from typing import List, Dict, Tuple, Set

Grid = List[List[int]]  

def compute_candidates(grid: Grid) -> Dict[Tuple[int,int], Set[int]]:
    """
    Retorna um dict com chave (r,c) para cada célula vazia e valor: conjunto de candidatos {1..9}.
    """
    n = 9
    all_vals = set(range(1, n+1))
    candidates = {}
    for r in range(n):
        for c in range(n):
            if grid[r][c] != 0:
                continue
            
            row_used = set(grid[r][j] for j in range(n) if grid[r][j] != 0)
            col_used = set(grid[i][c] for i in range(n) if grid[i][c] != 0)
            
            br, bc = (r // 3) * 3, (c // 3) * 3
            block_used = set(
                grid[i][j]
                for i in range(br, br+3)
                for j in range(bc, bc+3)
                if grid[i][j] != 0
            )
            used = row_used | col_used | block_used
            cand = all_vals - used
            candidates[(r,c)] = cand
    return candidates

def pretty_candidates(cands: Dict[Tuple[int,int], Set[int]]) -> str:
    lines = []
    for (r,c), s in sorted(cands.items()):
        lines.append(f"({r},{c}): {sorted(s)}")
    return "\n".join(lines)

def compare_with_llm(cands: Dict[Tuple[int,int], Set[int]], llm_output: Dict[str, List[int]]):
    """
    Compara candidatos (cands) com a resposta da LLM.
    llm_output: dicionário onde chave é "r,c" string (ex: "0,1") ou tuple mas
                é mais comum receber string; valor é lista de candidatos sugeridos
                ou lista vazia se LLM votou por um único número (p.ex. [5]).
    Retorna um relatório (dict) com:
      - matches: células onde conjuntos são iguais
      - missing: candidatos que LLM deixou de fora (cands - llm)
      - extra: candidatos que LLM sugeriu mas que não são possíveis (llm - cands)
      - llm_single_value_conflicts: se LLM deu valor único que não é candidato
    """
    matches = []
    missing = {}
    extra = {}
    single_conflicts = {}

    for (r,c), true_set in cands.items():
        key = f"{r},{c}"
        llm_set = set(llm_output.get(key, []))
        if llm_set == true_set:
            matches.append(key)
        else:
            miss = true_set - llm_set
            ext = llm_set - true_set
            if miss:
                missing[key] = sorted(miss)
            if ext:
                extra[key] = sorted(ext)
        
        if len(llm_output.get(key, [])) == 1:
            val = llm_output[key][0]
            if val not in true_set:
                single_conflicts[key] = val

    return {
        "matches": matches,
        "missing": missing,
        "extra": extra,
        "single_value_conflicts": single_conflicts,
    }

if __name__ == "__main__":
    sample = [
        [5,3,0,0,7,0,0,0,0],
        [6,0,0,1,9,5,0,0,0],
        [0,9,8,0,0,0,0,6,0],
        [8,0,0,0,6,0,0,0,3],
        [4,0,0,8,0,3,0,0,1],
        [7,0,0,0,2,0,0,0,6],
        [0,6,0,0,0,0,2,8,0],
        [0,0,0,4,1,9,0,0,5],
        [0,0,0,0,8,0,0,7,9],
    ]
    c = compute_candidates(sample)
    print(pretty_candidates(c))
   
    llm_fake = { f"{r},{c}": list(vals) for (r,c), vals in c.items() }
    report = compare_with_llm(c, llm_fake)
    print(report)
