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
            ### Técnica alvo — Naked Singles (profundidade 0)

            Ideia central:
            - Naked Single é um caso da single candidate principle: para a célula alvo [i,j] existe
              exatamente um dígito permitido que não é proibido pela linha, pela coluna e pelo bloco.
              O valor da célula é forçado apenas pela informação atual da grade, sem usar suposições.

            Definição operacional para Sudoku:
            1. Considere a célula alvo [i,j] associada ao par (position) da sua saída.
            2. Considere o conjunto DIGITOS_PERMITIDOS da grade (1..4 ou 1..9, conforme o tamanho).
            3. Calcule:
               - L = conjunto de dígitos não nulos presentes na LINHA i.
               - C = conjunto de dígitos não nulos presentes na COLUNA j.
               - B = conjunto de dígitos não nulos presentes no BLOCO que contém [i,j].
            4. Defina o conjunto de candidatos locais:
               - Candidatos([i,j]) = DIGITOS_PERMITIDOS \ (L ∪ C ∪ B).
            5. Trata-se de um Naked Single **somente se** Candidatos([i,j]) tiver exatamente
               um elemento, e esse elemento for igual a value.

            O que a explanation DEVE conter:
            - Uma linha de abertura do tipo: "Naked Single na célula [i,j] com valor value".
            - A descrição explícita dos conjuntos L, C e B:
              - "LINHA i: ..."  (valores distintos e ordenados da linha).
              - "COLUNA j: ..." (valores distintos e ordenados da coluna).
              - "BLOCO (b_i,b_j): ..." (valores distintos e ordenados do bloco).
            - O cálculo textual dos candidatos, por exemplo:
              - "Candidatos([i,j]) = DIGITOS_PERMITIDOS \ (L ∪ C ∪ B) = {value}".
            - Uma mini-matriz (linha, coluna ou bloco) com 0 nas casas vazias para ilustrar o recorte.
            - Uma frase final do tipo:
              - "Como só resta o candidato value para [i,j], esta célula é um Naked Single."

            Restrições de raciocínio (obrigatórias):
            - Use apenas informação atual: valores já presentes na grade.
            - Não crie suposições do tipo "se tal célula fosse k..." (isso seria informação virtual).
            - Não use outras técnicas além de Naked Singles:
              - não use Hidden Singles, pares/trincas, X-Wing, nem nenhum padrão avançado.
            - Não reinterprete este caso como Hidden Single:
              - o critério aqui é "a célula tem um único candidato local".
        """).strip(),
        SudokuSimplifiedCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES: textwrap.dedent("""
            ### Técnica alvo — Hidden Singles (profundidade 0)

            Ideia central:
            - Hidden Single também é um uso da single candidate principle, mas agora o "único"
              é relativo a uma UNIDADE (linha, coluna ou bloco), e não à célula isolada.
              O dígito value aparece como candidato viável em exatamente uma célula da unidade escolhida.

            Definição operacional para Sudoku:
            1. Escolha uma única unidade onde o Hidden Single será provado:
               - ou uma LINHA específica,
               - ou uma COLUNA específica,
               - ou um BLOCO específico.
            2. Dentro dessa unidade, considere todas as células vazias (com 0 na grade).
            3. Para cada uma dessas células, defina o conjunto de candidatos locais
               da mesma forma que em Naked Singles:
               - candidatos([r,c]) = DIGITOS_PERMITIDOS \ (valores da linha r ∪ coluna c ∪ bloco de [r,c]).
            4. Concentre-se em um dígito value.
               - Liste todas as posições da unidade em que value pertence ao conjunto de candidatos locais.
            5. É Hidden Single **somente se** dentro da unidade escolhida o dígito value aparece
               como candidato em exatamente uma posição, que será [i,j].

            O que a explanation DEVE conter:
            - Um enunciado claro da unidade usada, por exemplo:
              - "Hidden Single do dígito value na LINHA i" ou "no BLOCO (b_i,b_j)".
            - A lista das células da unidade com seus candidatos que contêm value, por exemplo:
              - "Células da LINHA i onde value é candidato: [ [i,c1], [i,c2], ... ]".
            - Para cada célula alternativa que não seja [i,j], explique por que value é inviável:
              - conflito com algum valor já presente na linha, coluna ou bloco correspondente.
            - Uma mini-representação da unidade (linha completa, coluna completa ou bloco),
              usando 0 nas casas vazias.
            - Uma frase final explícita, do tipo:
              - "Dentro da UNIDADE escolhida, value só pode ir em [i,j]; logo é um Hidden Single."

            Restrições de raciocínio (obrigatórias):
            - Use somente informação atual (valores já escritos na grade).
            - Não faça ramificações nem suposições do tipo "se value estiver aqui/ali...".
              Isso é reservado para Consensus.
            - Não use técnicas globais ou avançadas (nada de pares/trincas, blocos interagindo etc.).
            - Não transforme este caso em Naked Single:
              - a célula [i,j] pode ter vários candidatos locais,
                o que é único é a posição de value dentro da unidade.
        """).strip(),
        SudokuSimplifiedCandidateType.FIRST_LAYER_CONSENSUS: textwrap.dedent("""
            ### Técnica alvo — Consensus Principle (profundidade 1)

            Ideia central:
            - Consensus usa **informação virtual**: você abre alguns RAMOS de suposições
              mutuamente exclusivas e exaustivas, analisa as consequências de cada ramo
              usando apenas técnicas rasas (Naked/Hidden Singles), e observa que todos
              os ramos viáveis concordam na mesma conclusão para a célula alvo [i,j] = value.
            - Em termos de depth-bounded reasoning, Naked e Hidden Singles pertencem
              à camada de profundidade 0 (apenas informação atual), enquanto Consensus
              é a primeira camada que exige usar informação virtual para simular estados
              alternativos da grade.

            Estrutura geral de um passo de Consensus (profundidade 1):
            1. Escolha um pequeno conjunto de alternativas mutuamente exclusivas e exaustivas, por exemplo:
               - diferentes possíveis posições de um mesmo dígito em uma região (linha/coluna/bloco); ou
               - diferentes valores candidatos para uma única célula problemática.
            2. Para cada alternativa A_k:
               - abra um RAMO rotulado (por exemplo, "Ramo A", "Ramo B", ...);
               - faça uma suposição explícita do tipo "Se [r,c] = v então ...";
               - a partir daí, aplique apenas deduções determinísticas:
                 Naked Singles e Hidden Singles repetidamente, respeitando as regras de Sudoku.
               - registre as deduções principais em formato de log.
            3. Para cada ramo:
               - se as deduções levarem a uma contradição (dois dígitos iguais na mesma unidade,
                 célula sem candidato etc.), marque o ramo como inviável (ramo morto).
               - caso contrário, identifique o conjunto de candidatos possível para a célula alvo [i,j].
            4. Conclusão por Consensus:
               - Se todos os ramos viáveis forçarem [i,j] = value (ou se todos os ramos alternativos
                 que colocam outro valor em [i,j] forem inviáveis), conclua que, independentemente
                 de qual ramo for o verdadeiro, a única escolha compatível é [i,j] = value.

            O que a explanation DEVE conter:
            - Identificação clara da célula alvo [i,j] e do valor value.
            - Nomeação explícita dos ramos (Ramo A, Ramo B, ...), com:
              - a suposição inicial de cada ramo;
              - uma lista das principais deduções de Naked/Hidden Singles obtidas nesse ramo,
                cada uma em uma linha ("Dedução single: (r,c) = v", etc.);
              - indicação de contradição, se ela aparecer, ou do conjunto de candidatos resultante
                para [i,j] nesse ramo.
            - Uma seção de síntese do tipo:
              - "Resumo dos ramos viáveis: em todos eles a célula [i,j] fica forçada a value."
            - Uma conclusão final indicando explicitamente que isto caracteriza um passo de Consensus.

            Exemplo de log de Consensus (FORMATO APENAS; NÃO copie os números)
            (As cercas de código abaixo servem só para o exemplo; **não** use cercas de código
            na explanation da sua resposta final.)

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

            Restrições de raciocínio (obrigatórias):
            - Profundidade 1 apenas:
              - você pode abrir uma camada de RAMOS, mas **não** pode aninhar novos ramos
                dentro de um ramo já aberto.
            - Dentro de cada ramo, use apenas:
              - Naked Singles;
              - Hidden Singles;
              - consequências diretas das regras básicas de Sudoku (linha/coluna/bloco).
            - Não utilize técnicas mais avançadas (fish, cadeias lógicas longas, etc.).
            - Fora de Consensus, não conclua nada usando suposições:
              - toda suposição deve estar claramente localizada em um ramo,
                e descartada ao final quando você resume apenas o que é comum a todos os ramos viáveis.
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

            Nesta tarefa você deve localizar exatamente **uma** ocorrência da técnica
            "{candidate_type.display_name}" e explicá-la em detalhes, obedecendo às restrições abaixo.

            - Se a técnica pedida for "Naked Singles", seu raciocínio deve usar apenas Naked Singles.
            - Se a técnica pedida for "Hidden Singles", seu raciocínio deve usar apenas Hidden Singles.
            - Se a técnica pedida for "Consensus Principle (profundidade 1)":
              - você pode abrir ramos de suposição de profundidade 1;
              - dentro de cada ramo, só pode usar Naked/Hidden Singles e consequências imediatas
                das regras de Sudoku (linha/coluna/bloco).

            ### Grade e notação

            - O dígito 0 representa uma célula vazia.
            - A grade fornecida é o estado atual do jogo; você não deve modificá-la diretamente.
            - Os dígitos permitidos são:
              - 1 a 4 se a grade for 4×4;
              - 1 a 9 se a grade for 9×9.

            Sudoku (0 = vazio):

            {sudoku}

            ### Tarefa

            1. Verificar se existe pelo menos uma ocorrência de {candidate_type.display_name}.
            2. Se houver várias, escolher apenas uma, obedecendo:
               - menor índice de linha i;
               - em empate, menor índice de coluna j.
            3. Retornar:
               - um único objeto JSON descrevendo a ocorrência escolhida; ou
               - o objeto de erro padronizado, se nenhuma ocorrência existir.

            ### Regras gerais de saída (OBRIGATÓRIO)

            1. Responda com apenas JSON válido:
               - sem cercas de código (sem ```),
               - sem texto antes ou depois,
               - sem comentários.
            2. Use indexação zero-based: "position" = [i, j].
            3. NÃO inclua nenhum outro campo além dos especificados.
            4. Não invente dados:
               - toda afirmação deve ser coerente com a grade fornecida.
            5. Use apenas tipos JSON padrão:
               - não use NaN, Infinity, -Infinity, None.

            ### Formato em caso de sucesso

            Quando existir pelo menos uma ocorrência válida de {candidate_type.display_name},
            retorne exatamente um objeto JSON com estes 4 campos na raiz:

            {{
              "value": 3,
              "position": [1, 2],
              "candidate_type": "{candidate_type.value}",
              "explanation": "Relatório multilinha detalhado..."
            }}

            (O exemplo acima é apenas estrutural.)

            ### Formato quando não houver ocorrência

            Se não existir nenhuma ocorrência desta técnica na grade, retorne:

            {{"error": "No results found"}}

            ### Regras específicas da técnica

            Leia e siga cuidadosamente a descrição da técnica abaixo.
            Ela explica precisamente o que conta como um caso válido de {candidate_type.display_name}
            e quais passos de raciocínio são permitidos.

            {self.__PROMPT_TEMPLATES[candidate_type]}

            ### Checklist final

            - Há apenas um objeto JSON na saída (sem texto extra)?
            - Em caso de sucesso, os campos são exatamente:
              "value", "position", "candidate_type", "explanation"?
            - "position" contém dois inteiros [i, j] com indexação zero-based?
            - "candidate_type" é exatamente "{candidate_type.value}"?
            - A explanation mostra apenas a técnica pedida, respeitando as restrições acima?

            Agora gere apenas o objeto JSON final, seguindo todas as instruções.
        """)

        response: str = self.__llm.generate_content(prompt).text or ""
        payload: Dict[str, Any] = self.__get_inference_candidate_payload(response, candidate_type=candidate_type)
        return SudokuInferenceCandidate(**payload) if not "error" in payload else None

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
