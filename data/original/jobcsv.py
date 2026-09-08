import pandas as pd

df = pd.read_parquet("MineriaProtect\\data\\original\\JobHop_v2_train.parquet")

df.to_csv("MineriaProtect\\data\\original\\JobHop_v2_train.csv", index=False)

print("Conversión completada")