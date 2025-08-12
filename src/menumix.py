import pandas as pd
from pathlib import Path

REQUIRED_COLS = ["PLU", "Item Name", "Qty", "Total $", "Net $", "Sales %"]
RENAME_MAP = {
    "PLU": "plu",
    "Item Name": "item_name",
    "Qty": "qty",
    "Total $": "gross_cents",
    "Net $": "net_cents",
    "Sales %": "sales_pct"
}

def load_raw_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")

def validate_headers(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in CSV: {missing}\nFound: {list(df.columns)}")

def rename_to_canonical(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.rename(columns=RENAME_MAP)
    return df[list(RENAME_MAP.values())]

def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["plu"] = df["plu"].astype(str).str.strip()
    df["item_name"] = df["item_name"].str.strip()

    df["item_name"] = df["item_name"].str.replace(r"\s+", " ", regex=True)

    return df

def parse_qty(df: pd.DataFrame) -> pd.DataFrame:
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce")

    df["qty"] = df["qty"].astype("Int64")

    df["is_numeric_qty"] = df["qty"].notna()

    return df

def parse_money_to_cents(df: pd.DataFrame, cols=("gross_cents", "net_cents")) -> pd.DataFrame:
    for col in cols:
        s = df[col].astype(str).str.strip()

        # (123.45) -> -123.45
        s = s.replace(r"\(([^)]+)\)", r"-\1", regex=True)

        # extract first number like -123.45 (ignores words like 'tax:' etc.)
        s = s.str.extract(r"(-?\d+(?:\.\d{1,2})?)", expand=False)

        # dollars -> cents as float, then ROUND to remove float residue
        s = pd.to_numeric(s, errors="coerce")
        s = (s * 100).round(0)   # <- critical

        # swap NaN -> pd.NA, then cast to Pandas' nullable Int64
        s = s.where(s.notna(), pd.NA).astype("Int64")

        df[col] = s
    return df




# def parse_sales_pct(df: pd.DataFrame) -> pd.DataFrame:
#     b 

# def drop_non_item_rows(df: pd.DataFrame) -> pd.DataFrame:
#     b

def main():
    input_path = Path("data/raw/menu_mix_july.csv")
    output_path = Path("data/processed/normalized_sample.csv")

    df_raw = load_raw_csv(input_path)
    validate_headers(df_raw)
    df_raw = df_raw[REQUIRED_COLS]

    df = rename_to_canonical(df_raw)

    df = clean_text_columns(df)

    df = parse_qty(df)

    df = parse_money_to_cents(df)

    print("After rename:"), list(df.columns)
    print(df.head(20))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.head(20).to_csv(output_path, index=False)

    # df.to_csv("debug_output.csv", index=False)


if __name__ == "__main__":
    main()



