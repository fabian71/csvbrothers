# CSVBROTHERS - Automação de Metadados para Bancos de Imagem

O CSVBROTHERS é um utilitário em Python que automatiza a criação de metadados para fotos, vídeos e vetores destinados a agências de stock. A ferramenta processa uma pasta de arquivos, envia o conteúdo visual para modelos de IA (Google Gemini ou OpenAI) e gera título, descrição, palavras-chave e categoria prontos para importação em diferentes plataformas.

Este README descreve instalação, configuração, execução e fluxos avançados, incluindo uso de múltiplas chaves de API e exportação para Adobe Stock, Freepik e Dreamstime.

---

## Sumário
- [Principais Recursos](#principais-recursos)
- [Arquitetura Geral](#arquitetura-geral)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração de Ambiente](#configuração-de-ambiente)
  - [.env](#env)
  - [Variáveis de ambiente suportadas](#variáveis-de-ambiente-suportadas)
- [Uso Básico](#uso-básico)
  - [Selecionando provedor e modelo](#selecionando-provedor-e-modelo)
  - [Opções de linha de comando](#opções-de-linha-de-comando)
- [Fluxo Completo de Processamento](#fluxo-completo-de-processamento)
- [Formatos Suportados](#formatos-suportados)
  - [Imagens e vídeos](#imagens-e-vídeos)
  - [Vetores e reaproveitamento de metadados](#vetores-e-reaproveitamento-de-metadados)
- [CSV Gerados](#csv-gerados)
- [Rotação de Múltiplas Chaves](#rotação-de-múltiplas-chaves)
- [Exportação para Plataformas](#exportação-para-plataformas)
- [Boas Práticas e Dicas](#boas-práticas-e-dicas)
- [Resolução de Problemas](#resolução-de-problemas)
- [Contribuição](#contribuição)
- [Doação](#doação)

---

## Principais Recursos
- **IA Híbrida**: suporte a Google Gemini e OpenAI (por exemplo `gpt-5-mini`) comutáveis por flag ou variável de ambiente.
- **Metadados completos**: gera título, descrição (até 160 caracteres), lista de 40 a 49 palavras-chave e categoria Adobe Stock.
- **Entrada multimídia**: imagens (`jpg`, `jpeg`, `png`, `webp`), vídeos (`mp4`) e vetores (`svg`, `eps`).
- **Rotação de chaves**: aceita múltiplas chaves por provedor e distribui cada requisição em round-robin.
- **Persistência**: mantém log `processed_files.txt` garantindo reprocessamento apenas quando desejado.
- **Exportação multiplataforma**: cria CSVs para Adobe Stock, Freepik e Dreamstime, além de reutilizar metadados para vetores com mesmo nome.
- **Interface amigável**: seleção opcional de pasta via janela do sistema (tkinter) ou argumento de linha de comando.

## Arquitetura Geral
```
+-------------------+      +-----------------------+
| Pasta de entrada  | ---> | csvbrothers.py (CLI)  |
+-------------------+      +-----------------------+
           |                         |
           |                         +--> Análise por IA (Gemini ou OpenAI)
           |                         |
           v                         +--> CSVs de saída e logs
   processed_files.txt               +--> exporters_core.py (opcional)
```

`csvbrothers.py` concentra o fluxo principal: leitura da pasta, redimensionamento de imagens, escolha do provedor de IA, geração de metadados, escrita de CSVs, reaproveitamento para vetores e exportação adicional. O arquivo `exporters_core.py` pode ser customizado para adequar os layouts finais às plataformas desejadas.

## Requisitos
- Python 3.8 ou superior recomendado.
- Dependências listadas em `requirements.txt` (instalação com `pip install -r requirements.txt`).
- Conta com acesso à API do Google AI Studio (Gemini) e/ou conta OpenAI com modelos multimodais habilitados.
- Sistema operacional com suporte a tkinter (Windows, Linux ou macOS).

## Instalação
```bash
# 1. Clone ou copie o repositório
# 2. Crie um ambiente virtual (opcional, porém recomendado)
python -m venv .venv
source .venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1

# 3. Instale as dependências
pip install -r requirements.txt
```

> Dica: sempre mantenha o `pip` atualizado (`python -m pip install --upgrade pip`).

## Configuração de Ambiente
### .env
O arquivo `.env` é lido automaticamente no início da execução. Exemplo mínimo:
```
GEMINI_API_KEY=coloque-sua-chave-gemini-aqui
OPENAI_API_KEY=coloque-sua-chave-openai-aqui
CSV_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash-lite
OPENAI_MODEL=gpt-5-mini
```

As chaves podem ser salvas na primeira execução caso você aceite o prompt interativo. Para múltiplas chaves, veja [Rotação de Múltiplas Chaves](#rotação-de-múltiplas-chaves).

### Variáveis de ambiente suportadas
| Variável              | Descrição                                                                 | Default                           |
|-----------------------|---------------------------------------------------------------------------|-----------------------------------|
| `GEMINI_API_KEY`      | Chave única da API Gemini.                                                | —                                 |
| `GEMINI_API_KEYS`     | Lista separada por vírgula/space de chaves Gemini.                        | —                                 |
| `OPENAI_API_KEY`      | Chave única da API OpenAI.                                                | —                                 |
| `OPENAI_API_KEYS`     | Lista separada de chaves OpenAI para rotação.                             | —                                 |
| `CSV_PROVIDER`        | Provedor padrão (`gemini` ou `openai`).                                   | `gemini`                          |
| `GEMINI_MODEL`        | Nome do modelo Gemini padrão.                                            | `gemini-2.5-flash-lite`           |
| `OPENAI_MODEL`        | Nome do modelo OpenAI padrão.                                             | `gpt-5-mini`                      |
| `CSV_FOLDER` (opcional)| Pasta padrão para processar (alternativa ao seletor).                    | não definido                      |

> Prioridade: flags de CLI sobrescrevem variáveis de ambiente, que por sua vez sobrescrevem os defaults embutidos.

## Uso Básico
### Selecionando provedor e modelo
O script permite alternar o provedor de IA a cada execução:
```bash
# Usar Gemini com o modelo padrão
python csvbrothers.py

# Forçar Gemini com modelo específico
python csvbrothers.py --provider gemini --model gemini-2.0-pro

# Usar OpenAI (ex: gpt-5-mini)
python csvbrothers.py --provider openai --model gpt-5-mini
```

> Se você omitir `--model`, o script tenta `OPENAI_MODEL` (ou `GEMINI_MODEL`) e, na ausência, usa o default interno.

### Opções de linha de comando
| Opção                 | Descrição                                                                 |
|-----------------------|---------------------------------------------------------------------------|
| `--provider {gemini|openai}` | Define o provedor utilizado nesta execução.                         |
| `--model <nome>`      | Define o modelo a ser usado (compatível com o provedor selecionado).      |
| `--provider` seguido do valor | Forma alternativa: `--provider openai`.                            |
| `--model` seguido do valor    | Forma alternativa: `--model gpt-5-mini`.                           |
| `<caminho-da-pasta>`  | Argumento posicional opcional para pular a janela de seleção de pasta.    |

Exemplos:
```bash
python csvbrothers.py "D:\portfolio\lote1"
python csvbrothers.py --provider openai "E:\midia\para_processar"
python csvbrothers.py --provider gemini --model gemini-2.0-flash "./imagens"
```

## Fluxo Completo de Processamento
1. **Carregamento de configuração**: leitura do `.env`, definição do provedor e modelo ativos.
2. **Seleção da pasta**: via argumento ou janela interativa.
3. **Stage de pré-processamento**:
   - Conversão de PNGs sem transparência para JPG.
   - Montagem da lista de arquivos suportados.
   - Filtragem de arquivos já processados (`processed_files.txt`).
4. **Loop principal**:
   - Redimensionamento de imagem ou extração de frame (vídeos).
   - Seleção da próxima chave da lista (round-robin).
   - Chamada ao provedor (Gemini via `google-generativeai` ou OpenAI via `responses`/`ChatCompletion`).
   - Parsing do XML retornado, impressão e registro em CSV.
5. **Vetores**: reaproveitamento de metadados para `.svg`/`.eps` com mesmo nome base.
6. **Exporters externos**: criação de planilhas para Freepik/Dreamstime (quando `exporters_core.py` está disponível).
7. **Finalização**: limpeza de temporários, mensagem de resumo e CSVs prontos na pasta.

## Formatos Suportados
### Imagens e vídeos
- Imagens: `.jpg`, `.jpeg`, `.png`, `.webp` (conversão automática quando possível).
- Vídeos: `.mp4` (usa o primeiro frame para análise).

### Vetores e reaproveitamento de metadados
- Vetores: `.svg`, `.eps`.
- Requisitos: ter um arquivo raster (ex: `arte.jpg`) com o mesmo nome base do vetor (`arte.svg`).
- O script copia metadados existentes do raster para o vetor, evitando múltiplas chamadas à IA.

## CSV Gerados
Para cada execução bem-sucedida você encontrará na pasta processada:
- `adobe_metadata_YYYY-MM-DD.csv`: metadados mestres (título, descrição, keywords, categoria).
- `freepik_metadata_YYYY-MM-DD.csv`: conforme configuração no `exporters_core.py`.
- `dreamstime_metadata_YYYY-MM-DD.csv`: idem acima.
- `processed_files.txt`: log de arquivos já processados (inclui vetores reaproveitados).

## Rotação de Múltiplas Chaves
- Defina `GEMINI_API_KEYS` ou `OPENAI_API_KEYS` com valores separados por vírgulas, espaços ou quebras de linha.
- O script mantém um índice interno e alterna a cada arquivo processado, exibindo o slot ativo (`#1/3`, por exemplo).
- Se apenas uma chave for informada, o comportamento é idêntico ao tradicional.

Exemplo `.env` para múltiplas chaves Gemini:
```
GEMINI_API_KEYS=chave_um, chave_dois, chave_tres
```

## Exportação para Plataformas
O módulo `exporters_core.py` (se presente) recebe os dados acumulados e gera CSVs específicos. Para personalizar:
1. Abra `exporters_core.py` e ajuste os mapeamentos ou colunas desejadas.
2. Caso queira desativar exportações externas, basta remover/renomear o arquivo ou adaptar a condição no final de `csvbrothers.py`.

## Boas Práticas e Dicas
- Prefira executar em lotes menores para validar o comportamento do modelo escolhido.
- Revise os CSVs antes de subir para as plataformas (especialmente keywords e categorias).
- Mantenha as chaves de API em local seguro e nunca faça commit de `.env` em repositórios públicos.
- Para bins grandes de vídeo, considere gerar previamente uma imagem representativa para reduzir consumo de crédito.
- Utilize ambientes virtuais distintos para separar dependências entre projetos.

## Resolução de Problemas
| Sintoma                                             | Possíveis causas e soluções                                     |
|-----------------------------------------------------|------------------------------------------------------------------|
| `Biblioteca openai não está instalada`              | Execute `pip install openai` ou reinstale `requirements.txt`.    |
| Erro `provider 'xyz' não reconhecido`               | Use apenas `gemini` ou `openai` (verifique `--provider`).        |
| Resposta vazia ou parsing falha                     | O modelo pode ter respondido fora do formato; reexecute o arquivo.| 
| Vetores não recebem metadados                       | Verifique se o nome base coincide (`arte.jpg` x `arte.svg`).     |
| Mesmo arquivo processado repetidamente              | Apague `processed_files.txt` ou remova entradas específicas.     |
| Chaves não reconhecidas após salvar                 | Confirme se o `.env` está no mesmo diretório do script.          |

## Contribuição
Sugestões, correções e melhorias são bem-vindas. Abra issues ou envie pull requests descrevendo claramente o problema e a proposta de solução. Antes de contribuir:
1. Rode `python -m compileall csvbrothers.py` para checar sintaxe.
2. Atualize ou adicione testes/validações manuais conforme aplicável.
3. Documente mudanças relevantes neste README.

## Doação
Se esta ferramenta poupa seu tempo, considere apoiar com um café:

https://ko-fi.com/dentparanoide

