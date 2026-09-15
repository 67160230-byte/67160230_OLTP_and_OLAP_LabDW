from pathlib import Path
import sqlite3
p=Path(__file__).resolve().parent/'data'/'oltp.db'
if not p.exists():raise SystemExit('Run lab.py first')
with sqlite3.connect(p) as con:
    print('Before:',con.execute('SELECT * FROM orders').fetchall())
    # เปลี่ยนสถานะ O1004 จาก PENDING เป็น PAID โดยเช็ค order_id และ status เดิม
    cur = con.execute(
        "UPDATE orders SET status = 'PAID' WHERE order_id = 'O1004' AND status = 'PENDING'"
    )
    print('Rows affected:', cur.rowcount)
    print('After:',con.execute('SELECT * FROM orders').fetchall())
# รอบแรก rowcount = 1 เพราะ O1004 ยังเป็น PENDING
# รอบสอง rowcount = 0 เพราะ O1004 เปลี่ยนเป็น PAID แล้ว WHERE ไม่ตรง
# เงื่อนไข status ป้องกันการ UPDATE ซ้ำ ทำให้ idempotent
