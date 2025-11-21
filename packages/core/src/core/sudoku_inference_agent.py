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
    def __init__(self, llm_model: str, llm_api_key: str) -> None:
        genai.configure(api_key=llm_api_key)
        self.__llm: GenerativeModel = GenerativeModel(llm_model)

    def solve(self, sudoku: Sudoku, candidate_type: SudokuSimplifiedCandidateType) -> Optional[SudokuInferenceCandidate]:
        prompt: str = self.__get_prompt(sudoku, candidate_type)
        response_text: str = self.__llm.generate_content(prompt).text or ""
        payload: Dict[str, Any] = self.__get_inference_candidate_payload(text=response_text, candidate_type=candidate_type)
        return SudokuInferenceCandidate(**payload) if "error" not in payload else None

    @classmethod
    def __get_prompt(cls, sudoku: Sudoku, candidate_type: SudokuSimplifiedCandidateType) -> str:
        n: int = len(sudoku)
        technique_name: str = candidate_type.display_name
        technique_code: str = candidate_type.value

        return textwrap.dedent(f"""
            ============================================================
            0. Visão geral rápida (leia antes de tudo)
            ============================================================

            Você é um **especialista em Sudoku depth-bounded**.

            Você recebe:
            - uma grade de Sudoku {n}×{n};
            - uma técnica alvo: "{technique_name}" (código interno "{technique_code}").

            Sua tarefa é **apenas**:

            1. Verificar se existe pelo menos UM passo correto da técnica "{technique_name}"
               na grade recebida.
            2. Se existir, escolher a ocorrência com:
               - menor índice de linha i;
               - em empate, menor índice de coluna j;
               e produzir UM único objeto JSON com esse passo.
            3. Se **não** existir ocorrência limpa da técnica alvo, responder
               exatamente com o JSON de erro:
               {{"error": "No results found"}}

            Regras de segurança:

            - Nunca misture técnicas: use **apenas** "{technique_name}".
            - Se você tiver qualquer dúvida se o passo é realmente um
              "{technique_name}" puro, considere que **não há ocorrência válida**
              e devolva o JSON de erro.
            - Não use outras técnicas avançadas (X-Wing, Swordfish, etc.).

            Técnicas possíveis (campo "candidate_type"):

            - "ZEROTH_LAYER_NAKED_SINGLES"  → Naked Singles (camada 0, sem suposições).
            - "ZEROTH_LAYER_HIDDEN_SINGLES" → Hidden Singles (camada 0, sem suposições).
            - "FIRST_LAYER_CONSENSUS"       → Consensus de primeira camada
                                              (usa ramos com suposições de profundidade 1).

            ============================================================
            1. Modelo de Sudoku e notação
            ============================================================

            - Dimensão: Sudoku {n}×{n}.
            - Cada célula contém um inteiro entre 0 e {n}.
              - 0 significa célula vazia.
            - Dígitos permitidos: 1, 2, ..., {n}.
            - Posição: [i, j] com indexação zero-based:
              - i = índice da linha (0 ≤ i < {n});
              - j = índice da coluna (0 ≤ j < {n}).

            Grade alvo (0 = vazio), no formato textual Python:

            {sudoku}

            ============================================================
            2. Candidatos de camada 0: C_plain([i, j])
            ============================================================

            Para cada célula vazia [i, j]:

            - VALORES_LINHA_i       = dígitos ≠ 0 já presentes na linha i.
            - VALORES_COLUNA_j      = dígitos ≠ 0 já presentes na coluna j.
            - VALORES_BLOCO_[i,j]   = dígitos ≠ 0 já presentes no bloco de [i, j].

            Definimos C_plain([i, j]) como o conjunto de dígitos permitidos
            que ainda podem ir nessa célula, isto é, dígitos que NÃO aparecem:

            - na linha i,
            - na coluna j,
            - nem no bloco de [i, j].

            Todas as técnicas desta tarefa usam **apenas** C_plain de camada 0.

            ------------------------------------------------------------
            2.1 Naked Singles  (código "ZEROTH_LAYER_NAKED_SINGLES")
            ------------------------------------------------------------

            Ideia:
            - A unicidade é vista **pela célula**.

            Critério para Naked Single em [i, j]:

            1. A célula [i, j] está vazia (valor 0).
            2. C_plain([i, j]) contém **exatamente um** dígito v.
            3. Esse v é compatível com linha, coluna e bloco
               (isso já é garantido pela definição de C_plain).

            O que você deve explicar na "explanation":
            - Quais dígitos aparecem na linha i, na coluna j e no bloco.
            - Como isso elimina todos os outros dígitos, deixando só v em C_plain([i, j]).
            - Conclusão: a célula [i, j] é forçada a receber v.

            Proibições para Naked Singles:
            - Não usar informação virtual nem suposições.
            - Não usar consensus.

            ------------------------------------------------------------
            2.2 Hidden Singles (código "ZEROTH_LAYER_HIDDEN_SINGLES")
            ------------------------------------------------------------

            Ideia:
            - A unicidade é vista **pela unidade** (linha, coluna ou bloco),
              não pela célula individual.

            Critério para Hidden Single de um dígito v em uma unidade U:

            1. Escolha uma unidade U:
               - uma linha k, ou
               - uma coluna k, ou
               - um bloco.
            2. Considere apenas as células vazias [r, c] dentro de U e seus C_plain.
            3. Um dígito v é Hidden Single em [i, j] se:
               - [i, j] está em U e é vazia;
               - v ∈ C_plain([i, j]);
               - nenhuma outra célula vazia de U tem v em seu C_plain.

            O que você deve explicar:
            - Qual é a unidade U (linha, coluna ou bloco).
            - Lista das células vazias de U com seus C_plain.
            - Mostrar que v só aparece como candidato em [i, j] dentro de U.
            - Conclusão: [i, j] deve receber v.

            Proibições para Hidden Singles:
            - Não usar informação virtual nem suposições.
            - Não usar consensus.

            ============================================================
            3. Consensus de primeira camada (código "FIRST_LAYER_CONSENSUS")
            ============================================================

            Intuição:

            - Consideramos alternativas mutuamente exclusivas (ramos) obtidas
              ao supor temporariamente um dígito em certas posições.
            - Em cada ramo usamos **apenas** Naked/Hidden Singles (camada 0).
            - Se todos os ramos viáveis concordam no mesmo valor para uma célula alvo,
              então esse valor é um candidato de Consensus para aquela célula
              na grade real (sem suposições).

            ------------------------------------------------------------
            3.1 Esquema operacional OBRIGATÓRIO para Consensus
            ------------------------------------------------------------

            Quando `candidate_type = "FIRST_LAYER_CONSENSUS"` você DEVE seguir
            esta estrutura na "explanation":

            1. Escolha uma **célula alvo** [i, j] vazia.
            2. Escolha uma região R que imponha restrições à célula alvo:
               - linha i, ou
               - coluna j, ou
               - bloco contendo [i, j].
            3. Escolha um dígito w que seja candidato em [i, j]
               (w ∈ C_plain([i, j])).
            4. Liste as outras posições de R onde w também é candidato
               segundo C_plain:
               - uma lista de posições p diferentes de [i, j] onde w é possível.
            5. Para cada posição p nessa lista, abra um **Ramo k**:

               - Comece explicitamente com algo como:
                 "Ramo k: suponha temporariamente w na célula p = [r, c]."
               - Construa mentalmente uma grade virtual com essa suposição.
               - A partir daí, aplique apenas:
                 - Naked Singles de camada 0; e
                 - Hidden Singles de camada 0.
               - Descreva as principais deduções (por exemplo, "Dedução single: ...").
               - Se surgir contradição (regra de Sudoku quebrada ou célula sem candidatos),
                 marque o ramo como inviável e descarte-o.

               - Se o ramo for viável, observe os candidatos finais
                 da célula alvo [i, j] nessa grade virtual.
                 - Em particular, destaque quando C_plain_virtual([i, j]) fica unitário
                   com um dígito w.

            6. Conclusão de consensus:

               - Considere apenas os ramos viáveis.
               - Se todos eles forçam o mesmo dígito w na célula alvo [i, j],
                 então w é candidato de Consensus de primeira camada em [i, j].
               - Na explanation final, afirme claramente essa convergência, por exemplo:
                 "Em todos os ramos viáveis, a célula [i, j] é forçada ao valor w,
                  logo w é um candidato de Consensus de primeira camada para [i, j]."

            Restrições importantes:

            - Profundidade: use **apenas uma camada** de suposição.
              - Dentro de cada ramo, você não pode abrir novos consensos;
                apenas Naked/Hidden Singles.
            - A grade real nunca é modificada; as suposições são sempre virtuais.

            ------------------------------------------------------------
            3.2 O que NÃO conta como Consensus
            ------------------------------------------------------------

            As situações abaixo **não** devem ser descritas como Consensus.
            Se apenas isso acontecer, você deve devolver o JSON de erro
            {{"error": "No results found"}}:

            - C_plain([i, j]) é unitário e você conclui o valor apenas por isso:
              isso é um Naked Single, não Consensus.
            - Um dígito v aparece como candidato em apenas uma célula de uma unidade:
              isso é um Hidden Single, não Consensus.
            - Você usa duas ou mais camadas de suposição (ramos dentro de ramos).
            - Você usa técnicas mais avançadas de Sudoku que não sejam Naked/Hidden.

            ------------------------------------------------------------
            3.3 Exemplo concreto de relato textual de Consensus
            ------------------------------------------------------------

            A explanation pode seguir um estilo parecido com o exemplo abaixo
            (apenas como ilustração; você deve adaptá-lo à grade concreta desta chamada):

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
                Conclusão final: em todos os ramos viáveis, obtemos (0, 0) = 3.

            ============================================================
            4. Técnica alvo desta chamada
            ============================================================

            Parâmetros:

            - candidate_type = "{technique_code}"
            - display_name   = "{technique_name}"

            Para esta chamada você deve:

            - usar apenas a técnica correspondente ao código recebido;
            - considerar as outras técnicas como proibidas
              (exceto como linguagem auxiliar na explanation).

            Resumo por código:

            - "ZEROTH_LAYER_NAKED_SINGLES":
              - buscar uma célula vazia [i, j] com C_plain([i, j]) contendo
                exatamente um dígito v.

            - "ZEROTH_LAYER_HIDDEN_SINGLES":
              - buscar uma unidade (linha, coluna ou bloco) onde um dígito v
                só aparece em C_plain de uma única célula vazia [i, j].

            - "FIRST_LAYER_CONSENSUS":
              - buscar uma célula alvo [i, j] vazia para a qual exista um
                raciocínio de consensus de primeira camada, conforme a Seção 3.

            ============================================================
            5. Protocolo de busca da ocorrência
            ============================================================

            1. Analise a grade e identifique **todas** as possíveis ocorrências
               válidas da técnica "{technique_name}".
            2. Se não existir nenhuma ocorrência válida:
               - responda exatamente com:
                 {{"error": "No results found"}}.
            3. Se houver uma ou mais ocorrências:
               - escolha a célula alvo [i, j] com:
                 - menor índice de linha i;
                 - em caso de empate, menor índice de coluna j.
               - Use essa ocorrência única para construir o JSON de sucesso.

            ============================================================
            6. Formato da resposta (APENAS JSON)
            ============================================================

            Você deve responder **somente** com um objeto JSON válido,
            sem nenhum texto fora dele e sem cercas de código.

            ------------------------
            6.1 Caso de sucesso
            ------------------------

            Formato exato:

            {{
              "value": 3,
              "position": [1, 2],
              "candidate_type": "{technique_code}",
              "explanation": "Relatório detalhado em português..."
            }}

            Onde:

            - "value":
              - inteiro entre 1 e {n};
              - é o dígito forçado pela técnica na célula alvo [i, j].

            - "position":
              - lista com exatamente dois inteiros [i, j], 0-based;
              - 0 ≤ i < {n} e 0 ≤ j < {n};
              - é a posição da célula alvo onde o valor será colocado.

            - "candidate_type":
              - string **exatamente** "{technique_code}".
              - Não invente outro valor e não use descrição em linguagem natural.

            - "explanation":
              - texto em português (pt-BR), possivelmente multilinha;
              - sem cercas de código;
              - para Naked/Hidden:
                - explique os C_plain relevantes e a unicidade local / na unidade;
              - para Consensus:
                - descreva claramente os ramos (Ramo 1, Ramo 2, ...),
                  suas suposições, deduções por singles, ramos inviáveis
                  e a convergência final na célula alvo.

            ------------------------
            6.2 Caso de ausência
            ------------------------

            Se, depois de aplicar cuidadosamente a definição da técnica alvo,
            você concluir que não há nenhuma ocorrência válida, responda
            apenas com:

            {{"error": "No results found"}}

            ============================================================
            7. Restrições globais e checklist final
            ============================================================

            Restrições:

            - Nunca escreva ``` ou qualquer tipo de cerca de código.
            - Nunca escreva texto fora do objeto JSON.
            - Não use valores especiais fora do JSON padrão
              (nada de NaN, Infinity, None, etc.).
            - Não altere o valor de "candidate_type": deve ser sempre "{technique_code}".

            Checklist mental antes de responder:

            - [ ] A técnica usada na explanation é estritamente "{technique_name}"?
            - [ ] Eu respeitei o protocolo de escolha da célula alvo (menor i, depois menor j)?
            - [ ] A célula alvo está vazia na grade original?
            - [ ] "value" está entre 1 e {n}?
            - [ ] "position" é uma lista [i, j] com índices válidos 0-based?
            - [ ] "candidate_type" é exatamente "{technique_code}"?
            - [ ] Para Consensus:
                  - usei pelo menos um ramo com suposição explícita?
                  - em todos os ramos viáveis, o mesmo dígito foi forçado na célula alvo?
                  - não usei profundidade maior que 1 nem outras técnicas avançadas?
            - [ ] Respondi apenas com um objeto JSON, sem texto extra?

            Agora faça todo o raciocínio internamente e produza
            **apenas** o objeto JSON final.
        """)

    @classmethod
    def __get_inference_candidate_payload(cls, text: str, candidate_type: SudokuSimplifiedCandidateType) -> Dict[str, Any]:
        if not text:
            raise SudokuInferenceAgentGenerationException("LLM returned an empty response")

        clean_text: str = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
        try: payload: Dict[str, Any] = json.loads(clean_text)
        except json.JSONDecodeError as e:
            raise SudokuInferenceAgentGenerationException(f"LLM returned an invalid JSON: {e}")

        if "candidate_type" not in payload and "error" not in payload:
            payload["candidate_type"] = candidate_type.value
        return payload
