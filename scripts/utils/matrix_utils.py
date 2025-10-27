import random
from typing import List, Tuple

class MatrixUtils:
    @classmethod
    def get_empty_matrix(cls, n: int) -> List[List[int]]:
        return [[0 for _ in range(n)] for _ in range(n)]

    @classmethod
    def get_random_position(cls, n: int) -> Tuple[int, int]:
        return random.randint(0, n - 1), random.randint(0, n - 1)
