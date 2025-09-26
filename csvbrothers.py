import google.generativeai as genai
import os
import sys
import re
import base64
from pathlib import Path
from PIL import Image
import tempfile
import logging

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import openai as openai_legacy
except ImportError:
    openai_legacy = None
import cv2
import csv
from datetime import datetime
from dotenv import load_dotenv, find_dotenv, set_key
import tkinter as tk
from tkinter import filedialog

# --- Exporters (API-first) ---
API_ROWS = []
try:
    from exporters_core import export_from_rows
except Exception:
    export_from_rows = None


# --- Configuração Principal ---
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"
DEFAULT_OPENAI_MODEL = "gpt-5-mini"
DEFAULT_FOLDER_PATH = Path(r"")
SUPPORTED_PROVIDERS = {"gemini", "openai"}
CATEGORIAS_ADOBE = {
    1: "Animals", 2: "Buildings and Architecture", 3: "Business", 4: "Drinks",
    5: "The Environment", 6: "States of Mind", 7: "Food", 8: "Graphic Resources",
    9: "Hobbies and Leisure", 10: "Industry", 11: "Landscapes", 12: "Lifestyle",
    13: "People", 14: "Plants and Flowers", 15: "Culture and Religion", 16: "Science",
    17: "Social Issues", 18: "Sports", 19: "Technology", 20: "Transport", 21: "Travel"
}
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.mp4')

# --- System Prompt (em Inglês) ---
system_prompt = f"""
You are an expert in image SEO for stock photo agencies. Your complete task is to analyze the provided image and perform four actions: generate a title, a description, a list of keywords, and select a category ID.

**1. Title:**
- Create a concise, descriptive title in natural language (around 75 characters).

**2. Description:**
- Write a descriptive sentence for the image, up to 160 characters long. This should expand on the title.

**3. Keywords:**
- Provide 40 to 49 precise keywords, ordered by importance.
- Include literal terms (what is seen) and conceptual terms (feelings, trends).

**4. Category Selection:**
- Based on the image, title, and keywords, select the most appropriate category ID from the list below.
- **Category List:** {str(CATEGORIAS_ADOBE)}

**MANDATORY OUTPUT FORMAT:**
Respond ONLY with the following XML format, with no other text before or after.

<METADATA>
    <TITLE>
    [Your title here]
    </TITLE>
    <DESCRIPTION>
    [Your description here, up to 160 characters]
    </DESCRIPTION>
    <KEYWORDS>
    [keyword1], [keyword2], [keyword3], ...
    </KEYWORDS>
    <CATEGORY_ID>
    [The single numeric ID here]
    </CATEGORY_ID>
</METADATA>
"""

# --- Funções do Script ---


def parse_api_keys(raw_value):
    """Recebe uma string e devolve uma lista de chaves limpas."""
    if not raw_value:
        return []
    return [token.strip() for token in re.split(r'[;,\n\r\t ]+', raw_value) if token.strip()]


class APIKeyRotator:
    """Controla a alternância cíclica entre múltiplas chaves de API."""

    def __init__(self, api_keys):
        if not api_keys:
            raise ValueError("É necessário fornecer ao menos uma chave de API.")
        self._api_keys = api_keys
        self._index = 0
        self._total = len(api_keys)

    @property
    def total(self):
        return self._total

    def acquire_key(self):
        """Retorna a próxima chave e informações sobre a posição utilizada."""
        api_key = self._api_keys[self._index]
        slot = self._index + 1
        self._index = (self._index + 1) % self._total
        return api_key, slot, self._total


def load_gemini_keys_from_env():
    """Carrega chaves do .env (GEMINI_API_KEYS ou GEMINI_API_KEY) e devolve em lista."""
    api_keys = parse_api_keys(os.getenv("GEMINI_API_KEYS"))
    if api_keys:
        return api_keys
    single_key = os.getenv("GEMINI_API_KEY")
    if single_key and single_key.strip():
        return [single_key.strip()]
    return []

def load_openai_keys_from_env():
    """Carrega chaves do .env (OPENAI_API_KEYS ou OPENAI_API_KEY) e devolve em lista."""
    api_keys = parse_api_keys(os.getenv("OPENAI_API_KEYS"))
    if api_keys:
        return api_keys
    single_key = os.getenv("OPENAI_API_KEY")
    if single_key and single_key.strip():
        return [single_key.strip()]
    return []

