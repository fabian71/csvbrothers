# Csvbrothers - Automatizador de Metadados para Mídia de Stock

O Csvbrothers é um script em Python desenvolvido para automatizar e otimizar o processo de criação de metadados para fotos e vídeos destinados a bancos de imagem (stock). Utilizando a IA do Google (Gemini), o script analisa o conteúdo de cada arquivo e gera automaticamente um título, uma descrição, palavras-chave relevantes e atribui uma categoria apropriada.

## Funcionalidades Principais

- **Análise Inteligente:** Utiliza a API do Google Gemini para interpretar o conteúdo visual de imagens e vídeos.
- **Geração Automática de Metadados:** Cria automaticamente:
    - **Título:** Um título conciso e descritivo (aprox. 75 caracteres).
    - **Descrição:** Uma frase que expande o título (até 160 caracteres).
    - **Palavras-chave:** Entre 40 e 49 palavras-chave, ordenadas por relevância.
    - **Categoria:** Seleciona a categoria mais adequada a partir de uma lista pré-definida (padrão Adobe Stock).
- **Seleção de Pasta com Interface Gráfica:** Abre uma janela do Windows para que você possa selecionar facilmente a pasta com os arquivos que deseja processar.
- **Saída em CSV:** Salva todos os metadados gerados em um único arquivo `.csv`, nomeado com a data do processamento (ex: `metadata_2025-07-12.csv`).
- **Controle de Arquivos Processados:** Mantém um registro (`processed_files.txt`) para não processar o mesmo arquivo duas vezes, permitindo que você continue o trabalho de onde parou.
- **Armazenamento Seguro da Chave:** Sua chave de API do Google é armazenada de forma segura em um arquivo `.env`, separado do código-fonte.

## Requisitos

- Python 3.7 ou superior.
- As bibliotecas listadas no arquivo `requirements.txt`.

## Como Instalar e Configurar

1.  **Clone ou baixe os arquivos** para um diretório em seu computador.

2.  **Instale as dependências.** Abra o terminal (Prompt de Comando, PowerShell ou outro) na pasta do projeto e execute o seguinte comando:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Obtenha e Configure a Chave de API do Google:**

    Para usar o script, você precisa de uma chave de API do Google AI. É gratuito e fácil de obter.

    - **Acesse o Google AI Studio:** Vá para [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).
    - **Crie sua Chave:** Faça login com sua conta Google. Clique no botão **"Create API key"**.
    - **Copie a Chave:** Uma nova chave será gerada. Copie-a para a sua área de transferência. **Trate esta chave como uma senha, não a compartilhe.**

    Agora, configure a chave no script:

    - Na primeira vez que você executar o script, ele solicitará sua **Google AI API Key**.
    - Cole a chave que você acabou de copiar no terminal e pressione Enter.
    - O script perguntará se você deseja salvar a chave para uso futuro. Digite `y` (sim) e pressione Enter.
    - A chave será salva em um novo arquivo chamado `.env` na pasta do projeto. Nas próximas vezes, o script a lerá automaticamente.

## Como Usar

1.  **Execute o script** através do terminal com o comando:
    ```bash
    python csvbrothers.py
    ```

2.  **Selecione a Pasta:** Uma janela do explorador de arquivos do Windows será aberta. Navegue e selecione a pasta que contém as imagens e vídeos que você deseja processar.

3.  **Aguarde o Processamento:** O script começará a analisar cada arquivo na pasta selecionada. O progresso será exibido no terminal, mostrando qual arquivo está sendo processado e os metadados gerados para ele.

4.  **Verifique os Resultados:** Ao final do processo, você encontrará dois novos arquivos dentro da pasta que você selecionou:
    - `metadata_AAAA-MM-DD.csv`: Uma planilha com os nomes dos arquivos e todos os metadados correspondentes (título, palavras-chave e ID da categoria).
    - `processed_files.txt`: Um arquivo de log que lista todos os arquivos que já foram processados.

## Formatos de Arquivo Suportados

O script foi projetado para processar os seguintes formatos de arquivo:
- **Imagens:** `.jpg`, `.jpeg`, `.png`
- **Vídeos:** `.mp4` (o script extrai o primeiro frame do vídeo para análise)

### Suporte Especial para Vetores (`.svg`, `.eps`)

O script também oferece um suporte especial para arquivos vetoriais com as extensões `.svg` e `.eps`. Esta funcionalidade foi projetada para economizar seu tempo e manter a consistência dos metadados entre diferentes formatos do mesmo ativo artístico.

**Como funciona e o que você precisa fazer:**

O script **não envia** o arquivo vetorial para análise da IA. Em vez disso, ele de forma inteligente **reutiliza os metadados** de um arquivo de imagem (JPG ou PNG) que você já tenha na mesma pasta.

Para que a mágica aconteça, você só precisa garantir uma coisa:

**O arquivo vetorial (`.svg` ou `.eps`) deve ter exatamente o mesmo nome do arquivo de imagem correspondente, mudando apenas a extensão.**

**Exemplo Prático:**

Imagine que você tem os seguintes arquivos na sua pasta de processamento:

- `gato-feliz.jpg`
- `gato-feliz.svg`
- `cachorro-brincando.png`
- `cachorro-brincando.eps`

1.  **Execute o script** normalmente.
2.  **Primeiro Passo (Análise da IA):** O script irá analisar `gato-feliz.jpg` e `cachorro-brincando.png`, gerar o título, as palavras-chave e a categoria para cada um, e salvar essas informações no arquivo `metadata_DATA.csv`.
3.  **Segundo Passo (Mágica dos Vetores):**
    - O script encontrará o arquivo `gato-feliz.svg`. Ele vai procurar no CSV se já existem metadados para "gato-feliz". Como existem (do .jpg), ele **copiará** esses metadados e criará uma nova linha no CSV para `gato-feliz.svg`.
    - O mesmo acontecerá para `cachorro-brincando.eps`, que usará os dados de `cachorro-brincando.png`.

Ao final, seu arquivo `metadata_DATA.csv` terá quatro linhas, com metadados consistentes para todos os seus arquivos, prontos para o upload.

