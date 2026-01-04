#!/bin/bash

# Cargar variables de entorno desde .env
if [ -f .env ]; then
    echo "Cargando variables desde .env..."
    # Exportar variables ignorando comentarios y líneas vacías
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: Archivo .env no encontrado."
    exit 1
fi

# Verificar si las variables críticas están seteadas
if [ -z "$GCS_BUCKET_NAME" ] || [ -z "$BQ_SOURCE_TABLE" ] || [ -z "$BQ_STORAGE_TABLE" ]; then
    echo "Error: Faltan variables de entorno críticas en el archivo .env."
    exit 1
fi

# Verificar credenciales de Google
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "Aviso: GOOGLE_APPLICATION_CREDENTIALS no está seteado. Asegúrate de tener permisos para BigQuery y GCS."
fi

# Instalar dependencias si es necesario
if [ "$1" == "--install" ]; then
    echo "Instalando dependencias..."
    python3 -m pip install -r requirements.txt
fi

# Iniciar el functions-framework en segundo plano
echo "Iniciando servidor local de la función..."
python3 -m functions_framework --target process_images --debug &
FUNCTIONS_PID=$!

# Esperar a que el servidor esté listo
sleep 3

# Enviar una petición de prueba
echo "Enviando petición de prueba a http://localhost:8080..."
curl -X POST http://localhost:8080

# Detener el servidor
echo -e "\nDeteniendo servidor local..."
kill $FUNCTIONS_PID
echo "Prueba completada."
