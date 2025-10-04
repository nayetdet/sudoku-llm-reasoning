import json
import textwrap
from src.sudoku_llm_reasoning.deps.llm_instance import LLMInstance
from src.sudoku_llm_reasoning.mappers.sudoku_mapper import SudokuMapper
from src.sudoku_llm_reasoning.models.sudoku import Sudoku
from src.sudoku_llm_reasoning.schemas.sudoku_schemas import LLMSudokuSolutionSchema

class LLMService:
    @classmethod
    def solve_sudoku(cls, sudoku: Sudoku) -> LLMSudokuSolutionSchema:
        text: str = LLMInstance.get_llm().generate_content(textwrap.dedent(
            f"""
            Resolva este Sudoku e DOCUMENTE TODO O PROCESSO.
            
            Sudoku:
            {sudoku}
            
            Regras para sua resposta (obrigatório):
            1. Retorne **apenas JSON válido** — nada fora do JSON.
            2. Use **indexação começando em 0** para linhas e colunas (notação de matriz).
            3. Liste **todas as etapas** na ordem em que foram aplicadas. Cada etapa deve ser um objeto com os campos:
               - "step": inteiro (1, 2, 3, ...)
               - "cell": [linha, coluna] (indices zero-based)
               - "value": inteiro (valor colocado)
               - "candidates_before": lista de inteiros — candidatos válidos para a célula imediatamente antes de preenchê-la
               - "explanation": string curta (uma frase, justificativa concisa do porquê essa jogada foi legal com a técnica indicada)
            4. Cada célula preenchida deve gerar UMA etapa. Se várias células foram preenchidas "simultaneamente" por terem cada uma um único candidato, registre cada uma como etapas separadas na sequência que você aplicar.
            5. Após a lista de etapas, inclua os campos finais:
               - "final_grid": matriz completa (lista de listas) com o Sudoku resolvido (ou parcial, se não for resolvível)
               - "unique_solution": true/false (se você puder afirmar unicidade)
            6. Se o puzzle for **insolúvel**, retorne um JSON com `{{"error": "unsolvable"}}`.
            7. EXPLICAÇÕES devem ser concisas e factuais — **não** escreva seu raciocínio interno longo (nada tipo "estou pensando..."). Frases do tipo “A célula (0,2) só pode ser 3 porque {{razões}}” são perfeitas.
            8. NÃO inclua marcações de código (como ``` ou ```json) — retorne apenas JSON puro.
            
            Formato de saída esperado (exemplo mínimo):
            {{
                "steps": [
                    {{
                        "step": 1,
                        "cell": [0, 0],
                        "value": 1,
                        "candidates_before": [1],
                        "explanation": "Único candidato restante na célula."
                    }},
                    {{
                        "step": 2,
                        "cell": [1, 2],
                        "value": 4,
                        "candidates_before": [2, 4],
                        "explanation": "O número 4 só pode ir nesta posição da linha 1."
                    }}
              ],
              "final_grid": [[1, 2, 3, 4], [3, 4, 2, 1], [2, 1, 4, 3], [4, 3, 1, 2]],
              "unique_solution": true
            }}
            
            Termine a resposta estritamente com esse JSON — sem textos adicionais.
            """
        ).strip()).text
        return SudokuMapper.to_llm_solution_schema(json.loads(text))
