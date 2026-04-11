# Potion Sort - Water Sort Puzzle

Trabalho realizado por:
- Nádia Silva, up202350685
- Tiago Valente, up202306131
- Rui Andrade, up202306128

---

## Descrição

Implementação do puzzle **Water Sort** (Potion Sort) em Python, com interface gráfica e solver automático baseado em algoritmos de pesquisa em espaço de estados. O objetivo do jogo é ordenar as cores de forma a que cada tubo contenha apenas uma cor ou esteja vazio.

---

## Requisitos

- Python 3.x
- Anaconda (recomendado)
- Biblioteca `pygame` (para a interface gráfica)

Para instalar o pygame, escreva no terminal:

`pip install pygame`

---

## Como executar

1. Abra o **VS Code** através do **Anaconda Navigator**
2. Abra a pasta do projeto no VS Code
3. Abra o terminal integrado (View → Terminal ou Ctrl + `)
4. Escreva o seguinte comando:

`python main.py`

---

## Como usar o programa

**Menu principal:**
- **Play** - inicia o jogo no modo manual
- **Model** - corre o solver automático
- **Exit** - sai do programa

---

### Modo Play

1. Selecione o nível de dificuldade: **Easy**, **Medium** ou **Hard**
2. O jogo é iniciado com uma configuração aleatória de tubos
3. Clique num tubo de origem e depois num tubo de destino para transferir o líquido
4. **Reset** - reinicia o nível atual
5. **Hint** - sugere e executa automaticamente o próximo movimento ótimo com base no A\*. As dicas acumulam-se ao longo dos níveis e são renovadas a cada novo jogo
6. Ao completar o nível, clique em **Next** para avançar para um novo jogo gerado automaticamente

---

### Modo Model (Solver)

1. Selecione o nível de dificuldade: **Easy**, **Medium** ou **Hard**
2. Selecione o algoritmo a utilizar: BFS, DFS, UCS, A\*, Weighted A\* ou Greedy
3. Para algoritmos informados (A\*, Weighted A\*, Greedy), selecione a heurística: h1, h2 ou h3
4. O solver resolve o puzzle automaticamente
5. No final, são apresentadas as estatísticas da execução: número de movimentos, nós expandidos, nós gerados e tempo de execução
6. Escolha **Replay** para repetir ou volte ao menu principal

---

## Algoritmos implementados

| Algoritmo | Heurística | Garante ótimo |
|---|---|---|
| BFS | — | Sim |
| DFS | — | Não |
| UCS | — | Sim |
| A\* | h1, h2, h3 | Sim (h1/h2), Não (h3) |
| Weighted A\* (w=2) | h1, h2, h3 | Não garantido |
| Greedy | h1, h2, h3 | Não |


**Níveis de dificuldade:**
| Nível | Tubos | Cores |
|---|---|---|
| Easy | 6 | 4 |
| Medium | 9 | 7 |
| Hard | 12 | 10 |