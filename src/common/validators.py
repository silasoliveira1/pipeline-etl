import pandas as pd

class DataValidator:
    def validate_products(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return df
        initial_count = len(df)
        
        # Rule: Price > 0
        valid_df = df[df['price'].astype(float) > 0].copy()
        
        dropped = initial_count - len(valid_df)
        if dropped > 0:
            print(f"WARN: Dropped {dropped} invalid products (Price <= 0)")
        return valid_df

    def validate_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return df
        initial_count = len(df)
        
        # Rule: Email contains @
        # Handle non-string or nulls gracefully
        valid_df = df[df['email'].astype(str).str.contains('@')].copy()
        
        dropped = initial_count - len(valid_df)
        if dropped > 0:
            print(f"WARN: Dropped {dropped} invalid customers (Invalid Email)")
        return valid_df

    def validate_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return df
        initial_count = len(df)
        
        # Rule: Amount >= 0
        valid_df = df[df['total_amount'].astype(float) >= 0].copy()
        
        dropped = initial_count - len(valid_df)
        if dropped > 0:
            print(f"WARN: Dropped {dropped} invalid orders (Negative Amount)")
        return valid_df
