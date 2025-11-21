# Sudoku LLM Reasoning — Relatório explicativo

## Tema

Avaliar a capacidade de raciocínio de LLMs (Large Language Models) aplicando dois princípios humanos de resolução de Sudoku: o **Single Candidate Principle** e o **Consensus Principle**. O objetivo é gerar grades (grids) de Sudoku que permitam aplicar exclusivamente cada um desses princípios, grades onde ambos podem ser aplicados e grades onde nenhum dos dois se aplica; verificar formalmente a validade das soluções usando o **Z3** e ilustrar as instâncias com uma interface gráfica que salva as imagens geradas no banco de dados.

---

## Definições rápidas

* **Single Candidate Principle:** numa célula vazia, quando apenas um valor é compatível com as restrições das linhas, colunas e blocos — esse valor deve ser colocado.

* **Consensus Principle (Princípio do Consenso):** aplicado em nível de conjunto de células — quando, para um determinado dígito em uma unidade (linha/coluna/bloco), todas as possíveis posições coincidem com um subconjunto restrito de células que, combinado com informação de outras unidades, leva a uma dedução determinística.

---

## Objetivos do experimento

1. Gerar N grades onde apenas o **Single Candidate** é suficiente para avançar (e completar partes significativas do puzzle).
2. Gerar N grades onde apenas o **Consensus** é a técnica aplicável/principal para progredir.
3. Gerar N grades onde **ambos** os princípios podem ser aplicados.
4. Gerar N grades onde **nenhum** dos dois princípios é aplicável (exigem técnicas mais avançadas ou backtracking).

> Observação: escolhemos a mesma quantidade *N* para cada categoria para manter balanceamento estatístico na avaliação.

---

## Metodologia de geração

1. **Gerador procedural**: cria-se uma base de puzzles usando heurísticas controladas com parâmetros que favoreçam a presença ou ausência dos princípios. Exemplos de parâmetros:

   * densidade de pistas (quantas células já preenchidas)
   * concentração de pistas em certos blocos/linhas
   * posição de pistas que produzem muitos candidatos únicos

2. **Filtragem por detector de técnicas**: para cada grade gerada, aplica-se um motor de análise (um inferidor que computa candidatos por célula e identifica padrões) que testa se o Single Candidate é aplicável, se o Consensus é aplicável, ambos ou nenhum.

3. **Balanceamento**: repetir a geração até obter N instâncias por categoria.

---

## Verificação formal com Z3

Usamos o *SMT solver* Z3 para garantir que:

* a solução da grade é única;
* as deduções locais inferidas pelos princípios são logicamente válidas (i.e., a atribuição sugerida por um princípio não contradiz o modelo Z3);
* quando afirmamos que "nenhum dos dois princípios se aplica inicialmente", Z3 confirma que nenhuma atribuição imediata forçada existe sem assumir backtracking.

### Como modelamos o Sudoku no Z3:

* Variáveis: `cell_r_c` inteiras no intervalo 1..9 para cada linha `r` e coluna `c`.
* Restrições básicas: todos os valores em cada linha são distintos; em cada coluna são distintos; em cada bloco 3x3 são distintos.
* Pistas fixas: para cada célula com pista, `cell_r_c == value`.

### Verificações específicas:

* **Single Candidate**: para uma célula vazia `x`, construímos um modelo Z3 com restrições atuais e testamos a satisfatibilidade com a suposição `cell_x == v` para cada valor `v` que não foi eliminado por candidatos: se apenas um `v` tornar o sistema satisfatível, concluímos que `v` é single candidate. Procedimento implementado com chamadas de `solver.push()` / `solver.pop()` para eficiência.

* **Consensus**: modelamos conjunturas onde um dígito `d` tem posições possíveis limitadas em uma unidade; verificamos implicações lógicas entre essas posições usando consultas condicionais ao solver (por exemplo, forçar `d` fora de determinadas posições e verificar consequências). Em muitos casos isso equivale a checar implicações universais reduzidas a buscas satisfatíveis/insatisfatíveis pela forma padrão de usar Z3.

---

## Integração com interface gráfica e banco de dados

* **Geração de imagens**: para cada grid gerado (instância), renderizamos uma imagem PNG do tabuleiro com destaque nas células relevantes (por exemplo: células com single candidate em amarelo, células envolvidas em um consenso em azul).

* **Interface gráfica (GUI)**: desenvolvemos uma aplicação leve que permite ao usuário navegar pelas instâncias, ver os candidatos de cada célula e observar as marcações visuais que ilustram as técnicas aplicáveis.

* **Armazenamento**: as imagens geradas e metadados (categoria — Single/Consensus/Both/None, número de pistas, solução completa, log de verificação Z3) são salvos no banco de dados. A aplicação GUI busca os registros e exibe as imagens já processadas; as imagens também ficam disponíveis para exportação.

---

## Exemplo de fluxo (alto nível)

1. Gerador produz 10.000 variações; pipeline de análise filtra e classifica cada uma.
2. Para cada instância selecionada por categoria, rodamos verificações com Z3 para garantir consistência e unicidade (se necessário).
3. Renderizamos imagens e salvamos no banco com metadados.
4. Revisamos manualmente uma amostra para garantir qualidade das marcações visuais.

---

## Resultados esperados e utilização

* Dataset balanceado com exemplos claros para cada categoria — útil para avaliar LLMs: pedimos ao LLM explicar a próxima jogada e checamos se a explicação usa o princípio correto.
* Relatórios automatizados (por instância) com logs do Z3 provando a validade das deduções extraídas.

---

## Extensões possíveis

* Incluir técnicas adicionais e categorizar mais finamente.
* Gerar contraprovas formais (certificados) a partir do Z3 para cada inferência.
* Exportar um dataset pronto para treinamento/avaliação de LLMs.

---

## Conclusão

Este pipeline combina geração controlada, verificação formal via Z3 e visualização em GUI para produzir um conjunto de instâncias de Sudoku adequadas para avaliar raciocínio de LLMs com foco nos princípios Single Candidate e Consensus. A presença dos artefatos visuais salvos no banco facilita a inspeção humana e serve como material para apresentações e análises qualitativas.

