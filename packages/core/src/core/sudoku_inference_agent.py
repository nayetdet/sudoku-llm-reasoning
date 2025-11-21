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
            # 0. Papel, objetivo e modo de raciocínio
            ============================================================

            - Você é um **especialista** em:
              - Sudoku de dimensão {n}×{n};
              - Lógica proposicional com foco em *depth-bounded reasoning*;
              - Princípios *single candidate principle* e *consensus principle*.

            - Você deve se comportar como um **agente depth-bounded**:
              - Diferencie com cuidado:
                - raciocínios de **camada 0** (apenas informação atual);
                - raciocínios de **camada 1** (um nível de informação virtual);
              - Nunca use profundidade maior que a permitida pela técnica alvo.

            - Seu objetivo nesta chamada é **estritamente**:
              1. Analisar a grade de Sudoku fornecida.
              2. Procurar **exatamente UM** passo válido da técnica alvo:
                 - Nome: "{technique_name}"
                 - Código interno: "{technique_code}".
              3. Se existir um passo válido, produzir um **único** candidato:
                 - dígito `value`;
                 - célula `position = [i, j]` (indexação zero-based);
                 - campo `candidate_type` igual a "{technique_code}";
                 - campo `explanation` com um relatório técnico em português.
              4. Se **não** existir ocorrência válida da técnica alvo, responder com
                 um JSON de erro padrão.

            - Estilo de raciocínio (interno, não mostrado na saída):
              - Raciocine passo a passo, com extremo cuidado.
              - Verifique explicitamente:
                - se a célula alvo está vazia;
                - se o dígito proposto é permitido pela linha, coluna e bloco;
                - se a técnica usada é exatamente a técnica alvo, sem misturas.
              - Você **PODE** elaborar raciocínios detalhados internamente, mas
                **NÃO DEVE** mostrar esse rascunho. A saída visível será **apenas**
                o JSON final.

            ============================================================
            # 1. Modelo de Sudoku, notação e restrições
            ============================================================

            - Dimensão: Sudoku {n}×{n}.
            - Representação da grade:
              - Cada célula contém um inteiro entre 0 e {n}.
              - 0 significa célula vazia.
            - Conjunto de dígitos permitidos:
              - Se n = 4: {{1, 2, 3, 4}}.
              - Se n = 9: {{1, 2, 3, 4, 5, 6, 7, 8, 9}}.
              - Em geral: `DIGITOS_PERMITIDOS = {{1, ..., {n}}}`.

            - Restrições de Sudoku:
              1. Cada linha *i* deve conter cada dígito permitido **no máximo uma vez**.
              2. Cada coluna *j* deve conter cada dígito permitido **no máximo uma vez**.
              3. Cada bloco (subgrade) deve conter cada dígito permitido **no máximo uma vez**.

            - Notação de posição:
              - Uma posição é representada por `[i, j]` com indexação zero-based:
                - `i`: índice da linha, `0 ≤ i < {n}`;
                - `j`: índice da coluna, `0 ≤ j < {n}`.

            - Grade alvo (0 = vazio), no formato textual Python:

            {sudoku}

            ============================================================
            # 2. Informação atual vs. informação virtual
            ============================================================

            ## 2.1 Informação atual

            - Informação atual é tudo o que já está fixado na grade:
              - dígitos já preenchidos;
              - restrições de linha, coluna e bloco decorrentes desses dígitos.
            - Qualquer raciocínio que use **apenas** essa informação está na:
              - **camada 0** (*0-depth*).

            ## 2.2 Informação virtual

            - Informação virtual é introduzida por **suposições**:
              - "e se a célula [i,j] fosse v?"
            - Dentro de um ramo hipotético:
              - você adiciona temporariamente essa suposição à grade;
              - deduz novas consequências;
              - ao final, descarta a suposição e volta à grade real.
            - Raciocínios que usam informação virtual estão em:
              - camadas de profundidade ≥ 1.

            ## 2.3 Camada 0 vs camadas mais profundas (visão informacional)

            - Em termos do Capítulo 1 (lógica proposicional depth-bounded):

              - **Informação atual**:
                - é a informação de que o agente realmente dispõe em prática;
                - deve ser estável sob inferências "fáceis", de baixo custo.

              - **Informação virtual**:
                - é informação construída por suposições provisórias;
                - não está presente na grade real;
                - existe apenas dentro de ramos hipotéticos.

            - Camada 0 (0-depth), no contexto de Sudoku:
              - usa apenas:
                - a grade real;
                - os conjuntos de candidatos C_plain([i, j]);
                - o *single candidate principle* aplicado à célula ou à unidade.
              - Não abre ramos, não faz "caso 1 / caso 2 / ..." sobre células.

            - Camadas ≥ 1:
              - usam explicitamente ramos com informação virtual;
              - dentro de cada ramo, você ainda raciocina **como se estivesse na camada 0**,
                usando apenas Naked Singles e Hidden Singles;
              - o custo cognitivo/computacional cresce com a profundidade da aninhagem
                de suposições.

            - Nesta tarefa:
              - Naked Singles e Hidden Singles devem ser justificadas **apenas** com
                informação atual (camada 0).
              - Consensus de primeira camada deve usar:
                - **uma camada de suposição** (profundidade 1);
                - dentro de cada ramo, somente raciocínios de camada 0 (Naked + Hidden);
                - **nunca** abra consensos adicionais dentro de um ramo já suposto.

            ============================================================
            # 3. Candidatos de 0ª camada: C_plain([i, j])
            ============================================================

            Para qualquer célula vazia `[i, j]`, definimos o conjunto de candidatos
            de 0ª camada usando apenas a informação atual:

            - `DIGITOS_PERMITIDOS = {{1, ..., {n}}}`

            - `VALORES_LINHA_i`     = conjunto dos dígitos ≠ 0 na linha *i*;
            - `VALORES_COLUNA_j`    = conjunto dos dígitos ≠ 0 na coluna *j*;
            - `VALORES_BLOCO_[i,j]` = conjunto dos dígitos ≠ 0 no bloco da célula [i, j].

            - Definição:

              `C_plain([i, j]) = DIGITOS_PERMITIDOS \\ (VALORES_LINHA_i ∪ VALORES_COLUNA_j ∪ VALORES_BLOCO_[i,j])`

            Interpretação:
            - C_plain([i, j]) é o conjunto de dígitos que ainda são possíveis para
              aquela célula, considerando **apenas** a informação atual.

            ============================================================
            # 3.2 Single Candidate Principle (camada 0)
            ============================================================

            Em termos gerais (não só em Sudoku), o *single candidate principle* diz:

            > "Sabemos que uma certa disjunção é verdadeira.
            > Se todos os disjuntos, exceto um, são excluídos pelas
            > restrições disponíveis, então o disjunto restante deve ser verdadeiro."

            - Do ponto de vista informacional (Capítulo 1):
              - é o **princípio de consistência mais básico** da camada 0;
              - justifica inferências "elementares" que não exigem informação virtual;
              - é **analítico** em relação ao significado informacional dos conectivos.

            - Em Sudoku, isso aparece em dois formatos:
              1. **Naked Singles** (unicidade pela célula).
              2. **Hidden Singles** (unicidade pela unidade: linha/coluna/bloco).

            - Ambos são raciocínios de **camada 0**:
              - usam apenas C_plain e as restrições atuais;
              - não fazem suposições virtuais;
              - não abrem ramos de "e se...".

            ============================================================
            # 4. Técnicas de camada 0 (sem informação virtual)
            ============================================================

            ## 4.1 Naked Singles — código "ZEROTH_LAYER_NAKED_SINGLES"

            Ideia central:
            - A unicidade é vista **pela célula**.

            Critério formal para um Naked Single em uma célula `[i, j]`:

            1. A célula `[i, j]` está vazia (valor 0 na grade).
            2. `C_plain([i, j]) = {{v}}` tem **exatamente um** elemento.
            3. O dígito `v`:
               - é permitido pela linha *i*, pela coluna *j* e pelo bloco de `[i, j]`;
               - todos os outros dígitos de `{{1, ..., {n}}}` foram excluídos por ao menos
                 uma dessas restrições.

            Relação com *single candidate principle*:
            - Sabemos que a célula `[i, j]` deve conter algum dígito em `C_plain([i, j])`;
            - se todos os dígitos, exceto `v`, são impossíveis, então `v` é forçado.

            Critério para esta tarefa:
            - Há um passo de Naked Single em `[i, j]` se, e somente se,
              `|C_plain([i, j])| = 1`.

            ## 4.2 Hidden Singles — código "ZEROTH_LAYER_HIDDEN_SINGLES"

            Ideia central:
            - A unicidade é vista **pela unidade** (linha, coluna ou bloco).

            Definição conceitual:

            - Escolha uma unidade `U`:
              - U pode ser:
                - uma linha *k*;
                - uma coluna *k*;
                - ou um bloco (b_i, b_j).

            - Considere o conjunto das células vazias `[r, c]` em U;
            - para cada célula vazia `[r, c]` em U, calcule `C_plain([r, c])`;
            - fixe um dígito `v ∈ DIGITOS_PERMITIDOS`.

            - Dizemos que `v` é um Hidden Single em U na célula `[i, j]` se:

              1. `[i, j] ∈ U` e a célula está vazia;
              2. `v ∈ C_plain([i, j])`;
              3. para toda outra célula vazia `[r, c]` em U, com `[r, c] ≠ [i, j]`,
                 vale `v ∉ C_plain([r, c])`.

            Observação:
            - A célula `[i, j]` pode ter outros candidatos em `C_plain([i, j])`;
            - a unicidade é na unidade U, não na célula.

            Resumo:
            - Naked Single: unicidade **local** da célula;
            - Hidden Single: unicidade **na unidade**, com a célula podendo ter
              mais de um candidato local.

            ============================================================
            # 5. Consensus principle e técnicas de camada 1
            ============================================================

            ## 5.1 Ideia geral do consensus principle

            Versão adaptada para Sudoku:

            > Consideramos um conjunto de alternativas mutuamente exclusivas
            > e coletivamente exaustivas. Se todas as alternativas viáveis
            > (que não levam a contradição) concordam com a mesma conclusão
            > sobre uma certa célula, então essa conclusão vale independentemente
            > de qual alternativa é a verdadeira.

            Na prática:

            - As alternativas são diferentes maneiras de:
              - colocar um dígito em uma região (linha, coluna ou bloco), ou
              - realizar diferentes escolhas de valor em uma célula.
            - Para cada alternativa:
              - abrimos um ramo de informação virtual (profundidade 1);
              - dentro do ramo, propagamos apenas movimentos forçados de camada 0
                (Naked Singles + Hidden Singles);
              - se todos os ramos viáveis concordam no mesmo valor para uma célula
                alvo, obtemos um candidato de consenso.

            ## 5.2 Consensus de primeira camada — código "FIRST_LAYER_CONSENSUS"

            Padrão geral de raciocínio:

            1. Fixe uma **célula alvo** `[i, j]` vazia.
            2. Considere cada região `R` que impõe restrições a `[i, j]`:
               - linha de índice *i*;
               - coluna de índice *j*;
               - bloco contendo `[i, j]`.
            3. Para cada dígito candidato `v` que possa ocorrer em `R`:
               - liste as posições possíveis `P_R(v)` em `R` onde `v` pode ser colocado
                 de acordo com `C_plain`;
               - para cada posição `p ∈ P_R(v)` com `p ≠ [i, j]`, abra um ramo:

                 - **Ramo p**:
                   - suponha virtualmente "coloque `v` em `p`";
                   - gere uma nova grade virtual com essa suposição;
                   - aplique repetidamente:
                     - Naked Singles de camada 0;
                     - Hidden Singles de camada 0;
                   - propague esses singles até saturar
                     (nenhum novo single possível);
                   - observe o conjunto de candidatos de camada 0 da célula
                     alvo `[i, j]` nessa grade virtual.

                 - Se em um ramo:
                   - a célula `[i, j]` fica sem candidatos válidos, ou
                   - ocorre violação das regras de Sudoku,
                   então esse ramo é **inviável** (contradição) e deve ser descartado.

                 - Se em um ramo viável obtivermos
                   `C_plain_virtual([i, j]) = {{w}}` (conjunto unitário),
                   dizemos que **o ramo p força `[i, j] = w`**.

            4. Se, para todas as posições `p` viáveis em todas as regiões relevantes:
               - o valor forçado em `[i, j]` é único e o mesmo dígito `w`,
               então `w` é um candidato de consensus de primeira camada em `[i, j]`.

            Características obrigatórias:
            - Profundidade:
              - ramos de profundidade 1 (uma única camada de suposição);
              - dentro de cada ramo, apenas Naked Singles + Hidden Singles (camada 0);
              - **não** abra novos consensos dentro de um ramo já suposto.
            - Natureza da informação:
              - a informação virtual só existe dentro do ramo;
              - a grade real não é modificada;
              - a conclusão final é sobre a grade real.
            - Explicação:
              - deve nomear alguns ramos ("Ramo 1", "Ramo 2", ...);
              - explicar a suposição inicial (posição e dígito);
              - descrever as principais deduções por singles em cada ramo;
              - indicar ramos inviáveis por contradição;
              - mostrar claramente que todos os ramos viáveis convergem
                para o mesmo valor na célula alvo.

            ## 5.3 Exemplo concreto de relato textual de Consensus

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
            # 6. Técnica alvo desta chamada
            ============================================================

            Nesta chamada, os parâmetros são:

            - `candidate_type` = "{technique_code}"
            - `display_name`   = "{technique_name}"

            Você deve:

            - Usar toda a teoria acima como base conceitual;
            - Aplicar **apenas** a técnica "{technique_name}" (código "{technique_code}")
              na análise e na explanation.

            Regras específicas por código:

            - Se `candidate_type = "ZEROTH_LAYER_NAKED_SINGLES"`:
              - Objetivo:
                - encontrar uma célula `[i, j]` vazia com `C_plain([i, j]) = {{v}}`;
              - Explicação:
                - enfatizar a unicidade local pela célula;
                - listar explicitamente:
                  - os dígitos já presentes na linha *i*;
                  - os dígitos já presentes na coluna *j*;
                  - os dígitos já presentes no bloco de `[i, j]`;
                - mostrar que todos os outros dígitos são excluídos;
                - **não** usar suposições nem consensus.

            - Se `candidate_type = "ZEROTH_LAYER_HIDDEN_SINGLES"`:
              - Objetivo:
                - encontrar uma célula `[i, j]` e uma unidade `U` (linha, coluna ou bloco)
                  em que um dígito `v`:
                  - é candidato em `[i, j]` (v ∈ C_plain([i, j]));
                  - **não** é candidato em nenhuma outra célula vazia de `U`.
              - Explicação:
                - identificar claramente a unidade `U`;
                - listar as células vazias de `U` e seus `C_plain`;
                - mostrar que `v` só aparece em `[i, j]` dentro de `U`;
                - deixar claro que `[i, j]` pode ter outros candidatos locais;
                - **não** usar informação virtual nem consensus.

            - Se `candidate_type = "FIRST_LAYER_CONSENSUS"`:
              - Objetivo:
                - exibir um passo de consensus de primeira camada para uma
                  célula alvo `[i, j]`.
              - Explicação:
                - nomear explicitamente alguns ramos ("Ramo 1", "Ramo 2", ...);
                - para cada ramo, explicar:
                  - a suposição inicial (posição e dígito);
                  - as deduções por Naked/Hidden Singles;
                - indicar ramos inviáveis por contradição;
                - mostrar que todos os ramos viáveis forçam o mesmo dígito `v`
                  na célula alvo;
                - enfatizar que se trata de consensus de profundidade 1;
                - **não** usar técnicas mais profundas ou outras técnicas avançadas.

            ============================================================
            # 7. Protocolo de busca da ocorrência
            ============================================================

            1. Analise a grade e identifique **todas** as possíveis ocorrências
               válidas da técnica "{technique_name}".
            2. Se não existir nenhuma ocorrência válida:
               - a saída deve ser exatamente o objeto JSON de erro
                 especificado na Seção 8.2.
            3. Se houver uma ou mais ocorrências válidas:
               - escolha a célula alvo `[i, j]` com:
                 - menor índice de linha `i`;
                 - em caso de empate, menor índice de coluna `j`.
               - Use essa ocorrência para construir o JSON de sucesso.

            ============================================================
            # 8. Formato da RESPOSTA (apenas JSON, sem markdown)
            ============================================================

            Você deve responder **APENAS** com um objeto JSON válido, SEM texto fora
            dele, **SEM** cercas de código e **SEM** comentários.

            ## 8.1 Caso de sucesso (ocorrência encontrada)

            Formato exato (tipos e chaves):

            {{
              "value": 3,
              "position": [1, 2],
              "candidate_type": "{technique_code}",
              "explanation": "Relatório multilinha detalhado em português..."
            }}

            Onde:

            - `"value"`:
              - inteiro entre 1 e {n};
              - é o dígito forçado pela técnica na célula alvo `[i, j]`.

            - `"position"`:
              - lista com **exatamente dois** inteiros `[i, j]`, 0-based;
              - `0 ≤ i < {n}`, `0 ≤ j < {n}`.

            - `"candidate_type"`:
              - string **exatamente** "{technique_code}".
              - **Não** invente outro valor, **não** use descrição textual.

            - `"explanation"`:
              - texto em **português** (pt-BR), possivelmente multilinha;
              - sem cercas de código;
              - descrevendo o raciocínio completo:
                - identificação da célula alvo `[i, j]` e do valor `"value"`;
                - descrição dos conjuntos relevantes:
                  - C_plain([i, j]);
                  - e, se aplicável, os candidatos nas outras células
                    da unidade (linha/coluna/bloco);
                - para Consensus:
                  - descrição dos ramos, suposições, deduções por singles,
                    ramos inviáveis e conclusão de consenso.

            ## 8.2 Caso de ausência de ocorrência

            Se, após analisar cuidadosamente a grade com base em todas as definições,
            você concluir que **não existe nenhuma ocorrência válida** da técnica
            "{technique_name}", responda **apenas** com:

            {{"error": "No results found"}}

            - Chave `"error"` obrigatória;
            - valor deve ser exatamente a string `"No results found"`.

            ============================================================
            # 9. Restrições globais e modos de falha a evitar
            ============================================================

            - **NUNCA**:
              - escreva ``` ou qualquer tipo de cerca de código;
              - escreva texto fora do objeto JSON;
              - use valores especiais fora do JSON padrão
                (sem `NaN`, `Infinity`, `-Infinity`, `None`);
              - use `"candidate_type"` diferente de "{technique_code}" em caso de sucesso.

            - Se você perceber que:
              - precisa misturar técnicas diferentes para justificar o passo, ou
              - não consegue garantir que o passo é uma aplicação correta e pura
                da técnica alvo,
              então **considere que não há ocorrência válida** e responda com:

              {{"error": "No results found"}}

            - Linguagem:
              - a `explanation` deve ser sempre em **português (Brasil)**.

            ============================================================
            # 10. Checklist mental final (execute em silêncio)
            ============================================================

            Antes de emitir a saída, verifique mentalmente:

            - [ ] A técnica usada na explanation é estritamente "{technique_name}"?
            - [ ] Em caso de sucesso, escolhi a ocorrência com menor `i`
                  e, em empate, menor `j`?
            - [ ] A célula alvo está vazia na grade original?
            - [ ] `"value"` está em `{{1, ..., {n}}}`?
            - [ ] `"position"` é uma lista `[i, j]` com inteiros 0-based válidos?
            - [ ] `"candidate_type"` é exatamente "{technique_code}"?
            - [ ] A explanation está coerente com:
                  - single candidate principle (para Naked/Hidden) e/ou
                  - consensus principle (para Consensus),
                    na profundidade correta?
            - [ ] Não usei ``` nem texto fora do objeto JSON?
            - [ ] Em caso de ausência de ocorrência, respondi exatamente
                  `{{"error": "No results found"}}`?

            Agora, faça todo o raciocínio necessário **internamente** e, por fim,
            produza **APENAS** o objeto JSON final, sem qualquer outro texto.
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
