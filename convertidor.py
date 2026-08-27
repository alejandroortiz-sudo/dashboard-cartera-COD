import pandas as pd

print("1. Leyendo tu archivo Excel masivo (Esto usará la RAM de tu PC)...")
# Usamos calamine localmente para que sea rápido
diccionario_hojas = pd.read_excel("Base COD.xlsx", sheet_name=None, engine='calamine')

df_base_list = []
df_comision_list = []

for nombre_hoja, datos_hoja in diccionario_hojas.items():
    if 'comision' in nombre_hoja.lower() or 'comisión' in nombre_hoja.lower():
        df_comision_list.append(datos_hoja)
    else:
        df_base_list.append(datos_hoja)

print("2. Unificando hojas de cálculo...")
if len(df_base_list) > 0:
    columnas_maestras = df_base_list[0].columns
    for i in range(len(df_base_list)):
        df_base_list[i] = df_base_list[i].rename(columns=dict(zip(df_base_list[i].columns, columnas_maestras)))

df_principal = pd.concat(df_base_list, ignore_index=True)

print("3. Estandarizando datos y guardando en formato Parquet...")
# Homologamos los nombres de las columnas a texto
df_principal.columns = df_principal.columns.astype(str)
# Homologamos TODO el contenido de la tabla a texto para evitar errores de pyarrow
df_principal = df_principal.astype(str)
df_principal.to_parquet("base_principal.parquet", index=False)

if df_comision_list:
    df_comisiones = pd.concat(df_comision_list, ignore_index=True)
    df_comisiones.columns = df_comisiones.columns.astype(str)
    # Homologamos también el contenido de comisiones a texto
    df_comisiones = df_comisiones.astype(str)
    df_comisiones.to_parquet("comisiones.parquet", index=False)
    print("4. Hojas de comisiones guardadas exitosamente.")

print("¡Éxito! Ahora tienes los archivos .parquet listos. Ya no necesitamos enviar el Excel a la nube.")