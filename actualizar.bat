@echo off
echo =========================================
echo INICIANDO ACTUALIZACION DEL DASHBOARD
echo =========================================

echo.
echo 1. Convirtiendo el archivo Excel a Parquet...
python convertidor.py

echo.
echo 2. Empaquetando datos nuevos...
git add .

echo.
echo 3. Guardando los cambios...
git commit -m "Actualizacion automatica de base de datos"

echo.
echo 4. Enviando datos a la nube...
git push origin main

echo.
echo =========================================
echo ¡PROCESO COMPLETADO EXITOSAMENTE!
echo =========================================
pause