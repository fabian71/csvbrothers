# CSVBROTHERS - AUTOMATIZADOR DE METADADOS PARA MÍDIA DE STOCK

O Csvbrothers é um script em Python desenvolvido para automatizar e otimizar o processo de criação de metadados para fotos e vídeos destinados a bancos de imagem (stock). Utilizando a IA do Google (Gemini), o script analisa o conteúdo de cada arquivo e gera automaticamente um título, uma descrição, palavras-chave relevantes e atribui uma categoria apropriada.

## FUNCIONALIDADES PRINCIPAIS

*   **Análise Inteligente**: Utiliza a API do Google Gemini para interpretar o conteúdo visual de imagens e vídeos.
*   **Geração Automática de Metadados**: Cria automaticamente:
    *   **Título**: Um título conciso e descritivo (aprox. 75 caracteres).
    *   **Descrição**: Uma frase que expande o título (até 160 caracteres).
    *   **Palavras-chave**: Entre 40 e 49 palavras-chave, ordenadas por relevância.
    *   **Categoria**: Seleciona a categoria mais adequada a partir de uma lista pré-definida (padrão Adobe Stock).
*   **Seleção de Pasta com Interface Gráfica**: Abre uma janela do Windows para que você possa selecionar facilmente a pasta com os arquivos que deseja processar.
*   **Saída em CSV**: Salva todos os metadados gerados em um único arquivo `.csv`, nomeado com a data do processamento (ex: `adobe_metadata_2025-07-12.csv`).
*   **Controle de Arquivos Processados**: Mantém um registro (`processed_files.txt`) para não processar o mesmo arquivo duas vezes, permitindo que você continue o trabalho de onde parou.
*   **Armazenamento Seguro da Chave**: Sua chave de API do Google é armazenada de forma segura em um arquivo `.env`, separado do código-fonte.
*   **Exportação para Múltiplas Plataformas**: Gera arquivos CSV prontos para upload no Freepik e Dreamstime.

## REQUISITOS

*   Python 3.7 ou superior.
*   As bibliotecas listadas no arquivo `requirements.txt`.

## COMO INSTALAR E CONFIGURAR

1.  Clone ou baixe os arquivos para um diretório em seu computador.
2.  Instale as dependências. Abra o terminal (Prompt de Comando, PowerShell ou outro) na pasta do projeto e execute o seguinte comando:
    `pip install -r requirements.txt`
3.  Obtenha e Configure a Chave de API do Google:
    Para usar o script, você precisa de uma chave de API do Google AI. É gratuito e fácil de obter.
    *   Acesse o Google AI Studio: Vá para https://aistudio.google.com/app/apikey.
    *   Crie sua Chave: Faça login com sua conta Google. Clique no botão "Create API key".
    *   Copie a Chave: Uma nova chave será gerada. Copie-a para a sua área de transferência. Trate esta chave como uma senha, não a compartilhe.

    Agora, configure a chave no script:
    *   Na primeira vez que você executar o script, ele solicitará sua Google AI API Key.
    *   Cole a chave que você acabou de copiar no terminal e pressione Enter.
    *   O script perguntará se você deseja salvar a chave para uso futuro. Digite `y` (sim) e pressione Enter.
    *   A chave será salva em um novo arquivo chamado `.env` na pasta do projeto. Nas próximas vezes, o script a lerá automaticamente.

## COMO USAR

1.  Execute o script através do terminal com o comando:
    `python csvbrothers.py`
