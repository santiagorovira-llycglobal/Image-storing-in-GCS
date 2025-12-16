import os
import json
import requests
import pandas as pd
import gspread
from google.cloud import storage
from google.oauth2.service_account import Credentials
from flask import jsonify
from dotenv import load_dotenv
import functions_framework

# Cargar variables de entorno desde .env (útil para pruebas locales o si despliegas el .env)
load_dotenv()

def get_filename_from_url(url, index):
    """
    Genera un nombre de archivo seguro.
    Usa el índice de la fila para evitar sobreescribir imágenes con el mismo nombre.
    """
    try:
        # Intenta obtener el nombre real del archivo de la URL
        original_name = url.split("/")[-1].split("?")[0]
        if not original_name:
            original_name = "imagen_sin_nombre.jpg"
    except:
        original_name = "error_nombre.jpg"
    
    # Retorna formato: 001_nombrearchivo.jpg
    return f"{index}_{original_name}"

@functions_framework.http
def procesar_imagenes_sheet(request):
    """
    Función HTTP Cloud Function.
    Lee Sheets, descarga imágenes y las sube a GCS.
    """
    
    # 1. Configuración e Inicialización
    try:
        SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        SPREADSHEET_KEY = os.getenv('SPREADSHEET_KEY')
        WORKSHEET_NAME = os.getenv('WORKSHEET_NAME')
        URL_COL = os.getenv('URL_COLUMN_NAME')
        BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
        FOLDER_PATH = os.getenv('GCS_FOLDER_PATH', '') # Default vacío si no existe

        # Validaciones básicas
        if not all([SERVICE_ACCOUNT_FILE, SPREADSHEET_KEY, URL_COL, BUCKET_NAME]):
            return jsonify({"error": "Faltan variables de entorno críticas"}), 500

        print(f"Iniciando proceso para Sheet: {SPREADSHEET_KEY}")

        # Definir scopes necesarios para Sheets y Drive
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Cargar credenciales
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
        
        # Cliente de GCS
        storage_client = storage.Client(credentials=creds)
        bucket = storage_client.bucket(BUCKET_NAME)

        # Cliente de Sheets
        gc = gspread.authorize(creds)
        
    except Exception as e:
        return jsonify({"error": f"Error en autenticación o configuración: {str(e)}"}), 500

    # 2. Obtener Data Frame
    try:
        sh = gc.open_by_key(SPREADSHEET_KEY)
        worksheet = sh.worksheet(WORKSHEET_NAME)
        
        # Obtener todos los registros como lista de diccionarios
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        if df.empty:
            return jsonify({"message": "La hoja está vacía."}), 200
        
        if URL_COL not in df.columns:
            return jsonify({"error": f"La columna '{URL_COL}' no existe en el Sheet."}), 400
            
    except Exception as e:
        return jsonify({"error": f"Error leyendo Google Sheets: {str(e)}"}), 500

    # 3. Procesamiento de Imágenes
    resultados = {
        "total": len(df),
        "subidas": 0,
        "errores": 0,
        "detalles": []
    }

    print(f"Procesando {len(df)} filas...")

    # Iterar sobre el DataFrame
    for index, row in df.iterrows():
        url_imagen = row.get(URL_COL)
        
        # Saltar si no hay URL
        if not url_imagen or pd.isna(url_imagen) or str(url_imagen).strip() == "":
            continue

        try:
            # Descargar la imagen
            response = requests.get(url_imagen, stream=True, timeout=10)
            
            if response.status_code == 200:
                # Definir nombre de archivo en GCS
                filename = get_filename_from_url(url_imagen, index)
                blob_path = f"{FOLDER_PATH}{filename}" if FOLDER_PATH else filename
                
                # Subir a GCS
                blob = bucket.blob(blob_path)
                blob.upload_from_string(
                    response.content, 
                    content_type=response.headers.get('Content-Type')
                )
                
                resultados["subidas"] += 1
                # Opcional: Podrías actualizar el sheet aquí con la URL de GCS si quisieras
            else:
                resultados["errores"] += 1
                resultados["detalles"].append(f"Fila {index}: Status {response.status_code} para {url_imagen}")

        except Exception as e:
            resultados["errores"] += 1
            resultados["detalles"].append(f"Fila {index}: Error {str(e)}")
            print(f"Error en fila {index}: {e}")

    # 4. Retorno final
    return jsonify({
        "status": "Proceso finalizado",
        "estadisticas": resultados
    }), 200

# Bloque para pruebas locales simples
if __name__ == "__main__":
    # Simula una request vacía para testeo local
    class MockRequest:
        pass
    print(procesar_imagenes_sheet(MockRequest()))
