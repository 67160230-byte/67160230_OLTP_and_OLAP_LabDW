"""โจทย์ต่อยอด ข. - สำเนา warehouse.db เป็น challenge.db แล้วเพิ่มข้อมูลเดือนตุลาคม"""
from pathlib import Path
import shutil, sqlite3

ROOT = Path(__file__).resolve().parent
src = ROOT / 'data' / 'warehouse.db'
dst = ROOT / 'data' / 'challenge.db'

# สำเนาฐานข้อมูล
shutil.copy2(src, dst)

with sqlite3.connect(dst) as con:
    con.execute('PRAGMA foreign_keys = ON')

    # เพิ่มวันที่ 2026-10-01 ใน dim_date
    con.execute(
        "INSERT INTO dim_date VALUES (20261001, '2026-10-01', 2026, '2026-10')"
    )

    # เพิ่มรายการขาย O1007 และ O1008
    # O1007/1: Tea 3 ชิ้นที่ Bangsaen (store_key=1, product_key=1, unit_price=50)
    con.execute(
        "INSERT INTO fact_sales VALUES ('O1007', 1, 20261001, 1, 1, 3, 50)"
    )
    # O1007/2: Cookie 2 ชิ้นที่ Bangsaen (store_key=1, product_key=2, unit_price=80)
    con.execute(
        "INSERT INTO fact_sales VALUES ('O1007', 2, 20261001, 2, 1, 2, 80)"
    )
    # O1008/1: Tea 4 ชิ้นที่ Siam (store_key=2, product_key=1, unit_price=50)
    con.execute(
        "INSERT INTO fact_sales VALUES ('O1008', 1, 20261001, 1, 2, 4, 50)"
    )

    con.commit()

    # ตรวจ foreign key
    fk_check = con.execute('PRAGMA foreign_key_check').fetchall()
    assert len(fk_check) == 0, f'FK error: {fk_check}'

    # ตรวจจำนวนแถวและยอดรวม
    before = con.execute("""
        SELECT 'fact_sales' AS src, COUNT(*) AS rows, SUM(quantity*unit_price) AS total
        FROM fact_sales
        UNION ALL
        SELECT 'sales', COUNT(*), SUM(amount) FROM sales
    """).fetchall()

    print('ตรวจความถูกต้อง:')
    for row in before:
        print(f'  {row[0]}: {row[1]} แถว, {row[2]} บาท')

    # แสดง Pivot ใหม่
    print('\nข้อมูลหลังเพิ่ม:')
    rows = con.execute('SELECT * FROM sales ORDER BY order_id, line_no').fetchall()
    cols = [c[0] for c in con.execute('SELECT * FROM sales LIMIT 1').description]
    print('\t'.join(cols))
    for r in rows:
        print('\t'.join(str(x) for x in r))

    total = con.execute('SELECT SUM(amount) FROM sales').fetchone()[0]
    orders = con.execute('SELECT COUNT(DISTINCT order_id) FROM sales').fetchone()[0]
    print(f'\nยอดรวมใหม่: {total} บาท ({orders} ออเดอร์, {len(rows)} รายการ)')
