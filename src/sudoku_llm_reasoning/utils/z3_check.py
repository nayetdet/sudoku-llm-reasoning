from z3 import Int, And, Distinct, Solver, sat

def is_candidate_globally_possible(grid, r, c, v) -> bool:
    
    X = [[Int(f"x_{i}_{j}") for j in range(9)] for i in range(9)]
    s = Solver()
   
    for i in range(9):
        for j in range(9):
            s.add(X[i][j] >= 1, X[i][j] <= 9)
    
    for i in range(9):
        s.add(Distinct([X[i][j] for j in range(9)]))
    for j in range(9):
        s.add(Distinct([X[i][j] for i in range(9)]))
    for bi in range(3):
        for bj in range(3):
            block = [X[i][j] for i in range(bi*3, bi*3+3) for j in range(bj*3, bj*3+3)]
            s.add(Distinct(block))
   
    for i in range(9):
        for j in range(9):
            if grid[i][j] != 0:
                s.add(X[i][j] == grid[i][j])
   
    s.add(X[r][c] == v)
    return s.check() == sat
