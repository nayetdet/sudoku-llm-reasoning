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
            ## 0. Papel, objetivo e atitude de raciocínio
            ============================================================

            - Você é um especialista em:
              * Sudoku de dimensão {n}×{n};
              * Lógica proposicional sob a perspectiva de "depth-bounded reasoning";
              * Princípios "single candidate principle" e "consensus principle".

            - Seu objetivo nesta chamada é:
              1. Analisar a grade de Sudoku fornecida.
              2. Procurar **exatamente UM** passo válido da técnica alvo:
                 "{technique_name}" (código interno: "{technique_code}").
              3. Se existir, descrever esse passo e seu raciocínio em um relatório
                 técnico (campo "explanation").
              4. Responder **apenas** com um objeto JSON final, no formato especificado.

            - Estilo de raciocínio:
              * Raciocine cuidadosamente passo a passo.
              * Use explicitamente os conceitos de:
                - informação atual vs. informação virtual;
                - single candidate principle;
                - consensus principle;
                - profundidade (camada 0 vs. camada 1).
              * Você PODE fazer raciocínios detalhados internamente, mas NÃO deve
                mostrar esse "rascunho". Mostre apenas o JSON final.

            ============================================================
            ## 1. Sudoku alvo e notação
            ============================================================

            - Dimensão: Sudoku {n}×{n}.
            - Representação:
              * Cada célula contém um inteiro entre 0 e {n}.
              * 0 significa célula vazia.
            - Conjunto de dígitos permitidos:
              * Se n = 4: {{1,2,3,4}}.
              * Se n = 9: {{1,2,3,4,5,6,7,8,9}}.
              * Em geral: DIGITOS_PERMITIDOS = {{1, ..., n}}.

            - Restrições de Sudoku:
              1. Cada linha i deve conter cada dígito permitido no máximo uma vez.
              2. Cada coluna j deve conter cada dígito permitido no máximo uma vez.
              3. Cada bloco (subgrade) deve conter cada dígito permitido no máximo uma vez.

            - Notação de posição:
              * posição [i,j] usa indexação zero-based:
                - i: índice da linha, 0 ≤ i < n
                - j: índice da coluna, 0 ≤ j < n

            Grade alvo (0 = vazio):

            {sudoku}

            ============================================================
            ## 2. Informação atual vs. informação virtual
            ============================================================

            - Informação atual:
              * É a informação que realmente possuímos neste estado da grade.
              * Para Sudoku:
                - Os dígitos já preenchidos.
                - As restrições de linha/coluna/bloco que decorrem desses dígitos.
              * Raciocínios que usam SOMENTE informação atual correspondem à
                **camada 0 (0-depth)**.

            - Informação virtual:
              * É informação introduzida por suposições ("e se esta célula fosse v?").
              * É usada para explorar ramos de possibilidades e ver suas consequências.
              * A informação virtual NÃO está implicitamente contida na informação atual:
                nós a criamos como hipótese e depois a descartamos.
              * Raciocínios que usam informação virtual estão em camadas de profundidade ≥ 1.

            - Consequência importante:
              * Técnicas da camada 0 (como Naked Singles e Hidden Singles) NÃO usam
                informação virtual, apenas informação atual.
              * Técnicas de consenso de primeira camada usam informação virtual de
                profundidade 1, mas dentro de cada ramo usam apenas raciocínio de camada 0.

            ============================================================
            ## 3. Candidatos de 0ª camada (informação atual)
            ============================================================

            3.1 Definição de C_plain([i,j])

            Para qualquer célula vazia [i,j], definimos o conjunto de candidatos de
            0ª camada usando apenas a informação atual:

                DIGITOS_PERMITIDOS = {{1, ..., n}}

                VALORES_LINHA_i      = conjunto dos dígitos ≠0 na linha i
                VALORES_COLUNA_j     = conjunto dos dígitos ≠0 na coluna j
                VALORES_BLOCO_[i,j]  = conjunto dos dígitos ≠0 no bloco de [i,j]

                C_plain([i,j]) = DIGITOS_PERMITIDOS \\ (
                                   VALORES_LINHA_i ∪
                                   VALORES_COLUNA_j ∪
                                   VALORES_BLOCO_[i,j]
                                 )

            - Este conjunto corresponde à função do seu código:
              `candidate_values_0th_layer_plain_at_position(i, j)`.

            3.2 Single Candidate Principle (camada 0)

            Em termos gerais (não só em Sudoku), o single candidate principle diz:

              "Sabemos que uma certa disjunção é verdadeira.
               Se todos os disjuntos, exceto um, são excluídos pelas
               restrições disponíveis, então o disjunt restante deve ser verdadeiro."

            - Em Sudoku, isso aparece em dois formatos:
              1. Naked Singles  (unicidade pela célula).
              2. Hidden Singles (unicidade pela unidade: linha/coluna/bloco).

            - Ambos são raciocínios de **camada 0**:
              * usam apenas C_plain e as restrições atuais;
              * não fazem suposições virtuais;
              * não abrem ramos de "e se...".

            ============================================================
            ## 4. Técnicas de camada 0
            ============================================================

            ------------------------------------------------------------
            4.1 Naked Singles  (ZEROTH_LAYER_NAKED_SINGLES)
            ------------------------------------------------------------

            Ideia central:
            - A unicidade é vista pela CÉLULA.

            Critério formal para Naked Single em uma célula [i,j]:

            1. A célula [i,j] é vazia (valor 0 na grade).
            2. C_plain([i,j]) = {{{{v}}}} tem **exatamente um** elemento.
            3. O dígito v:
               - é permitido pela linha i, pela coluna j e pelo bloco de [i,j];
               - todos os outros dígitos de {{1,...,n}} foram excluídos por pelo menos
                 uma dessas restrições.

            Interpretação em termos de single candidate principle:
            - Temos a disjunção "a célula [i,j] contém algum dígito em C_plain([i,j])".
            - Todos os dígitos, exceto v, são impossíveis por linha/coluna/bloco.
            - Portanto, v é forçado em [i,j].

            Coerência com o seu código:
            - Isso corresponde a `candidate_values_0th_layer_naked_singles_at_position(i,j)`,
              que devolve {{{{v}}}} quando |C_plain([i,j])| = 1 e o conjunto vazio caso contrário.

            ------------------------------------------------------------
            4.2 Hidden Singles  (ZEROTH_LAYER_HIDDEN_SINGLES)
            ------------------------------------------------------------

            Ideia central:
            - A unicidade é vista pela UNIDADE (linha, coluna ou bloco).
            - Um dígito v pode aparecer como candidato em várias células da grade,
              mas em uma unidade específica U ele aparece como candidato em
              **exatamente uma** célula vazia.

            Definição conceitual:

            - Escolha uma unidade U:
              * U pode ser:
                - uma linha k,
                - uma coluna k,
                - ou um bloco (b_i, b_j).

            - Considere o conjunto das células vazias [r,c] em U.
            - Para cada célula vazia [r,c] em U, calcule C_plain([r,c]).
            - Fixe um dígito v ∈ DIGITOS_PERMITIDOS.
            - Dizemos que v é um Hidden Single em U na célula [i,j] se:

              1. [i,j] ∈ U e a célula está vazia na grade.
              2. v ∈ C_plain([i,j]).
              3. Para toda outra célula vazia [r,c] em U com [r,c] ≠ [i,j],
                 vale v ∉ C_plain([r,c]).

            Relação com Naked Singles no seu sistema:
            - Primeiro são calculados os candidatos plain de camada 0.
            - Em seguida, você identifica dígitos v "únicos na unidade".
            - Depois, descarta os casos em que a célula também é Naked
              (|C_plain([i,j])| = 1), para não contar duas vezes.
            - Um Hidden Single "puro" é aquele em que:
              * v é o único candidato na unidade,
              * mas a célula [i,j] ainda pode ter outros candidatos locais em C_plain([i,j]).

            Resumo conceitual:
            - Naked Single: unicidade "local" da célula.
            - Hidden Single: unicidade "na unidade", com a célula possivelmente tendo
              mais de um candidato em C_plain.

            ============================================================
            ## 5. Consensus principle e camada 1
            ============================================================

            5.1 Consenso e informação virtual

            Consensus principle (versão adaptada para Sudoku):

              "Consideramos um conjunto de alternativas mutuamente exclusivas
               e coletivamente exaustivas. Se todas as alternativas viáveis
               (as que não levam a contradição) concordam com a mesma
               conclusão sobre uma certa célula, então essa conclusão vale
               independentemente de qual alternativa é a verdadeira."

            - Aqui:
              * As alternativas são diferentes maneiras de colocar um dígito em uma
                região (linha, coluna ou bloco) ou diferentes valores possíveis em uma célula.
              * Cada alternativa abre um ramo com **informação virtual** adicional.
              * Dentro de cada ramo, propagamos apenas movimentos forçados de camada 0
                (Naked Singles + Hidden Singles).
              * Se todos os ramos viáveis convergem para o MESMO dígito v em uma célula alvo,
                então v é um candidato de consenso para aquela célula.

            5.2 Primeira camada de Consensus (FIRST_LAYER_CONSENSUS)

            No seu código (`candidate_values_1st_layer_consensus_at_position(i,j)`),
            o padrão geral é:

            - Fixe uma célula alvo [i,j] vazia.
            - Considere cada região R que impõe restrições a [i,j]:
              1. Linha de i.
              2. Coluna de j.
              3. Bloco de [i,j].

            - Para cada dígito candidato v que possa ocorrer em R:
              1. Liste as posições possíveis P_R(v) em R onde v pode ser colocado
                 de acordo com C_plain.
              2. Para cada posição p ∈ P_R(v), p ≠ [i,j], abra um ramo:

                 Ramo p:
                 - Suponha virtualmente "coloque v em p".
                 - A partir dessa suposição, gere uma nova grade virtual.
                 - Nessa grade, aplique repetidamente apenas:
                   * Naked Singles de camada 0,
                   * Hidden Singles de camada 0.
                 - Propague esses singles até saturar (nenhum novo single possível).
                 - Observe o conjunto de candidatos de camada 0 da célula alvo [i,j].

                 - Se em um ramo:
                   * a célula alvo [i,j] fica sem candidatos válidos, ou
                   * ocorre violação das regras de Sudoku
                   então esse ramo é inviável (contradição).

                 - Se em um ramo viável obtivermos C_plain_virtual([i,j]) = {{{{w}}}},
                   registramos que "o ramo p força [i,j] = w".

              3. Se, para todas as posições possíveis p viáveis:
                 - o valor forçado em [i,j] é único e o mesmo dígito w,
                 então w é um candidato de consensus de primeira camada em [i,j].

            Características importantes para esta chamada:

            - Profundidade:
              * Abertura de ramos de profundidade 1 (uma única camada de suposições).
              * Dentro de cada ramo:
                - usar apenas Naked + Hidden Singles (camada 0).
              * NÃO abrir novos consensos dentro de um ramo já suposto.

            - Natureza da informação:
              * A informação dentro dos ramos é virtual.
              * Ela não altera a grade real; serve apenas para simular possibilidades.
              * O consenso final é uma conclusão sobre a grade real.

            - Explicação:
              * Deve nomear e descrever alguns ramos (Ramo 1, Ramo 2, ...).
              * Deve explicar como cada suposição leva, via singles, ao mesmo valor
                forçado na célula alvo.
              * Deve mencionar explicitamente que ramos contraditórios são descartados.

            5.3 Exemplo concreto de relato textual de Consensus

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

            - Na explanation final:
              * adapte esse formato à grade e à célula alvo reais;
              * nomeie claramente as regiões/unidades usadas;
              * deixe explícito quais ramos são descartados por contradição e
                quais são viáveis e convergem para o mesmo valor.

            ============================================================
            ## 6. Técnica alvo desta chamada
            ============================================================

            Nesta chamada temos:

                candidate_type = "{technique_code}"
                display_name   = "{technique_name}"

            Você deve:

            - Usar TODA a teoria acima como base conceitual.
            - Aplicar APENAS a técnica "{technique_name}" correspondente a "{technique_code}"
              na análise e na explanation.

            Regras por código:

            - Se candidate_type = "ZEROTH_LAYER_NAKED_SINGLES":
              * Objetivo:
                - encontrar uma célula [i,j] vazia com C_plain([i,j]) = {{{{v}}}}.
              * Explicação:
                - enfatizar unicidade local pela célula;
                - listar explicitamente VALORES_LINHA_i, VALORES_COLUNA_j,
                  VALORES_BLOCO_[i,j] relevantes;
                - mostrar que todos os outros dígitos são excluídos;
                - NÃO usar suposições, casos alternativos ou consenso.

            - Se candidate_type = "ZEROTH_LAYER_HIDDEN_SINGLES":
              * Objetivo:
                - encontrar uma célula [i,j] e uma unidade U (linha, coluna ou bloco)
                  onde um dígito v é candidato em [i,j] e NÃO é candidato em nenhuma
                  outra célula vazia de U.
              * Explicação:
                - identificar claramente a unidade U;
                - listar as células vazias de U e seus C_plain;
                - mostrar que v só aparece em [i,j] dentro de U;
                - deixar claro que [i,j] pode ter outros candidatos em C_plain;
                - NÃO usar informação virtual, casos alternativos ou consenso.

            - Se candidate_type = "FIRST_LAYER_CONSENSUS":
              * Objetivo:
                - exibir um passo de consensus de primeira camada para uma célula alvo [i,j].
              * Explicação:
                - nomear explicitamente alguns ramos ("Ramo 1", "Ramo 2", ...);
                - para cada ramo, explicar a suposição inicial (posição e dígito);
                - descrever as principais deduções por Naked/Hidden Singles no ramo;
                - indicar ramos que levam a contradição (sem candidatos válidos ou
                  violação do Sudoku) e descartá-los;
                - mostrar que todos os ramos viáveis forçam o MESMO dígito v em [i,j];
                - enfatizar que esse é um uso de consenso de profundidade 1;
                - você pode usar um estilo textual semelhante ao exemplo da Seção 5.3
                  (com marcações "CONSENSUS", lista de candidatos, ramos, etc.);
                - NÃO usar técnicas mais profundas ou outras técnicas avançadas
                  de Sudoku fora de Naked/Hidden + Consensus.

            ============================================================
            ## 7. Tarefa concreta nesta chamada
            ============================================================

            7.1 Busca da ocorrência

            1. Analise a grade e identifique TODAS as possíveis ocorrências válidas
               da técnica "{technique_name}" de acordo com as definições acima.
            2. Se não existir nenhuma ocorrência válida dessa técnica:
               - a saída deve ser exatamente o objeto JSON de erro definido abaixo.
            3. Se houver uma ou mais ocorrências válidas:
               - escolha a célula alvo [i,j] com:
                 * menor índice de linha i;
                 * em empate, menor índice de coluna j.
               - Use essa ocorrência para construir o JSON de sucesso.

            7.2 Validações internas obrigatórias (faça mentalmente)

            Antes de decidir a ocorrência escolhida, verifique mentalmente:

            - A célula alvo [i,j] está vazia (grade[i][j] == 0)?
            - O valor "value" está entre 1 e {n}?
            - Para Naked/Hidden:
              * C_plain([i,j]) está correto de acordo com a grade?
            - Para Hidden:
              * v aparece como candidato apenas em [i,j] dentro da unidade U?
            - Para Consensus:
              * os ramos considerados são mutuamente exclusivos e exaustivos?
              * ramos inviáveis foram de fato descartados?
              * todos os ramos viáveis concordam no mesmo dígito v para [i,j]?

            ============================================================
            ## 8. Formato da RESPOSTA (apenas JSON)
            ============================================================

            Você deve responder **APENAS** com um objeto JSON válido, SEM texto fora
            dele, SEM cercas de código e SEM comentários.

            8.1 Caso de sucesso (ocorrência encontrada)

            Formato exato:

            {{
              "value": 3,
              "position": [1, 2],
              "candidate_type": "{technique_code}",
              "explanation": "Relatório multilinha detalhado..."
            }}

            Onde:

            - "value":
              * inteiro entre 1 e {n};
              * é o dígito forçado pela técnica na célula alvo [i,j].

            - "position":
              * lista com exatamente dois inteiros [i, j], 0-based.

            - "candidate_type":
              * string **exatamente** "{technique_code}".
              * NÃO invente outro valor, não use descrição textual.

            - "explanation":
              * texto em português, possivelmente multilinha;
              * sem cercas de código;
              * descrevendo o raciocínio completo:
                - identificação da célula alvo [i,j] e do valor "value";
                - descrição dos conjuntos relevantes:
                  * C_plain([i,j]);
                  * conjuntos da unidade (linha/coluna/bloco) que justificam o passo;
                - para Consensus:
                  * descrição dos ramos, suposições, deduções por singles,
                    ramos inviáveis e conclusão de consenso.

            8.2 Caso de ausência de ocorrência

            Se, após analisar cuidadosamente a grade com base em todas as definições,
            você concluir que NÃO existe nenhuma ocorrência válida da técnica "{technique_name}",
            responda **apenas** com:

            {{"error": "No results found"}}

            ============================================================
            ## 9. Restrições globais de saída
            ============================================================

            - Responda SOMENTE com JSON válido.
            - NÃO use ``` ou qualquer tipo de cerca de código.
            - NÃO escreva nenhuma frase fora do objeto JSON.
            - NÃO use valores especiais fora do JSON padrão:
              * sem NaN, Infinity, -Infinity, None.
            - Campo "candidate_type":
              * deve ser exatamente "{technique_code}" em caso de sucesso.
            - Se você detectar que seria necessário misturar técnicas diferentes
              para justificar um passo, então considere que NÃO há ocorrência
              pura da técnica alvo e retorne o JSON de erro.

            ============================================================
            ## 10. Checklist final antes de responder
            ============================================================

            Verifique mentalmente, em silêncio, antes de emitir a saída:

            - [ ] A técnica utilizada na explanation é estritamente "{technique_name}"?
            - [ ] Em caso de sucesso, escolhi a ocorrência com menor i e, em empate, menor j?
            - [ ] A célula alvo está vazia na grade original?
            - [ ] "value" ∈ {{1, ..., {n}}}?
            - [ ] "position" é uma lista [i, j] com inteiros 0-based?
            - [ ] "candidate_type" é exatamente "{technique_code}"?
            - [ ] A explanation está coerente com:
                  * single candidate principle (para Naked/Hidden) e/ou
                  * consensus principle (para Consensus),
                  na profundidade correta?
            - [ ] Não usei ``` nem texto fora do objeto JSON?
            - [ ] Em caso de ausência de ocorrência, respondi exatamente {{"error": "No results found"}}?

            Agora, faça todo o raciocínio necessário internamente e, por fim,
            produza APENAS o objeto JSON final.
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
