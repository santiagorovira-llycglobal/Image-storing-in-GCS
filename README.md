# Sistema de Almacenamiento de Imágenes - Arquitectura Modular

Una Cloud Function que lee URLs de imágenes desde Google Sheets, verifica duplicados en Google Cloud Storage (GCS), sube imágenes nuevas y almacena todas las URLs en BigQuery.

## Características

- ✅ **Detección de Duplicados**: Verifica si las imágenes ya existen en GCS antes de subirlas
- ✅ **Arquitectura Modular**: Separación clara de responsabilidades entre múltiples módulos
- ✅ **Integración con BigQuery**: Almacena URLs de imágenes y metadatos en BigQuery
- ✅ **Integración con Google Sheets**: Lee URLs de imágenes desde Google Sheets
- ✅ **Registro Completo**: Seguimiento detallado del progreso y reporte de errores
- ✅ **Listo para Cloud Functions**: Desplegable como Google Cloud Function

## Arquitectura

```
Image-storing-in-GCS/
├── modules/
│   ├── __init__.py              # Exportaciones del módulo
│   ├── config.py                # Gestión de configuración
│   ├── storage_manager.py       # Operaciones de GCS
│   ├── bigquery_manager.py      # Operaciones de BigQuery
│   └── sheets_manager.py        # Operaciones de Google Sheets
├── main.py                      # Punto de entrada de Cloud Function
├── requirements.txt             # Dependencias de Python
├── .env.example                 # Plantilla de variables de entorno
└── README.md                    # Este archivo
```

### Responsabilidades de los Módulos

#### `config.py`
- Carga y valida variables de entorno
- Proporciona métodos auxiliares para rutas e IDs
- Asegura que toda la configuración requerida esté presente

#### `storage_manager.py`
- Verifica si las imágenes existen en GCS (detección de duplicados)
- Descarga imágenes desde URLs
- Sube imágenes a GCS
- Genera URLs públicas de GCS

#### `bigquery_manager.py`
- Crea tabla de BigQuery con esquema si no existe
- Sube registros de URLs de imágenes a BigQuery
- Proporciona información y estadísticas de la tabla

#### `sheets_manager.py`
- Lee datos desde Google Sheets
- Valida la existencia de columnas
- Opcional: Actualiza la hoja con URLs de GCS

## Esquema de BigQuery

El sistema crea una tabla con el siguiente esquema:

