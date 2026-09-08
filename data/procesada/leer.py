import pandas as pd

df = pd.read_csv("MineriaProtect/data/procesada/empleos.csv", sep=",")
print(df.columns)
print(df.head())