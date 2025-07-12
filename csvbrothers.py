import google.generativeai as genai
import os
import sys
import re
from pathlib import Path
from PIL import Image
import tempfile
import logging
import cv2
import csv
from datetime import datetime
from dotenv import load_dotenv, find_dotenv, set_key
import tkinter as tk
from tkinter import filedialog

# --- Configuração Principal ---
MODEL_NAME = "gemini-2.5-flash"
DEFAULT_FOLDER_PATH = Path(r"")
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
    csv_file_name = f"metadata_{date_str}.csv"
    csv_path = folder_path / csv_file_name

    file_exists = csv_path.exists()

    with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Filename', 'Title', 'Keywords', 'Category ID'])
        
        writer.writerow([file_name, title, keywords, category_id])
    print(f"  -> Metadata for {file_name} saved to {csv_path}")

def get_model(api_key):
    """Configura e retorna o modelo generativo."""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_prompt,
    )

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

def process_file_single_call(model, file_path, folder_path):
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
            print(f"  ❌ Ignorando arquivo devido a erro de processamento (redimensionamento/extração de quadro).")
            return False

        print(f"  - Enviando arquivo processado para API...")
        with Image.open(temp_image_path) as img:
            response = model.generate_content(img)

        title, description, keywords, category_id = parse_response(response.text)

        print("\n✅ --- Metadados gerados --- ✅")
        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"Keywords: {keywords}")
        category_name = CATEGORIAS_ADOBE.get(int(category_id), 'Unknown') if category_id.isdigit() else 'N/A'
        print(f"Category: {category_id} ({category_name})")
        print("-----------------------------\n")

        gerar_csv(file_path.name, title, keywords, category_id, folder_path)

        return True

    except Exception as e:
        print(f"  ❌ Ocorreu um erro durante o processamento: {e}")
        return False
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)

def main():
    """Função principal que valida as configurações e percorre a pasta de imagens."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    load_dotenv()
    api_key = os.getenv("API_KEY")

    if not api_key:
        print("Chave da API do Google AI não encontrada.")
        new_api_key = input("Por favor, insira sua chave de API: ").strip()
        if not new_api_key:
            print("ERRO: a chave da API não pode estar vazia.")
            return
        api_key = new_api_key
        
        save_key = input("Você deseja salvar esta chave para uso futuro? (y/n): ").lower()
        if save_key == 'y':
            env_file = find_dotenv()
            if env_file == "":
                env_file = ".env"
            set_key(env_file, "API_KEY", api_key)
            print(f"Chave de API salva em {env_file}")

    folder_path = None
    if len(sys.argv) > 1:
        folder_path = Path(sys.argv[1])
        print(f"Usando o caminho fornecido pelo argumento: {folder_path}")
    else:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        folder_path_str = filedialog.askdirectory(title="Selecione a pasta a ser processada")
        if not folder_path_str:
            print("Nenhuma pasta selecionada. Saindo.")
            return
        folder_path = Path(folder_path_str)
        print(f"Usando caminho: {folder_path}")

    if not folder_path.is_dir():
        print(f"ERROR: O caminho '{folder_path}' não é uma pasta válida.")
        return
    
    processed_log_path = folder_path / "processed_files.txt"
    processed_files = set()
    if processed_log_path.exists():
        with open(processed_log_path, "r") as f:
            processed_files = set(f.read().splitlines())
        print(f"Found {len(processed_files)} arquivos processados no log.")

    model = get_model(api_key)
    files_to_process = [p for p in folder_path.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS]

    if not files_to_process:
        print("Nenhuma imagem ou vídeo encontrado na pasta especificada.")
        return

    print(f"\nUsando modelo: {MODEL_NAME}")
    print(f"Found {len(files_to_process)} total de arquivos. Iniciando processamento...\n")

    for file_path in files_to_process:
        if file_path.name in processed_files:
            print(f"⏩ Ignorando arquivo já processado: {file_path.name}")
            continue
        
        if process_file_single_call(model, file_path, folder_path):
            with open(processed_log_path, "a") as f:
                f.write(f"{file_path.name}\n")
            print(f"  -> Registrada {file_path.name} para processar arquivos de log.")

    print("🚀 Processamento de todas as imagens concluído!")

if __name__ == "__main__":
    main()