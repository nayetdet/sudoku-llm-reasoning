import re
import json
import logging
import textwrap
import itertools
import google.generativeai as genai
from typing import Tuple, Dict, Any
from google.generativeai import GenerativeModel
from src.sudoku_llm_reasoning.core.sudoku import Sudoku, SudokuSingle
from src.sudoku_llm_reasoning.core.compare_llm import compare_llm_vs_candidates, save_report
from src.sudoku_llm_reasoning.exceptions.sudoku_reasoner_exceptions import SudokuUnsolvableException, SudokuAlreadySolvedException, SudokuInvalidLLMSolutionException
from src.sudoku_llm_reasoning.mappers.sudoku_mapper import SudokuMapper
from src.sudoku_llm_reasoning.schemas.sudoku_schemas import SudokuLLMSolutionSchema

class SudokuReasoner:
    def __init__(self, llm_model: str, llm_api_key: str) -> None:
        genai.configure(api_key=llm_api_key)
        self.__llm: GenerativeModel = GenerativeModel(model_name=llm_model)

    def analyze(self, sudoku: Sudoku) -> None:
        logging.info(f"Analyzing the following Sudoku: {sudoku}")
        if not sudoku.is_solvable():
            raise SudokuUnsolvableException("The Sudoku is unsolvable; neither the Single Candidate Principle nor the Consensus Principle can be applied")

        if sudoku.is_solved():
            raise SudokuAlreadySolvedException("The Sudoku is already complete and solved")

        llm_solution: SudokuLLMSolutionSchema = self.solve(sudoku)
        try:
            
            report = compare_llm_vs_candidates(sudoku, llm_solution, z3_verify=False)

            
            summary = report.get("summary", {})
            logging.info(f"LLM vs Candidates summary: {summary}")

            
            for ps in report.get("per_step", []):
                if ps.get("missing") or ps.get("extra") or ps.get("single_value_conflict"):
                    logging.warning(
                        "LLM step #%s pos=%s: LLM_candidates=%s | true_candidates=%s | missing=%s | extra=%s | single_conflict=%s",
                        ps.get("step"),
                        ps.get("position"),
                        ps.get("llm_candidates"),
                        ps.get("true_candidates"),
                        ps.get("missing"),
                        ps.get("extra"),
                        ps.get("single_value_conflict"),
                    )
        except Exception as e:
                    
                    logging.exception("Erro ao comparar candidatos LLM vs calculados: %s", e)
            
        if llm_solution.final_grid not in (x.grid for x in sudoku.solutions):
            raise SudokuInvalidLLMSolutionException("The LLM-provided solution is incorrect and does not match any valid Sudoku solution")

        for llm_step in llm_solution.steps:
            naked_singles: Tuple[SudokuSingle, ...] = sudoku.naked_singles
            hidden_singles: Tuple[SudokuSingle, ...] = sudoku.hidden_singles

            logging.info("")
            logging.info(f"Step #{llm_step.step}: inserting '{llm_step.value}' into {tuple(llm_step.position)}")
            logging.info(f"Explanation: {llm_step.explanation}")
            logging.info(f"Candidates (LLM): {list(llm_step.candidates_before)}")
            logging.info(f"Candidates (Z3 - Naked Candidates): {[x.value for x in naked_singles if x.position == llm_step.position]}")
            logging.info(f"Candidates (Z3 - Hidden Candidates): {[x.value for x in hidden_singles if x.position == llm_step.position]}")

            if any(x.value == llm_step.value and x.position == llm_step.position for x in itertools.chain(naked_singles, hidden_singles)):
                logging.info("The step was resolved using the Single Candidate Principle")
            else: logging.info("No candidates found via the Single Candidate Principle (Naked/Hidden Singles); the step relied on the Consensus Principle instead")

            sudoku = sudoku.next_step(*llm_step.position, llm_step.value)
            logging.info(f"Sudoku: {sudoku}")
            if not sudoku.is_solvable():
                raise SudokuInvalidLLMSolutionException("The LLM-provided solution is incorrect; a step made the Sudoku unsolvable")

        logging.info("Analysis completed successfully for the Sudoku")

    def solve(self, sudoku: Sudoku) -> SudokuLLMSolutionSchema:
        logging.info("Generating prompt and sending Sudoku to LLM for solving")
        try:
            text: str = self.__llm.generate_content(textwrap.dedent(
                f"""
                Resolva este Sudoku e DOCUMENTE TODO O PROCESSO.
    
                Sudoku:
                {sudoku}
    
                Regras para sua resposta (obrigatório):
                1. Retorne **apenas JSON válido** — nada fora do JSON.
                2. Use **indexação começando em 0** para linhas e colunas (notação de matriz).
                3. Liste **todas as etapas** na ordem em que foram aplicadas. Cada etapa deve ser um objeto com os campos:
                   - "step": inteiro (1, 2, 3, ...)
                   - "value": inteiro (valor colocado)
                   - "position": [linha, coluna] (indices zero-based)
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
                            "value": 1,
                            "position": [0, 0],
                            "candidates_before": [1],
                            "explanation": "Único candidato restante na célula."
                        }},
                        {{
                            "step": 2,
                            "value": 4,
                            "position": [1, 2],
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
        except Exception as e:
            logging.error("An error occurred while generating content from the LLM")
            raise e

        sanitized_text: str = re.sub(r"(^```json\s*)|(```$)", "", text.strip())
        data: Dict[str, Any] = json.loads(sanitized_text)
        if "error" in data and data.get("error") == "unsolvable":
            raise SudokuUnsolvableException("The LLM reported the Sudoku as unsolvable")

        solution: SudokuLLMSolutionSchema = SudokuMapper.to_llm_solution_schema(data)
        logging.info("LLM response received and processed into Sudoku solution schema")
        return solution