def redimensionar_imagem(caminho_imagem, max_dimensao=600):
    """Redimensiona uma imagem para envio à API e retorna o caminho do arquivo temporário."""
    try:
        with Image.open(caminho_imagem) as img:
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, (0, 0), img)
                img_to_process = background
            else:
                img_to_process = img.convert('RGB')

            img_to_process.thumbnail((max_dimensao, max_dimensao))
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg', mode='wb') as temp_file:
                img_to_process.save(temp_file, 'JPEG', quality=85)
                return temp_file.name
    except Exception as e:
        logging.error(f"Erro ao redimensionar a imagem {caminho_imagem}: {e}")
        return None

def extrair_frame(caminho_video, max_dimensao=600):
    """Extracts and resizes a frame from a video, returns path to temp file."""
    video = cv2.VideoCapture(str(caminho_video))
    try:
        success, image = video.read()
        if success:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                cv2.imwrite(temp_file.name, image)
                return redimensionar_imagem(temp_file.name, max_dimensao)
        return None
    except Exception as e:
        logging.error(f"Error extracting frame from {caminho_video}: {e}")
        return None
    finally:
        video.release()

def gerar_csv(file_name, title, keywords, category_id, folder_path):
    """Gera um arquivo CSV com os metadados."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    csv_file_name = f"adobe_metadata_{date_str}.csv"
    csv_path = folder_path / csv_file_name

    file_exists = csv_path.exists()

    with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Filename', 'Title', 'Keywords', 'Category ID'])
        
        writer.writerow([file_name, title, keywords, category_id])
    print(f"  -> Metadata for {file_name} saved to {csv_path}")

def build_gemini_model(api_key, model_name):
    """Configura e retorna o modelo generativo do Gemini."""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
    )

def generate_with_gemini(api_key, model_name, image_path):
    """Gera metadados usando o modelo Gemini configurado."""
    model = build_gemini_model(api_key, model_name)
    with Image.open(image_path) as img:
        response = model.generate_content(img)
    return response.text


def _ensure_openai_available():
    if OpenAI is None and openai_legacy is None:
        raise RuntimeError("Biblioteca openai não está instalada. Instale 'openai'.")


def _normalize_openai_output(payload):
    """Extrai texto das respostas do OpenAI, cobrindo clientes novos e legados."""
    if payload is None:
        return ""

    try:
        output_text = getattr(payload, 'output_text', None)
        if output_text:
            return output_text.strip()
    except Exception:
        pass

    try:
        output = getattr(payload, 'output', None)
        if output:
            collected = []
            for block in output:
                contents = getattr(block, 'content', [])
                for item in contents:
                    text_item = getattr(item, 'text', None)
                    if text_item:
                        collected.append(text_item)
            if collected:
                return "\n".join(collected).strip()
    except Exception:
        pass

    if isinstance(payload, dict):
        if payload.get('output_text'):
            text = payload['output_text']
            if text:
                return text.strip()
        output = payload.get('output')
        if output:
            collected = []
            for block in output:
                for item in block.get('content', []):
                    text_item = item.get('text')
                    if text_item:
                        collected.append(text_item)
            if collected:
                return "\n".join(collected).strip()
        choices = payload.get('choices')
        if choices:
            choice = choices[0]
            message = choice.get('message', {})
            content = message.get('content')
            if isinstance(content, list):
                return ''.join(part.get('text', '') for part in content if isinstance(part, dict)).strip()
            if isinstance(content, str):
                return content.strip()

    choices = getattr(payload, 'choices', None)
    if choices:
        choice0 = choices[0]
        message = getattr(choice0, 'message', None)
        if message is not None:
            content = getattr(message, 'content', '')
            if isinstance(content, list):
                return ''.join(getattr(part, 'text', '') for part in content).strip()
            return str(content).strip()
        text_attr = getattr(choice0, 'text', None)
        if text_attr:
            return str(text_attr).strip()

    return str(payload).strip()


def generate_with_openai(api_key, model_name, image_path):
    """Gera metadados usando um modelo da OpenAI com suporte a imagens."""
    _ensure_openai_available()
    with open(image_path, 'rb') as image_file:
        image_b64 = base64.b64encode(image_file.read()).decode('utf-8')

    if OpenAI is not None:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model_name,
            input=[
                {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
                {"role": "user", "content": [
                    {"type": "input_text", "text": "Analyze the image and respond following the XML schema."},
                    {"type": "input_image", "image_base64": image_b64}
                ]}
            ],
        )
        return _normalize_openai_output(response)

    # Fallback para cliente legado
    openai_legacy.api_key = api_key
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [
            {"type": "text", "text": "Analyze the image and respond following the XML schema."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
        ]}
    ]
    response = openai_legacy.ChatCompletion.create(
        model=model_name,
        messages=messages
    )
    return _normalize_openai_output(response)

def parse_response(text):
    """Extrai os metadados da resposta XML de forma segura e eficiente."""
    title_match = re.search(r"<TITLE>(.*?)</TITLE>", text, re.DOTALL)
    title = title_match.group(1).strip() if title_match else "Not found"

    description_match = re.search(r"<DESCRIPTION>(.*?)</DESCRIPTION>", text, re.DOTALL)
    description = description_match.group(1).strip() if description_match else "Not found"

    keywords_match = re.search(r"<KEYWORDS>(.*?)</KEYWORDS>", text, re.DOTALL)
    keywords = keywords_match.group(1).strip() if keywords_match else "Not found"

    category_id_match = re.search(r"<CATEGORY_ID>(.*?)</CATEGORY_ID>", text, re.DOTALL)
    category_id = category_id_match.group(1).strip() if category_id_match else "Not found"
    
    return title, description, keywords, category_id

def process_file_single_call(provider, api_key_rotator, active_model, file_path, folder_path):
    """Preparar e processar um arquivo (imagem ou vídeo) e depois limpar os arquivos temporários."""
    print("-" * 50)
    print(f"Processando arquivo original: {file_path.name}")

    temp_image_path = None
    try:
        file_extension = file_path.suffix.lower()

        if file_extension in ('.jpg', '.jpeg', '.png', '.webp'):
            print("  - Redimensionando a imagem para envio...")
            temp_image_path = redimensionar_imagem(file_path)
        elif file_extension == '.mp4':
            print("  - Extraindo quadros do vídeo para envio...")
            temp_image_path = extrair_frame(file_path)
        else:
            print(f"  - Tipo de arquivo não suportado: {file_extension}")
            return False

        if not temp_image_path:
            print("  ? Ignorando arquivo devido a erro de processamento (redimensionamento/extração de quadro).")
            return False

        api_key, slot, total = api_key_rotator.acquire_key()
        provider_label = "Gemini" if provider == "gemini" else "OpenAI"
        if total > 1:
            print(f"  - Alternando para chave {provider_label} #{slot}/{total}.")
        print(f"  - Enviando arquivo processado para {provider_label}...")

        if provider == "gemini":
            response_text = generate_with_gemini(api_key, active_model, temp_image_path)
        else:
            response_text = generate_with_openai(api_key, active_model, temp_image_path)

        title, description, keywords, category_id = parse_response(response_text)

        # Acumular resultado desta execução para os exports externos
        try:
            API_ROWS.append({
                "Filename": file_path.name,
                "Title": title,
                "Description": description,
                "Keywords": keywords,
                "Category ID": category_id,
                "Releases": "",
                "DT_Category2": "",
                "DT_Category3": ""
            })
        except Exception:
            pass

        print("\\n? --- Metadados gerados --- ?")
        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"Keywords: {keywords}")
        category_name = CATEGORIAS_ADOBE.get(int(category_id), 'Unknown') if category_id.isdigit() else 'N/A'
        print(f"Category: {category_id} ({category_name})")
        print("-----------------------------\\n")

        gerar_csv(file_path.name, title, keywords, category_id, folder_path)

        return True

    except Exception as e:
        print(f"  ? Ocorreu um erro durante o processamento: {e}")
        return False
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)



def main():
    """Função principal que valida as configurações e percorre a pasta de imagens."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    load_dotenv()

    args = sys.argv[1:]
    provider_override = None
    model_override = None
    folder_arg = None
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg.startswith('--provider='):
            provider_override = arg.split('=', 1)[1].strip().lower()
        elif arg == '--provider':
            if idx + 1 < len(args):
                provider_override = args[idx + 1].strip().lower()
                idx += 1
            else:
                print("Flag --provider requer um valor (gemini ou openai). Mantendo configuração padrão.")
        elif arg.startswith('--model='):
            model_override = arg.split('=', 1)[1].strip()
        elif arg == '--model':
            if idx + 1 < len(args):
                model_override = args[idx + 1].strip()
                idx += 1
            else:
                print("Flag --model requer um valor. Mantendo configuração padrão.")
        else:
            if folder_arg is None:
                folder_arg = arg
            else:
                print(f"Aviso: argumento extra '{arg}' será ignorado.")
        idx += 1

    provider = (provider_override or os.getenv('CSV_PROVIDER') or 'gemini').lower()
    if provider not in SUPPORTED_PROVIDERS:
        print(f"Provedor '{provider}' não reconhecido. Usando 'gemini'.")
        provider = 'gemini'

    if provider == 'openai':
        api_keys = load_openai_keys_from_env()
        env_model = os.getenv('OPENAI_MODEL')
        default_model = DEFAULT_OPENAI_MODEL
        key_var_plural = 'OPENAI_API_KEYS'
        key_var_single = 'OPENAI_API_KEY'
        provider_label = 'OpenAI'
    else:
        provider = 'gemini'
        api_keys = load_gemini_keys_from_env()
        env_model = os.getenv('GEMINI_MODEL')
        default_model = DEFAULT_GEMINI_MODEL
        key_var_plural = 'GEMINI_API_KEYS'
        key_var_single = 'GEMINI_API_KEY'
        provider_label = 'Gemini'

    active_model = model_override or env_model or default_model

    if not api_keys:
        print(f"Nenhuma chave {provider_label} foi encontrada nas variáveis de ambiente.")
        raw_keys = input(f"Por favor, insira uma ou mais chaves {provider_label} (separe por vírgulas ou espaços): ").strip()
        api_keys = parse_api_keys(raw_keys)
        if not api_keys:
            print(f"ERRO: é necessário informar ao menos uma chave da {provider_label} API.")
            return

        save_key = input(f"Você deseja salvar estas chaves {provider_label} no .env para uso futuro? (y/n): ").lower()
        if save_key == 'y':
            env_file = find_dotenv()
            if env_file == '':
                env_file = '.env'
            key_name = key_var_plural if len(api_keys) > 1 else key_var_single
            value_to_save = ','.join(api_keys) if len(api_keys) > 1 else api_keys[0]
            set_key(env_file, key_name, value_to_save)
            print(f"Chave(s) {provider_label} salva(s) em {env_file} como {key_name}")

    if len(api_keys) > 1:
        print(f"Foram encontradas {len(api_keys)} chaves {provider_label}. Cada requisição usará a próxima chave da lista.")

    api_key_rotator = APIKeyRotator(api_keys)

    if folder_arg:
        folder_path = Path(folder_arg)
        print(f"Usando o caminho fornecido pelo argumento: {folder_path}")
    else:
        root = tk.Tk()
        root.withdraw()
        folder_path_str = filedialog.askdirectory(title="Selecione a pasta a ser processada")
        if not folder_path_str:
            print("Nenhuma pasta selecionada. Saindo.")
            return
        folder_path = Path(folder_path_str)
        print(f"Usando caminho: {folder_path}")

    if not folder_path.is_dir():
        print(f"ERROR: O caminho '{folder_path}' não é uma pasta válida.")
        return

    processed_log_path = folder_path / 'processed_files.txt'
    processed_files = set()
    if processed_log_path.exists():
        with open(processed_log_path, 'r') as f:
            processed_files = set(f.read().splitlines())
        print(f"Found {len(processed_files)} arquivos processados no log.")

    files_to_process = [p for p in folder_path.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS]

    if not files_to_process:
        print("Nenhuma imagem ou vídeo encontrado na pasta especificada.")
        return

    print(f"\\nUsando provedor: {provider_label} | modelo: {active_model}")
    print(f"Found {len(files_to_process)} total de arquivos. Iniciando processamento...\\n")

    for file_path in files_to_process:
        if file_path.name in processed_files:
            print(f"? Ignorando arquivo já processado: {file_path.name}")
            continue

        if process_file_single_call(provider, api_key_rotator, active_model, file_path, folder_path):
            with open(processed_log_path, 'a') as f:
                f.write(f"{file_path.name}\\n")
            print(f"  -> Registrada {file_path.name} para processar arquivos de log.")

    print("?? Processamento de todas as imagens concluído!")

    # --- NOVO BLOCO: Processamento de arquivos vetoriais associados ---
    print("\\n?? Verificando arquivos vetoriais associados (.svg, .eps)...")

    date_str = datetime.now().strftime("%Y-%m-%d")
    csv_file_name = f"adobe_metadata_{date_str}.csv"
    csv_path = folder_path / csv_file_name

    if not csv_path.exists():
        print("  - Arquivo de metadados não encontrado. Nenhum arquivo vetorial será processado.")
    else:
        # Ler metadados existentes do CSV
        metadata_map = {}
        try:
            with open(csv_path, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    print("  - Arquivo de metadados está vazio. Nenhum arquivo vetorial será processado.")
                else:
                    for row in reader:
                        base_name = Path(row['Filename']).stem
                        metadata_map[base_name] = row
        except Exception as e:
            print(f"  - Erro ao ler o arquivo CSV: {e}. Nenhum arquivo vetorial será processado.")

        if not metadata_map:
            print("  - Nenhum metadado encontrado no arquivo CSV. Nenhum arquivo vetorial será processado.")
        else:
            vector_extensions = ('.svg', '.eps')
            vector_files_found = [p for p in folder_path.iterdir() if p.suffix.lower() in vector_extensions]

            added_count = 0
            for vector_path in vector_files_found:
                if vector_path.name in processed_files:
                    print(f"  ? Ignorando arquivo vetorial já processado: {vector_path.name}")
                    continue

                vector_base_name = vector_path.stem
                if vector_base_name in metadata_map:
                    print(f"  ? Encontrada correspondência para: {vector_path.name}")
                    metadata = metadata_map[vector_base_name]

                    with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            vector_path.name,
                            metadata['Title'],
                            metadata['Keywords'],
                            metadata['Category ID']
                        ])
                    print(f"    -> Metadados para {vector_path.name} salvos em {csv_path}")

                    with open(processed_log_path, 'a') as f:
                        f.write(f"{vector_path.name}\\n")
                    print(f"    -> Registrado {vector_path.name} no arquivo de log.")
                    added_count += 1

            if added_count > 0:
                print(f"\\n? Adicionados metadados para {added_count} arquivo(s) vetorial(is).")
            else:
                print("  - Nenhum novo arquivo vetorial correspondente encontrado para processar.")

    # === Exports externos (Freepik/Dreamstime) a partir da resposta da API ===
    try:
        if not export_from_rows:
            print("?? exporters_core.py não encontrado; pulando exports externos.")
        else:
            base_rows = list(API_ROWS)
            if not base_rows:
                date_str = datetime.now().strftime("%Y-%m-%d")
                csv_file_name = f"adobe_metadata_{date_str}.csv"
                csv_path = folder_path / csv_file_name
                if csv_path.exists():
                    with open(csv_path, newline="", encoding="utf-8") as f:
                        dr = csv.DictReader(f)
                        for r in dr:
                            base_rows.append({
                                "Filename": r.get("Filename", ""),
                                "Title": r.get("Title", ""),
                                "Description": r.get("Description", ""),
                                "Keywords": r.get("Keywords", ""),
                                "Category ID": r.get("Category ID", ""),
                                "Releases": r.get("Releases", ""),
                                "DT_Category2": r.get("DT_Category2", ""),
                                "DT_Category3": r.get("DT_Category3", "")
                            })
                else:
                    print("?? Sem API_ROWS e sem CSV master do dia; nada para exportar.")

            final_rows = []
            if base_rows:
                from pathlib import Path as _Path
                vector_exts = {'.svg', '.eps'}
                by_stem = {}
                for r in base_rows:
                    fn = r.get("Filename", "")
                    if fn:
                        by_stem[_Path(fn).stem] = r
                seen_stems = set()
                for p in folder_path.iterdir():
                    if p.suffix.lower() in vector_exts:
                        stem = p.stem
                        base = by_stem.get(stem)
                        if base:
                            clone = dict(base)
                            clone["Filename"] = p.name
                            final_rows.append(clone)
                            seen_stems.add(stem)
                for stem, r in by_stem.items():
                    if stem not in seen_stems:
                        final_rows.append(r)

            if final_rows:
                stem = datetime.now().strftime("%Y-%m-%d")
                export_from_rows(final_rows, outdir=folder_path,
                                 targets=['freepik', 'dreamstime'],
                                 config_path=None, master_stem=stem)
                print("?? Exports gerados (freepik/dreamstime).")
            else:
                print("?? Nada para exportar.")
    except Exception as e:
        print(f"?? Falha ao gerar exports externos: {e}")

    print("?? Processo finalizado.")

if __name__ == "__main__":
    main()
