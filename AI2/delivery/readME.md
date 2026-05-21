# LIGHTNING ANOMALY - EV Charger Anomaly Detection Simulator

Trabalho realizado por:
- Nádia Silva, up202350685
- Tiago Valente, up202306131
- Rui Andrade, up202306128

---

## Descrição

Implementação de um simulador de carregamentos de veículos elétricos com deteção automática de anomalias utilizando algoritmos de Machine Learning.

O sistema gera dados sintéticos de carregamentos, injeta diferentes tipos de anomalias e executa modelos de deteção para identificar comportamentos anómalos em carregadores elétricos.

A aplicação inclui uma interface web interativa desenvolvida com Flask.

---

## Objetivos do Projeto

- Simular sessões de carregamento de veículos elétricos
- Gerar dados sintéticos realistas
- Injetar diferentes tipos de anomalias elétricas
- Aplicar algoritmos de deteção de anomalias
- Agrupar padrões anómalos
- Avaliar o desempenho dos modelos de Machine Learning

---

## Requisitos

- Python 3.x
- Anaconda (recomendado)
- Bibliotecas:
  - Flask
  - pandas
  - numpy
  - scikit-learn
  - matplotlib
  - openpyxl

---

## Como executar

1. Abra o **VS Code** através do **Anaconda Navigator**
2. Abra a pasta do projeto no VS Code
3. Abra o terminal integrado (View → Terminal ou Ctrl + `)
4. Entre na pasta `webapp`:

```bash
cd webapp
```

5. Execute o seguinte comando:

```bash
python simulator.py
```

ou

```bash
python3 simulator.py
```

6. No terminal irá aparecer um link semelhante a:

```text
http://127.0.0.1:5000
```

7. Abra esse link no navegador para utilizar a aplicação.

---

## Como usar o programa

1. Defina os parâmetros da simulação:
   - Número de carregadores
   - Número de sessões por carregador
   - Taxa de anomalias

2. Escolha os tipos de anomalias a injetar nos dados

3. Inicie a simulação

4. O sistema:
   - Gera dados sintéticos para treino e dados de inferência para teste
   - Treina o modelo nos dados de treino
   - Executa o modelo sobre os dados de teste
   - Demonstra as métricas obtidas de teste

5. No final são apresentadas:
   - Métricas de desempenho
   - Número de anomalias detetadas
   - Taxa de deteção de anomalias
   - Matriz de confusão
   - Estatísticas dos carregadores
   - Agrupamento de anomalias com K-Means
   - Random Forest Feature Importance
   - Threshold Selection

---

## Geração de Dados Sintéticos

O sistema gera dados sintéticos de telemetria de carregadores de veículos elétricos, simulando sessões de carregamento realistas com base em valores estatísticos derivados de dados reais. Anomalias são introduzidas nos dados e marcadas para o treino do modelo supervisionado. Adicionalmente, em dados de infêrencia, é feita uma aproximação a dados reais através de barulho.

Cada sessão inclui:
- Corrente elétrica por fase
- Tensões elétricas
- Potência consumida
- Potência oferecida
- Energia acumulada
- Duração da sessão
- Consumo verde
- Estado do carregador

Os dados são gerados automaticamente durante a simulação.

---

## Configuração da Simulação

O utilizador pode configurar:

- Número de carregadores
- Número de sessões por carregador
- Taxa de anomalias
- Tipos de anomalias a injetar

---

## Funcionalidades Implementadas

| Funcionalidade | Descrição |
|---|---|
| Geração de dados sintéticos | Criação automática de sessões de carregamento |
| Injeção de anomalias | Simulação de falhas elétricas e inconsistências |
| Random Forest | Deteção automática de anomalias |
| K-Means | Agrupamento de anomalias |
| Interface Web | Visualização e execução da simulação |
| Métricas de avaliação | Accuracy, Precision, Recall, F1-Score, Detection Rate, MCC, Balanced ACC, PR AUC, ROC AUC |
| Exportação para Excel | Armazenamento automático dos dados gerados |

---

## Tipos de Anomalias

O sistema consegue simular diferentes tipos de problemas em carregadores elétricos:

| Anomalia | Descrição |
|---|---|
| voltage_out_of_range | Tensões fora do intervalo 220–240 V |
| phase_voltage_diff | Diferença superior a 10 V entre fases |
| current_zero_phase | Uma fase com corrente nula |
| current_imbalance | Desequilíbrio superior a 2 A entre fases |
| power_offered_diff | Diferença superior a 2 kW entre potência oferecida e consumida |
| power_consistency | Inconsistência entre potência calculada e potência medida |

---

## Estrutura dos Dados

Os dados gerados incluem atributos como:

- `ChargePointId`
- `ConnectorId`
- `Timestamp`
- `Current.Import_L1`
- `Current.Import_L2`
- `Current.Import_L3`
- `Voltage_L1`
- `Voltage_L2`
- `Voltage_L3`
- `Power.Active.Import`
- `Power.Offered`
- `Energy.Active.Import.Register`
- `GreenConsumption`

---

## Algoritmos Utilizados

| Algoritmo | Objetivo |
|---|---|
| Random Forest | Deteção de anomalias supervisionada |
| K-Means | Agrupamento de anomalias |
| Silhouette Score | Avaliação da qualidade dos clusters |
| Data Imputation (SimpleImputer) | Preencher os valores vazios (NaN) com a média (mean) de cada coluna respetiva |

---

## Métricas Avaliadas

O sistema apresenta automaticamente métricas de desempenho dos modelos utilizados:

- Accuracy: proporção de previsões corretas no total de casos avaliados
- Precisionn: das instâncias classificadas como anomalia, quantas eram realmente anomalias (ajuda a reduzir falsos alarmes)
- Recall: das anomalias reais, quantas foram corretamente detetadas (evita falsos negativos)
- F1-Score: média harmónica entre precision e recall, útil em problemas com classes desbalanceadas como este (poucas anomalias face a dados normais)
- Matriz de Confusão: tabela que mostra acertos e erros do modelo (verdadeiros positivos, falsos positivos, verdadeiros negativos e falsos negativos)
- Balanced ACC (Balanced Accuracy): calcula a média do recall (sensibilidade) obtido em cada classe, avalia validade do modelo versus marcar tudo como normal
- MCC (Matthews Correlation Coefficient): só produz uma pontuação alta se o modelo obtiver bons resultados em todas as quatro categorias da matriz de confusão
- ROC AUC (Area Under the Receiver Operating Characteristic Curve): indica a capacidade global do modelo em distinguir entre sessões de carregamento normais e anomalias através de todos os limiares de classificação possíveis
- PR AUC (Area Under the Precision-Recall Curve): resume a curva que cruza a Precisão com o Recall; foca-se diretamente no desempenho do modelo face às anomalias reais, sem ser mascarada pelo grande volume de dados normais

---

## Exportação de Dados

Os dados gerados são automaticamente exportados para um ficheiro Excel (`.xlsx`) para posterior análise e execução dos modelos de deteção de anomalias.

---

## Estrutura Geral do Projeto

```text
project/
│
├── webapp/
│   ├── simulator.py
│   ├── templates/index.html
│   ├── static/
│
├── data/
│   ├── generator.py
│   ├── generator_testing.py
│   ├── all_chargers_pivoted.xlsx
│   ├── all_chargers_training_labeled.xlsx
│
├── model.py
└── README.md
```