| Columna | Tipo | Modo | Descripción |
|---------|------|------|-------------|
| `original_url` | STRING | REQUIRED | URL original de la imagen desde la hoja |
| `gcs_url` | STRING | REQUIRED | URL de almacenamiento en GCS (gs://...) |
| `filename` | STRING | REQUIRED | Nombre del archivo en GCS |
| `upload_timestamp` | TIMESTAMP | REQUIRED | Cuándo se procesó la imagen |
| `row_index` | INTEGER | REQUIRED | Índice de fila desde la hoja |

## Configuración e Instalación

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

Copia `.env.example` a `.env` y completa tus valores:

```bash
cp .env.example .env
```

Variables requeridas:

```bash
# Configuración de Google Sheets
SPREADSHEET_KEY=tu_id_de_spreadsheet_aqui        # ID de la hoja (de la URL)
WORKSHEET_NAME=Hoja1                              # Nombre de la pestaña
URL_COLUMN_NAME=Foto_URL                          # Columna con URLs de imágenes

# Configuración de Google Cloud Storage
GCS_BUCKET_NAME=nombre-de-tu-bucket               # Nombre del bucket
GCS_FOLDER_PATH=imagenes_descargadas/             # (Opcional) Carpeta dentro del bucket

# Configuración de BigQuery
BQ_PROJECT_ID=tu-proyecto-gcp                     # ID del proyecto de GCP
BQ_DATASET=tu_dataset                             # Nombre del dataset
BQ_TABLE_NAME=image_urls                          # Nombre de la tabla
BQ_WRITE_DISPOSITION=WRITE_APPEND                 # WRITE_APPEND o WRITE_TRUNCATE

# Autenticación
GOOGLE_APPLICATION_CREDENTIALS=./credenciales-service-account.json
```

### 3. Permisos de la Cuenta de Servicio

Tu cuenta de servicio necesita los siguientes permisos:
- **Google Sheets**: Acceso de lectura a la hoja de cálculo
- **Cloud Storage**: Acceso de escritura al bucket
- **BigQuery**: Crear tablas e insertar datos en el dataset

### 4. Ejecutar Localmente

#### Opción A: Servidor Local con HTTP Endpoint (Recomendado)

Usa el script de prueba local que monta el servidor usando Functions Framework:

```bash
# Iniciar el servidor local
./test_local.sh
```

Esto iniciará un servidor en `http://localhost:8080`. En otra terminal, puedes probarlo con:

```bash
# Probar el endpoint
./test_endpoint.sh

# O manualmente con curl
curl -X POST http://localhost:8080
```

El servidor mostrará logs detallados en tiempo real:

```
==========================================
Local Image Storage Function Server
==========================================

✓ Loading environment variables from .env
✓ Activating virtual environment
✓ Installing dependencies...

==========================================
Starting Local Server
==========================================

Function: procesar_imagenes_sheet
URL: http://localhost:8080

To test, run in another terminal:
  curl -X POST http://localhost:8080

Press Ctrl+C to stop the server
==========================================

 * Serving Flask app 'main'
 * Debug mode: on
```

#### Opción B: Ejecución Directa (Sin servidor)

Para una prueba rápida sin servidor HTTP:

```bash
python3 main.py
```

Verás una salida detallada como esta:

```
================================================================================
Starting Image Processing Workflow
================================================================================
✓ Configuration loaded successfully
  - Spreadsheet: 1AbC123...
  - GCS Bucket: mi-bucket-imagenes
  - BigQuery Table: mi-proyecto.mi_dataset.image_urls
✓ All managers initialized

--------------------------------------------------------------------------------
Reading Google Sheets data...
✓ Read 100 rows from sheet

--------------------------------------------------------------------------------
Ensuring BigQuery table exists...
✓ Table ready (current rows: 0)

--------------------------------------------------------------------------------
Processing images from column: Foto_URL
--------------------------------------------------------------------------------
  [0] ✓ Uploaded: 000_imagen1.jpg
  [1] ✓ Uploaded: 001_imagen2.jpg
  [2] ⊙ Already exists: 002_imagen3.jpg
  [3] ✓ Uploaded: 003_imagen4.jpg
  ...

--------------------------------------------------------------------------------
Uploading 100 records to BigQuery...
✓ Successfully inserted 100 rows into BigQuery

================================================================================
PROCESSING COMPLETE
================================================================================
Total rows processed:    100
Skipped (empty URL):     5
Skipped (duplicate):     30
Newly uploaded:          65
Errors:                  0
================================================================================
```

### 5. Desplegar en Cloud Functions

#### Opción A: Con variables de entorno

```bash
gcloud functions deploy procesar_imagenes_sheet \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point procesar_imagenes_sheet \
  --set-env-vars SPREADSHEET_KEY=tu_key,WORKSHEET_NAME=Hoja1,URL_COLUMN_NAME=Foto_URL,GCS_BUCKET_NAME=tu-bucket,BQ_PROJECT_ID=tu-proyecto,BQ_DATASET=tu_dataset,BQ_TABLE_NAME=image_urls
```

#### Opción B: Con Secret Manager (recomendado para producción)

Primero, crea los secretos:

```bash
# Subir credenciales de cuenta de servicio
gcloud secrets create service-account-key \
  --data-file=./credenciales-service-account.json

# Dar acceso a la Cloud Function
gcloud secrets add-iam-policy-binding service-account-key \
  --member=serviceAccount:tu-proyecto@appspot.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

Luego despliega:

```bash
gcloud functions deploy procesar_imagenes_sheet \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point procesar_imagenes_sheet \
  --set-env-vars SPREADSHEET_KEY=tu_key,WORKSHEET_NAME=Hoja1,URL_COLUMN_NAME=Foto_URL,GCS_BUCKET_NAME=tu-bucket,BQ_PROJECT_ID=tu-proyecto,BQ_DATASET=tu_dataset,BQ_TABLE_NAME=image_urls \
  --set-secrets 'GOOGLE_APPLICATION_CREDENTIALS=service-account-key:latest'
```

### 6. Invocar la Cloud Function

Una vez desplegada, puedes invocarla con:

```bash
# Obtener la URL de la función
gcloud functions describe procesar_imagenes_sheet --format='value(httpsTrigger.url)'

# Invocar con curl
curl -X POST https://REGION-PROJECT.cloudfunctions.net/procesar_imagenes_sheet
```

O desde Cloud Scheduler para ejecución automática:

```bash
gcloud scheduler jobs create http procesar-imagenes-diario \
  --schedule="0 2 * * *" \
  --uri="https://REGION-PROJECT.cloudfunctions.net/procesar_imagenes_sheet" \
  --http-method=POST \
  --time-zone="America/Mexico_City"
```

## Flujo de Trabajo

1. **Leer Hoja**: Obtiene datos desde Google Sheets
2. **Crear Tabla BQ**: Asegura que la tabla de BigQuery exista con el esquema apropiado
3. **Procesar Imágenes**:
   - Para cada fila con una URL de imagen:
     - Genera nombre de archivo desde URL e índice de fila
     - Verifica si la imagen ya existe en GCS
     - Si existe: Omite subida, registra como duplicado
     - Si es nueva: Descarga y sube a GCS
     - Agrega registro al lote de BigQuery
4. **Subir a BigQuery**: Inserta todos los registros (nuevos y existentes) a BigQuery
5. **Retornar Estadísticas**: Proporciona resumen de resultados del procesamiento

## Ejemplo de Salida

```json
{
  "status": "completed",
  "statistics": {
    "total_rows": 100,
    "skipped_empty": 5,
    "skipped_duplicate": 30,
    "uploaded": 65,
    "errors": 0,
    "error_details": []
  }
}
```

## Manejo de Errores

- URLs inválidas se registran y omiten
- Errores de red se capturan y reportan
- Fallos de subida a BigQuery se registran
- Todos los errores incluyen números de fila para facilitar la depuración

## Consultar Datos en BigQuery

Para ver las imágenes procesadas:

```sql
-- Ver todas las imágenes
SELECT * FROM `tu-proyecto.tu_dataset.image_urls`
ORDER BY upload_timestamp DESC;

-- Contar imágenes por día
SELECT 
  DATE(upload_timestamp) as fecha,
  COUNT(*) as total_imagenes
FROM `tu-proyecto.tu_dataset.image_urls`
GROUP BY fecha
ORDER BY fecha DESC;

-- Buscar una imagen específica
SELECT * FROM `tu-proyecto.tu_dataset.image_urls`
WHERE original_url LIKE '%nombre-imagen%';
```

## Desarrollo

### Agregar Nuevas Funcionalidades

La arquitectura modular facilita la extensión:

1. **Agregar nuevas fuentes de datos**: Crea un nuevo manager en `modules/`
2. **Agregar nuevos backends de almacenamiento**: Extiende `storage_manager.py`
3. **Agregar nuevas validaciones**: Actualiza `config.py`

### Pruebas

Ejecuta localmente con un archivo `.env` de prueba:

```bash
python3 main.py
```

Revisa la salida de consola para logs detallados de progreso.

## Solución de Problemas

### Error: "Missing required environment variables"
- Verifica que todas las variables en `.env` estén configuradas
- Asegúrate de que el archivo `.env` esté en el directorio raíz

### Error: "Column 'X' not found in sheet"
- Verifica que `URL_COLUMN_NAME` coincida exactamente con el nombre de la columna en tu hoja
- Los nombres de columnas son sensibles a mayúsculas/minúsculas

### Error: "403 Permission Denied"
- Verifica que la cuenta de servicio tenga los permisos correctos
- Asegúrate de que la hoja de Google Sheets esté compartida con el email de la cuenta de servicio

### Las imágenes no se suben
- Verifica que las URLs sean accesibles públicamente
- Revisa los logs para errores específicos de descarga
- Asegúrate de que el bucket de GCS exista y sea accesible

## Licencia

MIT
