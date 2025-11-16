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
        "explanation_hint": (
            "Mostre, passo a passo, os ramos de suposição (casos) e como TODOS os ramos "
            "válidos convergem para o mesmo valor na célula alvo, no estilo de relatório "
            "detalhado do exemplo de Sudoku 4×4 abaixo."
        ),
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

        data: Dict[str, Any] = self._sanitize_and_parse_json(text, technique)
        result: SudokuLLMCandidateSchema = SudokuMapper.to_llm_candidates_schema(data)

        logging.info(f"LLM response received and processed into {technique.name} ONE-PASS schema")
        return result

    @staticmethod
    def _build_prompt_for(sudoku: Sudoku, technique: Technique) -> str:
        meta = TECH_META[technique]

        common_rules = f"""
            {meta["scan_line"]} NÃO aplique nenhuma jogada de fato na grade real.
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
               - "value": inteiro                  // valor confirmado
               - "explanation": string             // ver FORMATO DA EXPLANATION abaixo
               - "type": {meta["code"]}            // inteiro exato: {meta["code"]}
            5) NÃO inclua quaisquer outros campos (ex.: "index", "candidates", "technique", "notes", etc.).
            6) NÃO aplique jogadas na grade real, NÃO altere a grade fornecida e NÃO invente dados ausentes.
            7) Se não houver resultados nesta varredura, retorne exatamente:
               {{"error": "{meta["no_results_msg"]}"}}
            8) A explanation DEVE ser multilinha, pronta para log, contendo um “mini-relatório” que:
               - mostre conjuntos usados na dedução (linha, coluna, bloco) e o conjunto de candidatos;
               - justifique por que este caso corresponde a {meta["label_pt"]};
               - inclua um “recorte” em matriz (linha/coluna/bloco/unidade) para apoiar a prova.
            9) Proibido usar terminologia incorreta da técnica (ex.: chamar Hidden de Naked ou vice-versa).
           10) NÃO use probabilidades, palpites ou linguagem condicional (“talvez”, “pode ser”).

           ATENÇÃO ESPECIAL:
           • O campo "type" É OBRIGATÓRIO e DEVE ser exatamente {meta["code"]}.
           • Responda com UM ÚNICO objeto JSON, sem comentários, sem texto extra.
        """.strip()

        if technique == Technique.NAKED_SINGLES:
            extra = """
                REGRAS ESPECÍFICAS — NAKED SINGLES:
                • Comprove que a célula [i,j] tem CANDIDATOS = {1..9} \\ (usados_na_linha ∪ usados_na_coluna ∪ usados_no_bloco)
                  e que o resultado tem cardinalidade 1 (apenas o "value").
                • Na explanation inclua, em linhas separadas:
                  - LINHA i: {…}    COLUNA j: {…}    BLOCO (b_i,b_j): {…}
                  - Candidatos([i,j]) = {1..9} \\ (L ∪ C ∪ B) = {k}
                  - Mini-matriz do bloco (ou linha/coluna) com os valores conhecidos (0 para vazios).
                • O foco é a restrição LOCAL da célula.

                EXEMPLO DE EXPLANATION (apenas formato; NÃO replique números do exemplo):
                \"\"\"
                Naked Single em [0,5]:
                LINHA 0 = {1,3,4,5,6,8,9} | COLUNA 5 = {1,2,3,4,5,8,9} | BLOCO (0,2) = {1,2,3,4,5,6,8,9}
                Candidatos([0,5]) = {1..9} \\ (L∪C∪B) = {7}
                Bloco (0,2):
                [ a b c
                  d e f
                  g h i ]
                Conclusão: único candidato restante é 7, caracterizando Naked Single.
                \"\"\"
            """.strip()

        elif technique == Technique.HIDDEN_SINGLES:
            extra = """
                REGRAS ESPECÍFICAS — HIDDEN SINGLES:
                • Mostre que o "value" aparece como candidato em EXATAMENTE UMA célula dentro de UMA unidade
                  (escolha UMA: linha i OU coluna j OU bloco 3x3).
                • NÃO basta a célula ter 1 candidato; o “único” é relativo à UNIDADE:
                  - Liste as células da unidade escolhida e indique onde o dígito "value" aparece como candidato.
                  - Comprove: ocorrências_do_value_na_unidade = 1.
                • Na explanation inclua:
                  - Unidade usada (ex.: LINHA 4) e mapeamento {pos -> candidatos_contendo_value}
                  - Mini-matriz da unidade (linha 1×9, coluna 9×1 ou bloco 3×3).
                  - Frase final: “{value} só pode ir em [i,j] dentro da {unidade}, logo Hidden Single”.

                EXEMPLO DE EXPLANATION (apenas formato):
                \"\"\"
                Hidden Single do dígito 9 na LINHA 1:
                Células com 9 como candidato na LINHA 1: {[1,2], [1,5]}
                Verificando restrições de bloco/coluna, apenas [1,5] permanece viável.
                Mini-linha 1:
                [ d1 d2 d3 d4 d5 d6 d7 d8 d9 ]
                Conclusão: 9 só pode ir em [1,5] na LINHA 1 -> Hidden Single.
                \"\"\"
            """.strip()

        else:
            extra = """
                REGRAS ESPECÍFICAS — CONSENSUS PRINCIPLE (profundidade 1 / árvore rasa):
                • Use análise por CASOS (ramos) com informação virtual:
                  - escolha um conjunto pequeno de alternativas mutuamente exclusivas
                    (ex.: duas ou três posições possíveis de um dígito numa unidade,
                    ou diferentes escolhas de candidato numa célula).
                • Para cada ramo:
                  - indique a suposição (“Se [r,c] = v...”, “Se o dígito d ficar na posição X...”);
                  - aplique deduções rasas e determinísticas (Naked/Hidden Singles + restrições diretas)
                    SEM abrir novos subcasos dentro do ramo.
                • Objetivo:
                  - mostrar que TODOS os ramos VIÁVEIS (que não geram contradição) implicam a MESMA conclusão
                    para a célula alvo [i,j] = value;
                  - ou então descartar um ramo explicitamente por violar regras do Sudoku (contradição).
                • A explanation deve:
                  - nomear e numerar os ramos (Ramo A, Ramo B, ...);
                  - listar as principais deduções em cada ramo (em formato de log);
                  - destacar, ao final, que “em todos os ramos válidos, [i,j] = value”, caracterizando Consensus.

                EXEMPLO (trecho resumido do log de Consensus em um Sudoku 4×4 onde (0,0)=3):

                \"\"\"
                Sudoku: Sudoku(((0, 1, 0, 0), (2, 0, 0, 1), (0, 0, 4, 0), (0, 3, 0, 0)))

                === [CONSENSUS] Analisando célula (0, 0)
                === [CONSENSUS] Região 0 com posições: [(0, 0), (0, 1), (0, 2), (0, 3)]
                - Célula (0, 0): candidatos plain = [3, 4]
                - Célula (0, 2): candidatos plain = [2, 3]
                - Célula (0, 3): candidatos plain = [2, 3, 4]

                [CANDIDATO 4] posições possíveis na região: [(0, 0), (0, 3)]
                > Assumindo 4 em (0, 3) e propagando Naked/Hidden Singles...
                - Dedução single: (0, 2) = 2
                - Dedução single: (1, 1) = 4
                - Dedução single: (1, 2) = 3
                - Dedução single: (2, 0) = 1
                - Dedução single: (2, 1) = 2
                - Dedução single: (2, 3) = 3
                - Dedução single: (3, 0) = 4
                - Dedução single: (3, 2) = 1
                - Dedução single: (3, 3) = 2
                Consequências da suposição 4 em (0, 3): [...]
                Candidatos em (0, 0) após suposição: [3]
                >>> Supondo 4 em (0, 3) força (0, 0) = 3

                (Outros ramos análogos, em diferentes regiões/unidades,
                 também forçando (0, 0) = 3.)

                === [CONSENSUS] Resultado em (0, 0): candidatos finais = [3]
                Conclusão final: em todos os ramos viáveis, obtemos (0,0)=3.
                \"\"\"

                Use esse ESTILO de log (estrutura, ramos, deduções e conclusão comum), mas adaptado ao Sudoku atual.
                O JSON final, porém, deve ser APENAS:

                {{
                  "position": [i, j],
                  "value": value,
                  "explanation": "RELATÓRIO COMPLETO DO CONSENSUS...",
                  "type": 3
                }}
            """.strip()

        format_block = f"""
            FORMATO DE SAÍDA (EXEMPLO ESTRUTURAL):
            {{
              "position": [3, 5],
              "value": 9,
              "explanation": "{meta["explanation_hint"]} — veja mini-relatório acima.",
              "type": {meta["code"]}
            }}

            LEMBRETE FINAL:
            • NÃO retorne texto fora do JSON.
            • NÃO omita o campo "type".
            • "type" DEVE ser exatamente {meta["code"]}.
        """.strip()

        prompt = textwrap.dedent(f"""
            {common_rules}

            {extra}

            {format_block}
        """).strip()

        return prompt

    @staticmethod
    def _sanitize_and_parse_json(text: str, technique: Technique) -> Dict[str, Any]:
        if not text:
            raise ValueError("Empty response from LLM")

        sanitized_text = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            text.strip(),
            flags=re.IGNORECASE,
        )

        try:
            obj = json.loads(sanitized_text)
        except json.JSONDecodeError as e:
            logging.error("Failed to parse LLM JSON response", exc_info=True)
            logging.debug("Raw LLM text: %s", text)
            raise ValueError(f"Invalid JSON from LLM: {e}") from e

        if isinstance(obj, dict) and "error" in obj:
            return obj

        if isinstance(obj, dict) and "type" not in obj:
            obj["type"] = TECH_META[technique]["code"]

        return obj
