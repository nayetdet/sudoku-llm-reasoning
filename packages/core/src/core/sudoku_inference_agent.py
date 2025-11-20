import json
import re
import textwrap
import google.generativeai as genai
from typing import Tuple, Dict, Any, Optional
from google.generativeai import GenerativeModel
from pydantic import BaseModel
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from core.exceptions.sudoku_inference_agent_exceptions import SudokuInferenceAgentGenerationException
from core.sudoku import Sudoku, SudokuCandidate

class SudokuInferenceCandidate(BaseModel):
    value: int
    position: Tuple[int, int]
    candidate_type: SudokuSimplifiedCandidateType
    explanation: str

    @property
    def candidate(self) -> SudokuCandidate:
        return SudokuCandidate(value=self.value, position=self.position)

class SudokuInferenceAgent:
    __PROMPT_TEMPLATES: Dict[SudokuSimplifiedCandidateType, str] = {
        SudokuSimplifiedCandidateType.ZEROTH_LAYER_NAKED_SINGLES: textwrap.dedent("""
            ### Regras específicas — Naked Singles

            1. Demonstre que a célula `[i,j]` possui o conjunto de candidatos:
               - `CANDIDATOS = DIGITOS_PERMITIDOS \\ (usados_na_linha ∪ usados_na_coluna ∪ usados_no_bloco)`
               - e que esse conjunto tem **cardinalidade 1** (apenas o `value`).

               Onde:
               - `DIGITOS_PERMITIDOS` é o conjunto de dígitos válidos da grade:
                 - `{1,2,3,4}` para Sudoku 4×4;
                 - `{1,2,3,4,5,6,7,8,9}` para Sudoku 9×9.

            2. Na `explanation`, inclua, em linhas separadas:
               - `LINHA i: {...}`  
                 `COLUNA j: {...}`  
                 `BLOCO (b_i,b_j): {...}`
               - `Candidatos([i,j]) = DIGITOS_PERMITIDOS \\ (L ∪ C ∪ B) = {k}`
               - Uma mini-matriz do bloco (ou da linha/coluna) com os valores conhecidos  
                 (use `0` para células vazias).

            3. O foco deve ser a **restrição local** da célula alvo:
               - Mostre claramente como os valores da linha, coluna e bloco restringem os candidatos.
               - A conclusão deve deixar explícito que só resta **um único candidato** para a célula.

            #### Exemplo de *explanation* (apenas FORMATO; NÃO replique números do exemplo)

            > Este exemplo ilustra o estilo do texto.  
            > Não copie os valores, posições nem o caso específico.

            ```text
            Naked Single em [0,5]:
            LINHA 0 = {1,3,4,5,6,8,9} | COLUNA 5 = {1,2,3,4,5,8,9} | BLOCO (0,2) = {1,2,3,4,5,6,8,9}
            Candidatos([0,5]) = {1..9} \ (L∪C∪B) = {7}
            Bloco (0,2):
            [ a b c
              d e f
              g h i ]
            Conclusão: único candidato restante é 7, caracterizando Naked Single.
            ```

            > ATENÇÃO:  
            > As cercas de código acima (` ``` `) existem apenas para o exemplo.  
            > **Na resposta final você NÃO deve usar cercas de código.**
        """).strip(),
        SudokuSimplifiedCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES: textwrap.dedent("""
            ### Regras específicas — Hidden Singles

            1. Mostre que o dígito `value` aparece como candidato em **EXATAMENTE UMA** célula
               dentro de **UMA** unidade escolhida (apenas uma das opções abaixo):
               - Linha `i`; ou
               - Coluna `j`; ou
               - Bloco (subgrade quadrada: 2×2 em Sudoku 4×4, 3×3 em Sudoku 9×9).

            2. O “único” aqui é **relativo à unidade**, não à célula isolada:
               - Liste as células da unidade escolhida.
               - Indique em quais posições o dígito `value` aparece como candidato.
               - Comprove que `ocorrências_do_value_na_unidade = 1`.

            3. Na `explanation`, inclua:
               - A unidade utilizada (por exemplo, `LINHA 4`) e um mapeamento do tipo  
                 `{posição -> candidatos_que_contem_value}`.
               - Uma mini-matriz da unidade (linha completa, coluna completa ou bloco).
               - Uma frase final do tipo:  
                 `"{value} só pode ir em [i,j] dentro da {unidade}, logo Hidden Single"`.

            #### Exemplo de *explanation* (apenas FORMATO; não use estes números)

            ```text
            Hidden Single do dígito 9 na LINHA 1:
            Células com 9 como candidato na LINHA 1: {[1,2], [1,5]}
            Verificando restrições de bloco/coluna, apenas [1,5] permanece viável.
            Mini-linha 1:
            [ d1 d2 d3 d4 d5 d6 d7 d8 d9 ]
            Conclusão: 9 só pode ir em [1,5] na LINHA 1 -> Hidden Single.
            ```

            > ATENÇÃO:  
            > As cercas de código acima (` ``` `) existem apenas para o exemplo.  
            > **Na resposta final você NÃO deve usar cercas de código.**
        """).strip(),
        SudokuSimplifiedCandidateType.FIRST_LAYER_CONSENSUS: textwrap.dedent("""
            ### Regras específicas — Consensus Principle (profundidade 1 / árvore rasa)

            1. Use **análise por casos (ramos)** com informação virtual:
               - Escolha um conjunto pequeno de alternativas mutuamente exclusivas, por exemplo:
                 - duas ou três posições possíveis de um dígito em uma mesma unidade; ou
                 - diferentes escolhas de candidato em uma única célula.

            2. Para cada ramo:
               - Declare claramente a suposição, por exemplo:  
                 `"Se [r,c] = v..."` ou `"Se o dígito d for colocado na posição X..."`.
               - Aplique apenas deduções rasas e determinísticas  
                 (Naked Singles, Hidden Singles e restrições diretas),
                 **sem** abrir novos subcasos dentro desse ramo.

            3. Objetivo:
               - Mostrar que todos os ramos **viáveis** (sem contradição) levam à **mesma conclusão**
                 para a célula alvo `[i,j] = value`; ou
               - Descartar explicitamente um ramo que viole as regras do Sudoku (contradição).

            4. A `explanation` deve:
               - Nomear e numerar os ramos (por exemplo, `Ramo A`, `Ramo B`, ...).
               - Listar as principais deduções de cada ramo, em formato de log.
               - Destacar ao final que  
                 `"em todos os ramos válidos, [i,j] = value"`, caracterizando o Consensus.

            #### Exemplo de log de Consensus (resumido, apenas FORMATO)

            ```text
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
            ```

            > ATENÇÃO:  
            > As cercas de código acima (` ``` `) existem apenas para o exemplo.  
            > **Na resposta final você NÃO deve usar cercas de código.**

            #### Estrutura esperada do JSON final (apenas FORMATO)

            ```json
            {
              "position": [i, j],
              "candidate_type": "FIRST_LAYER_CONSENSUS",
              "value": value,
              "explanation": "RELATÓRIO COMPLETO DO CONSENSUS..."
            }
            ```
        """).strip()
    }

    def __init__(self, llm_model: str, llm_api_key: str) -> None:
        genai.configure(api_key=llm_api_key)
        self.__llm: GenerativeModel = GenerativeModel(llm_model)

    def solve(self, sudoku: Sudoku, candidate_type: SudokuSimplifiedCandidateType) -> Optional[SudokuInferenceCandidate]:
        n: int = len(sudoku)
        prompt: str = textwrap.dedent(f"""
            ### Papel

            Você é um especialista em Sudoku de dimensão {n}×{n} e em explicações matemáticas claras.
            Sua tarefa é analisar a grade abaixo e localizar **exatamente UMA** ocorrência da técnica
            **"{candidate_type.display_name}"**, seguindo rigorosamente todas as instruções.

            ### Grade

            - Sudoku de dimensão {n}×{n}.
            - O dígito `0` representa uma célula vazia.
            - A grade fornecida representa o **estado atual** do jogo; não a altere.
            - Os dígitos permitidos são:
              - `1` a `4` se a grade for 4×4;
              - `1` a `9` se a grade for 9×9.

            Sudoku (0 = vazio):

            {sudoku}

            ### Objetivo

            1. Verificar se existe pelo menos uma ocorrência de {candidate_type.display_name}.
            2. Se houver várias, escolher **apenas uma**, usando esta ordem:
               - menor índice de linha `i`;
               - em empate, menor índice de coluna `j`.
            3. Retornar:
               - um único objeto JSON descrevendo a ocorrência escolhida; **ou**
               - o objeto de erro padronizado, se nenhuma ocorrência existir.

            ### Regras gerais (OBRIGATÓRIO)

            1. Responda com **apenas JSON válido**:
               - sem cercas de código (sem ```),
               - sem texto antes ou depois,
               - sem comentários.
            2. Use indexação zero-based: `"position" = [linha, coluna]`.
            3. NÃO inclua nenhum outro campo além dos especificados.
            4. NÃO invente dados:
               - toda afirmação deve ser coerente com a grade fornecida;
               - não use probabilidades, palpites ou termos vagos ("talvez", "pode ser").
            5. Use apenas tipos JSON padrão:
               - não use `NaN`, `Infinity`, `-Infinity`, `None`.
            6. NÃO aplique jogadas reais na grade, NÃO altere valores e NÃO considere estados futuros.

            ### Formato em caso de sucesso (OBRIGATÓRIO)

            Quando existir pelo menos uma ocorrência válida de {candidate_type.display_name},
            retorne **exatamente** um objeto JSON com estes 4 campos na raiz:

            {{
              "value": 3,                                  // inteiro: valor confirmado na célula alvo (exemplo)
              "position": [1, 2],                          // dois inteiros [i, j], zero-based (exemplo)
              "candidate_type": "{candidate_type.value}",  // string exata: "{candidate_type.value}"
              "explanation": "Relatório multilinha detalhado..."
            }}

            - O exemplo acima é **somente estrutural**:
              - substitua `3` por um dígito permitido na grade ({n}×{n});
              - substitua `[1, 2]` pela posição correta;
              - escreva uma `explanation` real e detalhada.
            - O campo `"candidate_type"` é **obrigatório** e DEVE ser exatamente `"{candidate_type.value}"`.

            ### Formato quando não houver ocorrência

            Se **não existir nenhuma** ocorrência de {candidate_type.display_name} nesta varredura,
            retorne **apenas** o JSON abaixo, sem campos extras e sem texto adicional:

            {{"error": "No results found"}}

            Nenhum outro formato é aceito para o caso sem resultado.

            ### Requisitos para o campo "explanation"

            A `explanation` deve ser um texto multilinha, adequado para log, que:

            - descreve o raciocínio passo a passo da técnica aplicada;
            - mostra explicitamente:
              - os conjuntos usados na dedução (linha, coluna, bloco, unidade etc.),
              - o conjunto de candidatos relevantes,
              - por que esse caso é um exemplo de {candidate_type.display_name},
              - um “recorte” em forma de matriz (linha/coluna/bloco/unidade) que apoie a prova;
            - usa a terminologia correta (não confunde Naked, Hidden, Consensus etc.);
            - coloca **todo** o raciocínio dentro do campo `"explanation"`;
            - não adiciona nenhum texto fora do objeto JSON final.

            ### Condições especiais sobre "candidate_type"

            - O campo `"candidate_type"` é **obrigatório**.
            - O valor deve ser exatamente a string `"{candidate_type.value}"`.
            - Não traduza, não abrevie, não altere maiúsculas/minúsculas
              e não use nomes alternativos.

            ### Regras específicas da técnica

            Leia e siga cuidadosamente as regras abaixo, específicas para
            **{candidate_type.display_name}**.  
            Os exemplos servem **apenas** para ilustrar o formato da `explanation`
            (não copie números, posições nem o caso específico):

            {self.__PROMPT_TEMPLATES[candidate_type]}

            ### Exemplo estrutural de saída (apenas FORMATO)

            {{
              "value": 3,
              "position": [1, 2],
              "candidate_type": "{candidate_type.value}",
              "explanation": "Relatório detalhado da técnica {candidate_type.display_name}..."
            }}

            ### Checklist final

            Antes de responder, confirme mentalmente:

            - [ ] Há apenas **um** objeto JSON na saída (sem texto extra).
            - [ ] O JSON é sintaticamente válido.
            - [ ] Em caso de sucesso, os campos são exatamente:
                  `"value"`, `"position"`, `"candidate_type"`, `"explanation"`.
            - [ ] Em caso sem resultado, o objeto é exatamente:
                  {{"error": "No results found"}}.
            - [ ] `"position"` contém dois inteiros `[i, j]` com indexação zero-based.
            - [ ] `"candidate_type"` é exatamente `"{candidate_type.value}"`.
            - [ ] Não há comentários, explicações ou texto fora do JSON.

            Agora gere **apenas** o objeto JSON final, seguindo todas as instruções acima.
        """)

        response: str = self.__llm.generate_content(prompt).text or ""
        payload: Dict[str, Any] = self.__get_inference_candidate_payload(response, candidate_type=candidate_type)
        if "error" in payload:
            return None
        return SudokuInferenceCandidate(**payload)

    @classmethod
    def __get_inference_candidate_payload(cls, text: str, candidate_type: SudokuSimplifiedCandidateType) -> Dict[str, Any]:
        if not text:
            raise SudokuInferenceAgentGenerationException("LLM returned an empty response")

        clean_text: str = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
        try: payload: Dict[str, Any] = json.loads(clean_text)
        except json.JSONDecodeError as e:
            raise SudokuInferenceAgentGenerationException(f"LLM return an invalid JSON: {e}")

        if "candidate_type" not in payload and "error" not in payload:
            payload["candidate_type"] = candidate_type.value
        return payload
