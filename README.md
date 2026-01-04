# Almacenamiento de Imágenes en Google Cloud Storage (GCS)

Este proyecto implementa una Google Cloud Function (GCF) diseñada para automatizar la descarga de imágenes desde URLs externas, su almacenamiento en un bucket de Google Cloud Storage y el registro de estas operaciones en BigQuery.

## 🚀 Flujo de Trabajo Detallado

El proceso es lineal y está diseñado para ser eficiente y evitar redundancias. A continuación se detalla paso a paso:

### 1. Inicio y Configuración
- La función se activa (vía HTTP o programada).
- Se inicializan los clientes de **BigQuery** y **Google Cloud Storage** utilizando las credenciales configuradas en las variables de entorno.

### 2. Obtención de URLs de Origen
- La función consulta la tabla definida en `BQ_SOURCE_TABLE` para obtener todas las URLs de imágenes que deben ser procesadas (columna `AdURL`).

### 3. Identificación de Procesados (Detección de Duplicados)
- Se consulta la tabla de destino (`BQ_STORAGE_TABLE`) para obtener una lista de todos los `ImageID` que ya han sido procesados exitosamente en ejecuciones anteriores.
- **¿Cómo se detectan los duplicados?**
    - **Extracción de ID**: Para cada URL, se extrae el nombre del archivo (sin extensión) para usarlo como `ImageID`. Si no hay un nombre claro, se genera un hash MD5 de la URL.
    - **Filtro**: Antes de intentar descargar, la función verifica si el `ImageID` ya existe en:
        1. La lista de IDs ya procesados en BigQuery.
        2. El lote (batch) actual que se está procesando en la ejecución presente.
    - Si el ID ya existe en cualquiera de los dos, la URL se omite automáticamente.

### 4. Procesamiento de Imágenes
Para cada URL nueva:
1. **Descarga**: Se descarga el contenido binario de la imagen. Se utiliza un tiempo de espera (timeout) y se omiten verificaciones de SSL si es necesario para asegurar la descarga.
2. **Carga a GCS**: El contenido se sube al bucket definido en `GCS_BUCKET_NAME`.
    - El archivo se renombra usando su `ImageID` y su extensión original (o `.jpg` por defecto).
    - El objeto se hace **público** automáticamente para permitir su visualización en herramientas como Looker Studio.
3. **Registro en BigQuery**: Se inserta una nueva fila en `BQ_STORAGE_TABLE` con:
    - `OriginalURL`: La URL de origen.
    - `GCSURL`: La URL pública del archivo en GCS.
    - `ImageID`: El identificador único extraído.
    - `ProcessedAt`: Marca de tiempo de la operación.

---

## 🛠️ Configuración y Requisitos

### Variables de Entorno (.env)
Es fundamental que las siguientes variables estén configuradas:
- `BQ_SOURCE_TABLE`: Tabla de BigQuery con las URLs originales (ej: `proyecto.dataset.tabla_origen`).
- `BQ_STORAGE_TABLE`: Tabla de BigQuery donde se registrarán los resultados.
- `GCS_BUCKET_NAME`: Nombre del bucket de GCS.
- `GCS_FOLDER_PATH`: (Opcional) Carpeta dentro del bucket.
- `GOOGLE_APPLICATION_CREDENTIALS`: Ruta al archivo JSON de la Service Account.

### Permisos Necesarios
La Service Account debe tener los siguientes roles:
- `BigQuery Data Editor` y `BigQuery Job User`.
- `Storage Object Admin`.
- `Storage Admin` (si se requiere cambiar permisos de acceso público).

---

## 🔍 Solución de Problemas (Troubleshooting)

Si la función falla o no procesa imágenes, revisa los siguientes puntos:

### 1. Errores de Permisos (403 Forbidden)
- **Síntoma**: Logs indican que no se puede escribir en BigQuery o subir a GCS.
- **Solución**: Verifica que la Service Account tenga los roles mencionados arriba. Si el bucket tiene "Public Access Prevention" activado, la función no podrá hacer los objetos públicos.

### 2. Imágenes no se descargan
- **Síntoma**: `status: failed_download` en la respuesta.
- **Solución**: La URL puede estar rota, requerir autenticación o el servidor de origen puede estar bloqueando peticiones de Google Cloud. Revisa los logs para ver el código de estado HTTP (ej. 404, 500).

### 3. Duplicados no detectados
- **Síntoma**: Se suben imágenes que ya existían.
- **Solución**: Verifica que la columna `ImageID` en BigQuery no esté vacía. Si el formato de la URL cambia (ej. parámetros dinámicos), el `ImageID` extraído podría ser diferente, causando que se trate como una imagen nueva.

### 4. Tabla de BigQuery no existe
- **Síntoma**: Error al intentar registrar la URL.
- **Solución**: La función intenta crear la tabla automáticamente si no existe. Asegúrate de que el Dataset ya esté creado en BigQuery.

---

## 📂 Estructura del Código
- `main.py`: Punto de entrada y lógica principal de orquestación.
- `modules/bigquery_utils.py`: Manejo de consultas e inserciones en BigQuery.
- `modules/gcs_utils.py`: Lógica de carga y gestión de archivos en GCS.
- `modules/image_utils.py`: Utilidades para descargar imágenes y procesar nombres/IDs.
