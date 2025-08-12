import pandas as pd

file_path = "/Users/bashi/Documents/repos/Menu-mix-project/data/raw/menu_mix_june.csv"

df = pd.read_csv(file_path, encoding="utf-8-sig", usecols=['PLU', 'Item Name', 'Qty', 'Total $', 'Net $', 'Sales %'])

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


print(df)

