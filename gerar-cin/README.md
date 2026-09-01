# 🪪 Gerador de Amostras de CIN (Carteira de Identidade Nacional)

Ferramenta visual *client-side* (100% offline) para geração dinâmica de amostras sintéticas e realistas da **Nova Carteira de Identidade Nacional (CIN - Decreto nº 10.977/2022)** para testes do motor de OCR, validação de layouts e fluxos de upload do **DOC_Intelligence**.

---

## 🎯 Casos de Uso no Projeto

1. **Geração de Dados de Teste para o Pipeline OCR:**
   - Criação rápida de imagens nítidas (frente e verso) ou PDFs multipágina com dados randômicos brasileiros válidos.
   - Teste de extração de campos (Nome, CPF, Data de Nascimento, Naturalidade, Validade, Órgão Emissor).
2. **Validação do Algoritmo Módulo 11 (RN-04):**
   - Os CPFs gerados na ferramenta possuem dígitos verificadores matematicamente válidos calculados por Módulo 11, permitindo testar o fluxo de aprovação automática (`READY`) versus falhas de checksum.
3. **Testes de Rasterização e Resolução (RN-06):**
   - Suporte a exportação em diferentes resoluções: **1x Padrão (856x540)**, **2x HD (1712x1080)** e **3x Full HD (2568x1620)**.
4. **Testes do Portal Mobile e Conferência Humana:**
   - Amostras para testar o enquadramento da câmera (`CameraModalComponent`) e a tela de revisão *Split-Screen* (`DocumentReviewComponent`).

---

## 🚀 Como Usar

Não é necessário instalar nenhum servidor ou dependência backend:

1. Acesse o diretório `gerar-cin/`.
2. Dê um duplo-clique no arquivo **`index.html`** (ou abra diretamente no navegador: Google Chrome, Microsoft Edge, Firefox, etc.).
3. Configure as opções no cabeçalho:
   * **Qtd:** Quantidade de cartões a gerar (de 1 a 50).
   * **Formato:** PNG, JPG ou WEBP.
   * **Resolução:** 1x (Padrão), 2x (HD) ou 3x (Full HD).
4. Clique em:
   * **🔄 Gerar Novos Dados:** Recalcula nomes, CPFs, datas e QR Codes randômicos.
   * **⬇️ Baixar Frente / Baixar Verso:** Download individual do cartão em exibição.
   * **📦 Baixar Tudo (.ZIP):** Empacota todas as frentes e versos em um arquivo ZIP.
   * **📄 Exportar em PDF Único:** Gera um documento PDF com todas as identidades (frente e verso por página).

---

## 🧩 Recursos e Tecnologias Utilizadas

* **HTML5 Canvas & `html2canvas`:** Renderização e captura dos cartões em alta fidelidade.
* **`jsPDF`:** Geração de documentos PDF vetoriais/rasterizados prontos para teste de rasterização 300 DPI.
* **`JSZip` & `FileSaver.js`:** Compressão e download em lote no navegador.
* **`qrcodejs`:** Geração de QR Code dinâmico no padrão Gov.br da CIN.
* **Tailwind CSS:** Layout responsivo e moderno.
* **Tipografia e Assinatura:** Fontes estilizadas para emular a assinatura manuscrita do titular.

---

## 📁 Estrutura de Arquivos

```text
gerar-cin/
├── index.html         # Aplicação web completa (UI + Gerador + Exportadores)
├── assets.js          # Imagens base e templates embutidos em Base64
├── img (1).jfif       # Imagem base de alta fidelidade da Frente
├── img (2).jfif       # Imagem base de alta fidelidade do Verso
├── modelo_padrao.jpg  # Modelo de referência de layout
└── README.md          # Este guia de documentação
```
