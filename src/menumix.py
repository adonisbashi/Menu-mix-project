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
HEADER_ROW_VALUES = {
    "subtotal", "total", "grand total", "tax", "tender", "change",
    "report", "header"
}
KNOWN_CATEGORY_HEADERS = {
    "appetizers", "appetizermods", "pizzas", "desserts", "drinks"
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
    df["plu"] = df["plu"].astype("string").str.strip()
    df["plu"] = df["plu"].replace({"": pd.NA})

    df["item_name"] = df["item_name"].astype("string").str.strip()
    df["item_name"] = df["item_name"].str.replace(r"\s+", " ", regex=True)

    return df

def parse_qty(df: pd.DataFrame) -> pd.DataFrame:
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce")

    df["qty"] = df["qty"].astype("Int64")

    df["is_numeric_qty"] = df["qty"].notna()

    return df

def parse_money_simple(df, cols=("gross_cents", "net_cents")):
    for col in cols:
        s = df[col].astype(str).str.strip()
        s = s.str.replace("$", "", regex=False)
        s = s.str.replace(",", "", regex=False)
        s = pd.to_numeric(s, errors="coerce")
        s = (s * 100).round(0)
        s = s.astype("Int64")
        df[col] = s
    return df
    
def parse_sales_pct(df: pd.DataFrame) -> pd.DataFrame:
    df["sales_pct"] = (
        df["sales_pct"]
        .astype(str)
        .str.strip()
        .str.replace("%", "", regex=False)
        .astype(float)
        .div(100)
        .round(3)
    )
    return df

def drop_fully_empty_rows(df):
    for col in ["plu", "item_name"]:
        df[col] = (
            df[col].astype(str).str.strip()
                .replace(r"^$", pd.NA, regex=True)
        )
    key = ["plu", "item_name", "qty", "gross_cents", "net_cents"]
    mask_empty = df[key].isna().all(axis=1)
    print(f"Dropping fully empty rows: {mask_empty.sum()}")

    return df.loc[~mask_empty].copy()

def tag_looks_like_header(df: pd.DataFrame) -> pd.DataFrame:
    is_numeric_qty = df["is_numeric_qty"] if "is_numeric_qty" in df.columns \
                    else pd.to_numeric(df["qty"], errors="coerce").notna()

    name_clean = df["item_name"].astype("string").str.strip().str.lower()
    plu_clean = df["plu"].astype("string").str.strip().str.lower()

# A) lines that live in PLU: store/report/group/category headers
    starts_mask = plu_clean.fillna("").str.startswith(
        ("store:", "report group:", "report date:", "report:", "category:")
    )

    # B) category section titles sitting in item_name with empty PLU
    plu_missing = plu_clean.isna() | (plu_clean == "")
    name_is_category = name_clean.isin({"appetizers","appetizermods","pizzas","desserts","drinks"})

    # C) item_name missing entirely (these have no sellable item)
    name_missing = name_clean.isna()

    # D) qty not numeric (header-ish/junk)
    qty_not_numeric = ~is_numeric_qty

    df["looks_like_header"] = (
        # (df["qty"].isna() != df["is_numeric_quantity"])
        # | (df["gross_cents"].isna() & df["net_cents"].isna())
        # (~is_numeric_qty)
        # | (name_clean.isin(HEADER_ROW_VALUES))
        # | (plu_missing & name_clean.isin(KNOWN_CATEGORY_HEADERS))
        # | ()
        starts_mask
        | (plu_missing & name_is_category)
        | name_missing
        | qty_not_numeric
    )
    return df

def drop_non_item_rows(df: pd.DataFrame) -> pd.DataFrame:
    if "looks_like_header" not in df.columns:
        df = tag_looks_like_header(df)

    flagged = df["looks_like_header"].sum()
    kept_df = df.loc[~df["looks_like_header"]].copy()

    print(f"Flagged as headers: {flagged} rows | Kept: {len(kept_df)} of {len(df)}")

    return kept_df

def main():
    input_path = Path("data/raw/menu_mix_july.csv")
    output_path = Path("data/processed/normalized_sample.csv")

    df_raw = load_raw_csv(input_path)
    validate_headers(df_raw)
    df_raw = df_raw[REQUIRED_COLS]

    df = rename_to_canonical(df_raw)

    df = clean_text_columns(df)

    df = parse_qty(df)

    df = parse_money_simple(df)

    df = parse_sales_pct(df)

    df = drop_fully_empty_rows(df)

    df = tag_looks_like_header(df)
    print("Rows after pre-drop:", len(df))
    print("Flagged as headers:", int(df["looks_like_header"].sum()))
    print("Kept after drop:", int((~df["looks_like_header"]).sum()))

    print("Sample kept rows:")
    print(df.loc[~df["looks_like_header"], ["plu","item_name","qty","gross_cents","net_cents"]].head(10))


    print("PLU starts with matches (sanity):")
    m = df["plu"].astype("string").str.lower().fillna("").str.startswith(
        ("store:", "report group:", "report date:", "report:", "category:")
    )
    print(int(m.sum()))
    print(df.loc[m, ["plu","item_name","qty"]].head(8))


    df = drop_non_item_rows(df)

    assert "is_numeric_qty" in df.columns, "parse_qty must run before tagging"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    df.to_csv("debug_output.csv", index=False)
    print("\nTop 10 by qty:")
    print(df.sort_values("qty", ascending=False).head(20)[["item_name","qty"]])

    print("\nTop 10 by net (dollars):")
    tmp = df.assign(net_dollars=(df["net_cents"] / 100.0))
    print(tmp.sort_values("net_cents", ascending=False).head(20)[["item_name","net_dollars"]])

if __name__ == "__main__":
    main()



