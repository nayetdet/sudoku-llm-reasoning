import json
import logging
import re
import textwrap
from typing import Dict, Any

import google.generativeai as genai
from google.generativeai import GenerativeModel

from api.mappers.sudoku_mapper import SudokuMapper
from core.schemas.sudoku_schemas import SudokuLLMCandidateSchema, Technique
from core.sudoku import Sudoku

TECH_META: Dict[Technique, Dict[str, Any]] = {
    Technique.NAKED_SINGLES: {
        "label_pt": "Naked Singles",
        "scan_line": "Faça apenas UMA varredura de Naked Singles neste Sudoku.",
        "explanation_hint": "Célula com exatamente 1 candidato possível neste estado.",
        "code": 1,
        "no_results_msg": "No Naked Singles found",
    },
    Technique.HIDDEN_SINGLES: {
        "label_pt": "Hidden Singles",
        "scan_line": "Faça apenas UMA varredura de Hidden Singles neste Sudoku.",
        "explanation_hint": "Valor único restante em uma linha/coluna/bloco.",
        "code": 2,
        "no_results_msg": "No Hidden Singles found",
    },
    Technique.CONSENSUS_PRINCIPLE: {
        "label_pt": "Consensus Principle",
        "scan_line": "Faça apenas UMA varredura usando o Consensus Principle neste Sudoku.",
        "explanation_hint": "Conclusão comum em todos os ramos válidos de análise local.",
        "code": 3,
        "no_results_msg": "No results for Consensus Principle",
    },
}