2.  Selecione a Pasta: Uma janela do explorador de arquivos do Windows será aberta. Navegue e selecione a pasta que contém as imagens e vídeos que você deseja processar.
3.  Aguarde o Processamento: O script começará a analisar cada arquivo na pasta selecionada. O progresso será exibido no terminal, mostrando qual arquivo está sendo processado e os metadados gerados para ele.
4.  Verifique os Resultados: Ao final do processo, você encontrará os seguintes arquivos dentro da pasta que você selecionou:
    *   `adobe_metadata_AAAA-MM-DD.csv`: Uma planilha com os nomes dos arquivos e todos os metadados correspondentes (título, palavras-chave e ID da categoria).
    *   `freepik_metadata_AAAA-MM-DD.csv`: Uma planilha com os metadados prontos para o Freepik.
    *   `dreamstime_metadata_AAAA-MM-DD.csv`: Uma planilha com os metadados prontos para o Dreamstime.
    *   `processed_files.txt`: Um arquivo de log que lista todos os arquivos que já foram processados.

## FORMATOS DE ARQUIVO SUPORTADOS

O script foi projetado para processar os seguintes formatos de arquivo:

*   **Imagens**: `.jpg`, `.jpeg`, `.png`, `.webp`
*   **Vídeos**: `.mp4` (o script extrai o primeiro frame do vídeo para análise)
*   **Vetores**: `.svg`, `.eps`

## SUPORTE ESPECIAL PARA VETORES (.SVG, .EPS)

O script também oferece um suporte especial para arquivos vetoriais com as extensões `.svg` e `.eps`. Esta funcionalidade foi projetada para economizar seu tempo e manter a consistência dos metadados entre diferentes formatos do mesmo ativo artístico.

Como funciona e o que você precisa fazer:

O script não envia o arquivo vetorial para análise da IA. Em vez disso, ele de forma inteligente reutiliza os metadados de um arquivo de imagem (JPG, PNG ou WEBP) que você já tenha na mesma pasta.

Para que a mágica aconteça, você só precisa garantir uma coisa:

O arquivo vetorial (`.svg` ou `.eps`) deve ter exatamente o mesmo nome do arquivo de imagem correspondente, mudando apenas a extensão.

Exemplo Prático:

Imagine que você tem os seguintes arquivos na sua pasta de processamento:

*   `gato-feliz.jpg`
*   `gato-feliz.svg`
*   `cachorro-brincando.png`
*   `cachorro-brincando.eps`

1.  Execute o script normalmente.
2.  Primeiro Passo (Análise da IA): O script irá analisar `gato-feliz.jpg` e `cachorro-brincando.png`, gerar o título, as palavras-chave e a categoria para cada um, e salvar essas informações no arquivo `adobe_metadata_DATA.csv`.
3.  Segundo Passo (Mágica dos Vetores):
    *   O script encontrará o arquivo `gato-feliz.svg`. Ele vai procurar no CSV se já existem metadados para "gato-feliz". Como existem (do `.jpg`), ele copiará esses metadados e criará uma nova linha no CSV para `gato-feliz.svg`.
    *   O mesmo acontecerá para `cachorro-brincando.eps`, que usará os dados de `cachorro-brincando.png`.

Ao final, seu arquivo `adobe_metadata_DATA.csv` terá quatro linhas, com metadados consistentes para todos os seus arquivos, prontos para o upload.

💡 Dica para o Adobe Stock:

Ao fazer o upload para o Adobe Stock, você pode enviar apenas os seus arquivos vetoriais (`.svg` e `.eps`) e usar o arquivo CSV gerado pelo script. A plataforma da Adobe associará corretamente os metadados do CSV aos seus vetores com base no nome do arquivo, mesmo que a análise original da IA tenha sido feita a partir de um `.jpg` ou `.png`. Você não precisa enviar os arquivos de imagem se não quiser.

## EXPORTAÇÃO PARA FREEMIUM E DREAMSTIME

O arquivo `exporters_core.py` é responsável por gerar os CSVs para Freepik e Dreamstime.
Você pode personalizar as configurações de exportação editando este arquivo.
Por exemplo, você pode mapear as categorias do Adobe Stock para as categorias do Dreamstime.

----------------------------------------

## DOAÇÃO

Se esta ferramenta te ajuda, considere apoiar com um café ❤️

https://ko-fi.com/dentparanoide
