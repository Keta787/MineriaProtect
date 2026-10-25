import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from lib import calidad, carga, categorias, competencias, config, periodo

df = carga.leer(config.CON_OUTLIERS)
print("filas:", len(df))

periodo.validar(df)
df["period_time"] = periodo.crear_period_time(df)
df["duracion"] = periodo.duracion_observada(df)
df["duracion_a_corte"] = periodo.duracion_a_corte(df)
df["nivel_ordinal"] = categorias.nivel_ordinal(df)
df["nivel_no_reportado"] = categorias.nivel_no_reportado(df)
df["isco_mayor"] = categorias.isco_mayor(df)
categorias.validar(df)
print("categorias ok")

df = competencias.agregar_banderas(df)
competencias.validar(df)
print("banderas ok")

lim = calidad.limites_iqr(df["duracion"])
print("limites duracion:", lim)
marca = calidad.marcar_outliers(df["duracion"])
print("outliers duracion:", int(marca.sum()), round(100 * marca.mean(), 2), "%")
print("rango outliers:", df.loc[marca, "duracion"].min(), df.loc[marca, "duracion"].max())
print("personas en outliers:", df.loc[marca, "resume_id"].nunique())
print("outliers vigentes:", int((marca & df.es_vigente.eq("True")).sum()))
print()
print(calidad.impacto_outliers(df, "duracion").to_string(index=False))
print()
print(calidad.resumen_outliers(df, ["duracion", "n_skills_essential", "veces_ese_oficio"]).to_string(index=False))
print()
print("duracion describe con outliers:")
print(pd.to_numeric(df.duracion).describe().round(2).to_string())
print()
print("percentiles:", pd.to_numeric(df.duracion).quantile([.5,.9,.95,.99,1]).round(2).to_dict())
print()
print("isco_mayor:", df.isco_mayor.value_counts(dropna=False).to_dict())
print("nivel:", df.university_level.value_counts(dropna=False).to_dict())
print("emparejado:", df.emparejado.value_counts(dropna=False).to_dict())
