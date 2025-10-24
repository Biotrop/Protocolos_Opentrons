# 🧬 Protocolo Opentrons: Normalização e Diluição de Amostras de DNA

Este protocolo Opentrons automatiza a **normalização de até 96 amostras de DNA**. Ele lê automaticamente o arquivo de concentração mais recente gerado por um Qubit (ou similar), calcula os volumes de DNA e diluente necessários para atingir uma concentração alvo e mapeia as amostras de entrada (S1-S96) para posições específicas na placa final.

## 🎯 Configurações e Objetivos

| Parâmetro | Valor no Código | Descrição |
| :--- | :--- | :--- |
| **Concentração Alvo ($\text{C}_2$)** | **30.0 ng/µL** | A concentração final desejada para todas as amostras. |
| **Volume Final ($\text{V}_2$)** | **200 µL** | O volume final em cada poço da Placa Final. |
| **Pipeta Utilizada** | **P300 Single-Channel GEN2** | Instrumento necessário para volumes de até 300 µL. |

---

## 🌟 Funcionalidades Específicas

* **Leitura Automática de CSV:** Busca e utiliza o arquivo mais recente que corresponde ao padrão de nome **`QubitData*.csv`** dentro do diretório `/var/lib/jupyter/notebooks/`.
* **Cálculo de Normalização:** Utiliza a fórmula $\text{C}_1\text{V}_1 = \text{C}_2\text{V}_2$ para calcular os volumes de DNA e diluente. Se a concentração original já estiver abaixo do alvo, transfere o volume final de DNA (200 µL).
* **Mapeamento de Poços Customizado:** As amostras sequenciais (S1 a S96) são mapeadas de 4 racks de 24 tubos para posições específicas na placa final de 96 poços, seguindo a lógica implementada no script (detalhada abaixo).
* **Pipetagem Otimizada de Diluente:** Utiliza uma única ponteira para dispensar a água em todos os poços, minimizando o uso de consumíveis.
* **Transferência de DNA Segura:** Usa uma **nova ponteira** para cada amostra de DNA, eliminando o risco de contaminação cruzada.
* **Geração de Relatório de Saída:** Cria um arquivo **`saida.csv`** com todos os volumes, origens e destinos para documentação.

---

## ⚙️ Requisitos de Setup

### Hardware (Opentrons)

* **Robô:** Opentrons OT-2
* **Pipeta:** **P300 Single-Channel GEN2** (montada no lado **esquerdo**)

### Labware Necessário

| Posição (Slot) | Labware | Descrição |
| :---: | :--- | :--- |
| **1** | `opentrons_96_wellplate_200ul_pcr_full_skirt` | **Placa Final (96 poços - Destino)** |
| **2** | `opentrons_24_tuberack_nest_1.5ml_snapcap` | Placa de Amostras 1 (Tubos S1 - S24) |
| **3** | `opentrons_24_tuberack_nest_1.5ml_snapcap` | Placa de Amostras 2 (Tubos S25 - S48) |
| **5** | `opentrons_24_tuberack_nest_1.5ml_snapcap` | Placa de Amostras 3 (Tubos S49 - S72) |
| **6** | `opentrons_24_tuberack_nest_1.5ml_snapcap` | Placa de Amostras 4 (Tubos S73 - S96) |
| **4** | `usascientific_12_reservoir_22ml` | Reservatório de Água (Fonte do Diluente - **Poço H4/índice [7]**) |
| **8** | `opentrons_96_tiprack_300ul` | Rack de Ponteiras P300 (1) |
| **9** | `opentrons_96_tiprack_300ul` | Rack de Ponteiras P300 (2) |

---

## 💾 Arquivo de Entrada (`QubitData*.csv`)

O script buscará o arquivo mais recente chamado `QubitData*.csv` (ex: `QubitData_2025-10-24.csv`) no caminho `/var/lib/jupyter/notebooks/`.

### Colunas Essenciais

O script espera, no mínimo, as seguintes colunas no arquivo CSV (normalmente gerado por um leitor de concentração):

| Nome da Coluna (CSV) | Descrição |
| :---: | :--- |
| **`Sample Name`** | Nome da Amostra (deve seguir o formato **SXX**, ex: `S1`, `S25`). |
| **`Original Sample Conc.`** | Concentração da amostra (valor numérico em ng/µL). |

**Exemplo de Conteúdo do CSV:**

```csv
Sample Name,Original Sample Conc.,...
S1,85.0,...
S2,15.0,...
S3,30.0,...
...
