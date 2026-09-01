# Guia de Arquitetura e IA para API de OCR em FastAPI

Este documento detalha as práticas arquiteturais e as diretrizes (skills) para configurar um agente de IA visando a construção de uma API de OCR flexível em FastAPI. O objetivo principal é garantir que a aplicação possa trocar ou adicionar motores de OCR (Tesseract, AWS Textract, Google Vision, etc.) para diferentes tipos de documentos (PDF, JPEG, PNG) sem afetar as camadas superiores do código, utilizando as melhores práticas da Orientação a Objetos.

---

## 1. Padrões de Projeto Recomendados

Para alcançar a flexibilidade desejada, a arquitetura exigida do agente deve ser baseada nos seguintes padrões de projeto:

### 1.1 O Padrão Strategy (Padrão Principal)
O padrão de projeto Strategy é a peça central desta arquitetura.
*   **Definição:** O padrão de projeto Strategy define uma família de algoritmos, encapsula cada um deles e os torna intercambiáveis[cite: 1]. 
*   **Aplicação no OCR:** A interface principal (`InterfaceOCR`) exigirá um método comum (ex: `extrair_dados()`). Cada motor de OCR (ex: `TesseractOCR`, `AwsTextractOCR`) será implementado como uma estratégia separada que implementa essa interface.
*   **Vantagem:** Na arquitetura principal, o contexto delega o trabalho para o objeto estratégia ao invés de executá-lo por conta própria[cite: 1]. Isso permite isolar os detalhes de implementação de um algoritmo do código que usa ele[cite: 1]. Além disso, permite trocar algoritmos usados dentro de um objeto durante a execução[cite: 1].

### 1.2 O Padrão Adapter (Padrão de Apoio)
Como lidaremos com bibliotecas externas de diferentes fornecedores, elas terão interfaces, retornos e métodos imcompatíveis.
*   **Definição:** O Adapter permite a colaboração de objetos de interfaces incompatíveis[cite: 1].
*   **Aplicação no OCR:** As classes de estratégia atuarão como adaptadores. Elas atuarão como um tradutor, onde a adaptação acontece dentro dos métodos sobrescritos[cite: 1]. 
*   **Vantagem:** Possibilita introduzir novos tipos de adaptadores no programa sem quebrar o código cliente existente[cite: 1].

---

## 2. Arquitetura em Camadas (FastAPI + Injeção de Dependência)

Para implementar os padrões acima no FastAPI, recomenda-se a seguinte estrutura em camadas:

1.  **Camada de Interfaces / Abstração:** Define o contrato obrigatório. A regra de ouro é garantir que o código dependa de abstrações, não de classes concretas[cite: 1].
2.  **Camada de Implementações (Estratégias / Adaptadores):** Contém as classes concretas. O adaptador recebe chamadas do cliente através da interface do adaptador e as traduz em chamadas para o objeto encobrido do serviço em um formato que ele possa entender[cite: 1].
3.  **Camada de Regra de Negócio (Contexto):** Contém o serviço principal. Desta forma, o contexto se torna independente das estratégias concretas, permitindo adicionar novos algoritmos ou modificar os existentes sem modificar o código do contexto[cite: 1].
4.  **Camada de API (Rotas FastAPI):** Utiliza o recurso `Depends()` do FastAPI para injetar dinamicamente qual implementação de OCR será passada ao Contexto.

---

## 3. Skills Sistêmicas para o Agente de IA

Para configurar o agente (Cursor, Copilot, CrewAI), as seguintes regras devem ser adicionadas ao prompt do sistema ou `.cursorrules`:

### Skill 1: Domínio do Princípio de Inversão de Dependência (DIP)
*   **Diretriz para a IA:** O agente deve aplicar estritamente a Injeção de Dependência do FastAPI (`Depends()`).
*   **Regra de Ouro:** O agente deve projetar a aplicação para garantir que o código dependa de abstrações, não de classes concretas[cite: 1]. As rotas (alto nível) nunca devem instanciar diretamente as bibliotecas de OCR (baixo nível).

### Skill 2: Especialista no Padrão Strategy
*   **Diretriz para a IA:** Todo motor de processamento deve ser visto como um algoritmo independente.
*   **Regra de Ouro:** Exija que a IA defina uma família de algoritmos, coloque-os em classes separadas e faça os objetos deles intercambiáveis[cite: 1]. O serviço principal (contexto) apenas delega o trabalho para um objeto estratégia ao invés de executá-lo por conta própria[cite: 1].

### Skill 3: Aplicação do Padrão Adapter
*   **Diretriz para a IA:** Serviços de terceiros nunca devem ser usados diretamente pelo código de negócio.
*   **Regra de Ouro:** O agente deve desenhar adaptadores para permitir a colaboração de objetos de interfaces incompatíveis[cite: 1]. O agente deve envolver a biblioteca externa em um adaptador para introduzir novos tipos de adaptadores no programa sem quebrar o código cliente existente[cite: 1].

### Skill 4: Guardião do Princípio Aberto/Fechado (OCP)
*   **Diretriz para a IA:** O agente deve projetar sistemas prevendo futuras modificações e novas adições de OCRs.
*   **Regra de Ouro:** O agente deve garantir que a classe possa ser aberta para extensão e fechada para modificação ao mesmo tempo[cite: 1]. O código deve encapsular o que varia em módulos independentes, protegendo o resto do código de efeitos adversos[cite: 1].