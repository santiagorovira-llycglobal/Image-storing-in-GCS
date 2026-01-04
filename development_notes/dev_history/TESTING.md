# Guía Rápida de Pruebas Locales

## Configuración Inicial (Solo una vez)

1. **Copiar archivo de configuración:**
   ```bash
   cp .env.example .env
   ```

2. **Editar `.env` con tus valores:**
   - `SPREADSHEET_KEY`: ID de tu Google Sheet
   - `WORKSHEET_NAME`: Nombre de la pestaña
   - `URL_COLUMN_NAME`: Nombre de la columna con URLs
   - `GCS_BUCKET_NAME`: Nombre de tu bucket
   - `BQ_PROJECT_ID`, `BQ_DATASET`, `BQ_TABLE_NAME`: Configuración de BigQuery
   - `GOOGLE_APPLICATION_CREDENTIALS`: Ruta a tu archivo JSON de credenciales

3. **Asegurar que tienes las credenciales:**
   - Descarga el archivo JSON de tu cuenta de servicio
   - Colócalo en el directorio del proyecto
   - Actualiza `GOOGLE_APPLICATION_CREDENTIALS` en `.env`

## Probar Localmente

### Método 1: Servidor HTTP Local (Recomendado)

**Terminal 1 - Iniciar servidor:**
```bash
./test_local.sh
```

**Terminal 2 - Probar endpoint:**
```bash
./test_endpoint.sh
```

O manualmente:
```bash
curl -X POST http://localhost:8080
```

### Método 2: Ejecución Directa

```bash
python3 main.py
```

## Símbolos en los Logs

- `✓` = Operación exitosa
- `✗` = Error
- `⊙` = Imagen duplicada (ya existe en GCS)

## Salida Esperada

```
================================================================================
Starting Image Processing Workflow
================================================================================
✓ Configuration loaded successfully
✓ All managers initialized
✓ Read 100 rows from sheet
✓ Table ready (current rows: 0)

Processing images from column: Foto_URL
  [0] ✓ Uploaded: 000_imagen1.jpg
  [1] ⊙ Already exists: 001_imagen2.jpg
  [2] ✓ Uploaded: 002_imagen3.jpg

✓ Successfully inserted 100 rows into BigQuery

PROCESSING COMPLETE
Total rows processed:    100
Skipped (empty URL):     5
Skipped (duplicate):     30
Newly uploaded:          65
Errors:                  0
================================================================================
```

## Solución de Problemas

### "Missing required environment variables"
→ Verifica que `.env` esté configurado correctamente

### "Column 'X' not found in sheet"
→ Verifica que `URL_COLUMN_NAME` coincida exactamente con tu columna

### "403 Permission Denied"
→ Comparte la hoja con el email de la cuenta de servicio

### "Server is not running"
→ Asegúrate de ejecutar `./test_local.sh` primero

## Archivos Importantes

- `test_local.sh` - Inicia el servidor local
- `test_endpoint.sh` - Prueba el endpoint
- `.env` - Configuración (no subir a git)
- `main.py` - Función principal
- `modules/` - Módulos del sistema
