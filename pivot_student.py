from pathlib import Path
import sqlite3
import pandas as pd
ROOT=Path(__file__).resolve().parent
with sqlite3.connect((ROOT/'data'/'warehouse.db').as_uri()+'?mode=ro',uri=True) as con:
    df=pd.read_sql_query('SELECT * FROM sales',con)
print(df.head())
print()

# P1: Pivot province x month, sum(amount), fill_value=0, margins=True
p1 = df.pivot_table(
    index='province',
    columns='month',
    values='amount',
    aggfunc='sum',
    fill_value=0,
    margins=True,
    margins_name='Total'
)
print('=== P1: Province x Month ===')
print(p1)
p1.to_csv(ROOT/'pivot_province_month.csv')
print()

# P2: กรองเดือนกันยายน แล้ว Pivot category x province
df_sep = df[df['month'] == '2026-09']
p2 = df_sep.pivot_table(
    index='category',
    columns='province',
    values='amount',
    aggfunc='sum',
    fill_value=0,
    margins=True,
    margins_name='Total'
)
print('=== P2: September - Category x Province ===')
print(p2)
p2.to_csv(ROOT/'pivot_september.csv')
print()

# P3: assert ตรวจ Grand Total ของ P1 กับ df['amount'].sum()
grand_total = p1.loc['Total', 'Total']
assert grand_total == df['amount'].sum(), f'ไม่ตรง: {grand_total} != {df["amount"].sum()}'
print(f'Grand Total ตรง: {grand_total} บาท')
print()

# ทดลอง Drink filter (แทน Excel PivotTable)
df_drink = df[df['category'] == 'Drink']
p_drink = df_drink.pivot_table(
    index='province',
    columns='month',
    values='amount',
    aggfunc='sum',
    fill_value=0,
    margins=True,
    margins_name='Total'
)
print('=== Drink Only ===')
print(p_drink)
p_drink.to_csv(ROOT/'pivot_drink.csv')
print(f'ยอดรวม Drink: {p_drink.loc["Total","Total"]} บาท')