class SudokuReasoner:
    def __init__(self, llm_model: str, llm_api_key: str) -> None:
        genai.configure(api_key=llm_api_key)
        self.__llm: GenerativeModel = GenerativeModel(llm_model)

    def solve_naked_singles(self, sudoku: Sudoku) -> SudokuLLMCandidateSchema:
        return self.__solve_by_technique(sudoku, Technique.NAKED_SINGLES)

    def solve_hidden_singles(self, sudoku: Sudoku) -> SudokuLLMCandidateSchema:
        return self.__solve_by_technique(sudoku, Technique.HIDDEN_SINGLES)

    def solve_consensus_principle(self, sudoku: Sudoku) -> SudokuLLMCandidateSchema:
        return self.__solve_by_technique(sudoku, Technique.CONSENSUS_PRINCIPLE)

    def __solve_by_technique(self, sudoku: Sudoku, technique: Technique) -> SudokuLLMCandidateSchema:
        logging.info(f"Generating prompt and sending Sudoku to LLM for ONE-PASS {technique.name} scan")
        try:
            prompt = self._build_prompt_for(sudoku, technique)
            resp = self.__llm.generate_content(prompt)
            text = resp.text or ""
        except Exception as e:
            logging.error("An error occurred while generating content from the LLM", exc_info=True)
            raise e

        data: Dict[str, Any] = self._sanitize_and_parse_json(text)
        result: SudokuLLMCandidateSchema = SudokuMapper.to_llm_candidates_schema(data)

        logging.info(f"LLM response received and processed into {technique.name} ONE-PASS schema")
        return result

    @staticmethod
    def _build_prompt_for(sudoku: Sudoku, technique: Technique) -> str:
        meta = TECH_META[technique]

        common_rules = f"""
                {meta["scan_line"]} NÃO aplique nenhuma jogada.
                Identifique APENAS uma ocorrência (se existir) de {meta["label_pt"]} no estado atual.

                Sudoku (0 = vazio):
                {sudoku}

                REGRAS GERAIS (OBRIGATÓRIO):
                1) Retorne SOMENTE JSON válido (sem cercas de código).
                2) Indexação zero-based: "position" = [linha, coluna].
                3) Se existirem VÁRIAS ocorrências agora, escolha APENAS UMA seguindo esta ordem:
                   a) menor linha; b) em empate, menor coluna (ordem de leitura).
                4) O JSON DEVE ter EXATAMENTE estes 4 campos no nível raiz:
                   - "position": [i, j]                // ambos inteiros
                   - "value": inteiro                  // valor confirmado (1..9)
                   - "explanation": string             // ver FORMATO DA EXPLANATION abaixo
                   - "type": {meta["code"]}            // inteiro exato: {meta["code"]}
                5) NÃO inclua quaisquer outros campos (ex.: "index", "candidates", "technique", "notes", etc.).
                6) NÃO aplique jogadas, NÃO altere a grade, NÃO invente dados ausentes.
                7) Se não houver resultados nesta varredura, retorne exatamente:
                   {{"error": "{meta["no_results_msg"]}"}}
                8) A explanation DEVE ser multilinha, pronta para log, contendo um “mini-relatório” que:
                   - mostre conjuntos usados na dedução (linha, coluna, bloco) e o conjunto de candidatos;
                   - justifique por que este caso corresponde a {meta["label_pt"]};
                   - inclua um “recorte” em matriz (3x3 ou a linha/coluna/unidade pertinente) para apoiar a prova.
                9) Proibido usar terminologia incorreta da técnica (ex.: chamar Hidden de Naked ou vice-versa).
               10) NÃO use probabilidades, palpites ou linguagem condicional (“talvez”, “pode ser”).
            """.strip()

        if technique == Technique.NAKED_SINGLES:
            extra = """
                REGRAS ESPECÍFICAS — NAKED SINGLES:
                • Comprove que a célula [i,j] tem CANDIDATOS = {1..9} \\ (usados_na_linha ∪ usados_na_coluna ∪ usados_no_bloco)
                  e que o resultado tem cardinalidade 1 (apenas o "value").
                • Na explanation inclua, em linhas separadas:
                  - LINHA i: {…}    COLUNA j: {…}    BLOCO (b_i,b_j): {…}
                  - Candidatos([i,j]) = {1..9} \\ (L ∪ C ∪ B) = {k}
                  - Mini-matriz do bloco 3x3 contendo [i,j] OU a linha i e coluna j como matrizes de 9 valores/zeros.
                • O foco é a restrição LOCAL da célula (nenhuma análise por “único na unidade” aqui).

                EXEMPLO DE EXPLANATION (apenas formato; NÃO replique números do exemplo):
                \"\"\" 
                Naked Single em [0,5]:
                LINHA 0 = {1,3,4,5,6,8,9} | COLUNA 5 = {1,2,3,4,5,8,9} | BLOCO (0,2) = {1,2,3,4,5,6,8,9}
                Candidatos([0,5]) = {{1..9}} \\ (L∪C∪B) = {{7}}
                Bloco (0,2):
                [ a b c
                  d e f
                  g h i ]  // preencha com dígitos conhecidos ou 0 para vazios
                Conclusão: único candidato restante é 7, caracterizando Naked Single.
                \"\"\"
                """.strip()
        elif technique == Technique.HIDDEN_SINGLES:
            extra = """
                REGRAS ESPECÍFICAS — HIDDEN SINGLES:
                • Mostre que o "value" aparece como candidato em EXATAMENTE UMA célula dentro de UMA unidade (escolha UMA: linha i OU coluna j OU bloco 3x3).
                • NÃO basta a célula ter 1 candidato; o “único” é relativo à UNIDADE:
                  - Liste as células da unidade escolhida e os candidatos (somente para o dígito “value”).
                  - Comprove contagem: ocorrências_do_value_na_unidade = 1.
                • Na explanation inclua:
                  - Unidade usada (ex.: LINHA 4) e mapeamento {pos -> candidatos_contendo_value}
                  - Mini-matriz da unidade (linha como 1×9, coluna como 9×1 ou bloco 3×3).
                  - Breve frase: “{value} só pode ir em [i,j] dentro da {unidade}, logo Hidden Single”.

                EXEMPLO DE EXPLANATION (apenas formato):
                \"\"\"
                Hidden Single do dígito 9 na LINHA 1:
                Células com 9 como candidato na LINHA 1: {[1,2], [1,5]} -> checagem mostra que [1,2] é inválido (9 já no bloco), restando apenas [1,5]
                Mini-linha 1:
                [ d1 d2 d3 d4 d5 d6 d7 d8 d9 ]  // conhecidas ou 0
                Conclusão: 9 só pode ir em [1,5] na LINHA 1 -> Hidden Single.
                \"\"\"
                """.strip()
        else:
            extra = """
                REGRAS ESPECÍFICAS — CONSENSUS PRINCIPLE (profundidade 1):
                • Use análise por casos LOCAIS (no máx. 3 ramos) com informação virtual: escolha um conjunto pequeno de alternativas mutuamente exclusivas
                  (ex.: duas posições possíveis de um dígito numa unidade OU presença/ausência de um candidato numa célula).
                • Para cada ramo:
                  - indique a suposição (“Se [r] = v…” ou “Se o dígito d ficar em X…”);
                  - aplique apenas deduções rasas (Naked/Hidden/cobrança direta de restrição) para chegar a uma MESMA conclusão sobre [i,j] = value,
                    OU descarte o ramo por contradição explícita (explique a quebra da regra).
                • Mostre o CONSENSO: todos os ramos válidos implicam o mesmo valor para [i,j].
                • Na explanation inclua:
                  - Resumo dos ramos (Ramo A, Ramo B, …), mini-matrizes/unidades envolvidas e a conclusão comum.
                  - Limite-se a profundidade 1 (sem aninhar casos dentro de casos).

                EXEMPLO DE EXPLANATION (apenas formato):
                \"\"\" 
                Consensus em [1,7] = 4:
                Ramo A) suponha 1 em [4,4] -> deduções locais forçam [1,7]=4.
                Ramo B) suponha 1 em [4,6] -> deduções locais forçam [1,7]=4.
                Ramo C) suponha 1 em [4,7] -> deduções locais forçam [1,7]=4.
                Conclusão comum: todos os ramos válidos concordam que [1,7]=4 -> Consensus Principle (prof. 1).
                \"\"\"
                """.strip()

        format_block = f"""
                FORMATO DE SAÍDA (EXEMPLO ESTRUTURAL):
                {{
                  "position": [3, 5],
                  "value": 9,
                  "explanation": "{meta["explanation_hint"]} — veja mini-relatório acima.",
                  "type": {meta["code"]}
                }}
            """.strip()

        prompt = textwrap.dedent(f"""
                {common_rules}

                {extra}

                {format_block}
            """).strip()

        return prompt

    @staticmethod
    def _sanitize_and_parse_json(text: str) -> Dict[str, Any]:
        if not text:
            raise ValueError("Empty response from LLM")

        sanitized_text = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            text.strip(),
            flags=re.IGNORECASE
        )

        try:
            return json.loads(sanitized_text)
        except json.JSONDecodeError as e:
            logging.error("Failed to parse LLM JSON response", exc_info=True)
            logging.debug("Raw LLM text: %s", text)
            raise ValueError(f"Invalid JSON from LLM: {e}") from e
