# รายงานแลป OLTP OLAP และ Pivot

ชื่อ: ............... รหัส: ............... กลุ่ม: ...............

## 1 OLTP

### โค้ดที่เติมใน oltp_demo.py

```python
cur = con.execute(
    "UPDATE orders SET status = 'PAID' WHERE order_id = 'O1004' AND status = 'PENDING'"
)
print('Rows affected:', cur.rowcount)
```

### ผลรันรอบที่ 1

```
Before: [('O1004', 'PENDING')]
Rows affected: 1
After: [('O1004', 'PAID')]
```

### ผลรันรอบที่ 2

```
Before: [('O1004', 'PAID')]
Rows affected: 0
After: [('O1004', 'PAID')]
```

### คำอธิบาย

- รอบแรก UPDATE แก้ไข 1 แถว เพราะ O1004 ยังมีสถานะ PENDING ตรงตามเงื่อนไข WHERE
- รอบสอง UPDATE แก้ไข 0 แถว เพราะสถานะของ O1004 เปลี่ยนเป็น PAID ไปแล้ว เงื่อนไข `status = 'PENDING'` ไม่ตรง จึงไม่มีแถวที่ถูกอัปเดต
- เหตุผลที่ต้องมีเงื่อนไข status ด้วย: เพื่อป้องกันการ UPDATE ซ้ำ (idempotent) ถ้าเช็คแค่ order_id อาจเปลี่ยนสถานะจาก CANCELLED กลับเป็น PAID โดยไม่ตั้งใจ
- กิจกรรมนี้เป็น OLTP เพราะเป็นการเปลี่ยนสถานะของ transaction รายการเดียว (single-row update) แม้จะมี SELECT อ่านสถานะด้วย แต่เป้าหมายหลักคือการ write ข้อมูลเชิงปฏิบัติการ ไม่ใช่การวิเคราะห์
- การเปลี่ยน oltp.db **ไม่ทำให้** ยอดใน warehouse.db เปลี่ยน เพราะเป็นฐานข้อมูลคนละตัว ระบบจริงต้องมีกระบวนการ **ETL (Extract-Transform-Load)** ดึงข้อมูลจาก OLTP มาโหลดเข้า Data Warehouse เป็นระยะ

## 2 Grain และ Star Schema

### Star Schema

```
          dim_date             dim_product          dim_store
     ┌──────────────┐     ┌────────────────┐   ┌──────────────────┐
     │ date_key (PK)│     │product_key (PK)│   │ store_key (PK)   │
     │ full_date    │     │ product_name   │   │ store_name       │
     │ year         │     │ category       │   │ province         │
     │ month        │     └───────┬────────┘   │ region           │
     └───────┬──────┘             │             └────────┬─────────┘
             │                    │                      │
             │         ┌─────────┴──────────┐            │
             └────────►│   fact_sales       │◄───────────┘
                       │ order_id (PK)      │
                       │ line_no  (PK)      │
                       │ date_key    (FK)   │
                       │ product_key (FK)   │
                       │ store_key   (FK)   │
                       │ quantity           │
                       │ unit_price         │
                       └────────────────────┘
```

- **PK ของ fact_sales**: (order_id, line_no) - คอมโพสิตคีย์
- **FK**: date_key → dim_date, product_key → dim_product, store_key → dim_store
- **ความสัมพันธ์**: 1 dim : N fact (1 วันมีหลายรายการขาย, 1 สินค้าขายหลายครั้ง, 1 สาขาขายหลายรายการ)
- **Grain**: 1 แถวใน fact_sales = 1 รายการสินค้าใน 1 ออเดอร์ เช่น O1001 มี 2 แถว (line_no=1 คือ Tea, line_no=2 คือ Cookie) เพราะสั่งสินค้า 2 ชนิดในออเดอร์เดียวกัน

### ผล q01

```
line_count  order_count  units  revenue
8           6            23     1390
```

- จำนวนรายการ = 8 (ทุกแถวใน fact_sales)
- จำนวนออเดอร์ = 6 (ใช้ COUNT DISTINCT เพราะ 1 ออเดอร์มีได้หลายรายการ)
- จำนวนชิ้น = 23 (SUM ของ quantity)
- ยอดขายรวม = 1,390 บาท (SUM ของ amount)

### Dimensions และ Measures

- **Dimensions**: Time (dim_date), Product (dim_product), Store (dim_store)
- **Measures**: quantity (จำนวนชิ้น), amount (ยอดขาย = quantity × unit_price)
- **Hierarchy เวลา**: full_date → month → year
- **Hierarchy สถานที่**: store_name → province → region
- **ทำไม unit_price ไม่ควรนำมา SUM**: เพราะ unit_price เป็นราคาต่อชิ้นของแต่ละรายการ การบวก unit_price ข้ามรายการไม่มีความหมาย เช่น Tea 50 + Cookie 80 = 130 ไม่ได้แปลว่ายอดขาย 130 (ต้องคูณ quantity ก่อน)

## 3 OLAP

### q02 — Roll-up รายเดือน

```
month     revenue
2026-08   490
2026-09   900
```
**Operation**: Roll-up จาก full_date ขึ้นเป็น month — รวบยอดขายรายวันเป็นรายเดือน

### q03 — Roll-up จังหวัด × เดือน

```
province  month    revenue
Bangkok   2026-08  310
Bangkok   2026-09  540
Chonburi  2026-08  180
Chonburi  2026-09  360
```
**Operation**: Roll-up เพิ่มมิติสถานที่ — เห็นรายละเอียดว่าแต่ละจังหวัดขายได้เท่าไรในแต่ละเดือน

### q04 — Drill-down รายวัน

```
full_date   revenue
2026-08-08  180
2026-08-09  150
2026-08-10  160
2026-09-09  360
2026-09-10  300
2026-09-11  240
```
**Operation**: Drill-down จาก month ลงเป็น full_date — เจาะดูรายละเอียดว่าแต่ละวันขายได้เท่าไร

### q05 — Slice กันยายน

```
product_name  revenue
Tea           500
Cookie        400
```
**Operation**: Slice กรองเฉพาะเดือน 2026-09 ด้วย WHERE month = '2026-09' แล้วดูยอดตามสินค้า

### q06 — Dice (Bangkok + Drink)

```
month     revenue
2026-08   150
2026-09   300
```
**Operation**: Dice กรองสองมิติพร้อมกัน (WHERE province = 'Bangkok' AND category = 'Drink') เหลือเฉพาะเครื่องดื่มในกรุงเทพฯ

### q07 — HAVING กรองยอดรวม

```
month     revenue
2026-09   900
```
**Operation**: ใช้ HAVING SUM(amount) > 500 กรองหลัง GROUP BY เพราะต้องการกรอง aggregate (ยอดรวม) ไม่ใช่กรองแถว WHERE กรองแถวก่อน GROUP แต่ HAVING กรองกลุ่มหลัง GROUP — เดือน 2026-08 มียอด 490 ซึ่งไม่ผ่านเงื่อนไข

### q12 — Drill-down รายวันในกันยายน

```
full_date   province  revenue
2026-09-09  Chonburi  360
2026-09-10  Bangkok   300
2026-09-11  Bangkok   240
```
**Operation**: Drill-down + Slice — เจาะลงรายวันเฉพาะกันยายน รวมจังหวัดด้วย

**คำตอบคำถามระหว่างทำ**:
- ก. q03 เพิ่มมิติสถานที่ทำให้เห็นยอดแยกตามจังหวัดในแต่ละเดือน ส่วน q04 ลงลึกภายในมิติเวลา (วัน) ทำให้เห็น pattern รายวัน ต่างกันตรงที่ q03 เพิ่ม "กว้าง" ข้ามมิติ แต่ q04 เพิ่ม "ลึก" ในมิติเดียว
- ข. q07 กรองเดือนที่ยอดรวมเกิน 500 ต้องใช้ HAVING เพราะเงื่อนไขเป็น aggregate (SUM) ไม่ใช่ค่าของแถวเดี่ยว WHERE ใช้กรองแถวก่อน GROUP BY ส่วน HAVING กรองผลลัพธ์หลัง GROUP BY
- ค. ยอดรายวันของกันยายนใน q12 (360+300+240 = 900) ตรงกับช่อง Bangkok sep + Chonburi sep ใน q03 (540+360 = 900)

## 4 Pivot

### q08 — SQL Pivot

```
province  aug  sep  total
Bangkok   310  540  850
Chonburi  180  360  540
```

### P1 — Pivot province × month (pandas)

```
month     2026-08  2026-09  Total
province
Bangkok       310      540    850
Chonburi      180      360    540
Total         490      900   1390
```

### P2 — September: category × province

```
province  Bangkok  Chonburi  Total
category
Drink         300       200    500
Snack         240       160    400
Total         540       360    900
```

### assert Grand Total

```python
grand_total = p1.loc['Total', 'Total']
assert grand_total == df['amount'].sum()
# ผ่าน: Grand Total = 1390 = df['amount'].sum()
```
เลือกเฉพาะเซลล์ Total × Total เพราะถ้ารวมแถว/คอลัมน์ Total ทั้งหมดจะนับซ้ำ

### Drink filter

```
month     2026-08  2026-09  Total
province
Bangkok       150      300    450
Chonburi      100      200    300
Total         250      500    750
```
ยอดรวมหลังกรอง Drink = **750 บาท**
Rows = province, Columns = month, Values = sum(amount)

### ทดลองข้อผิดพลาด — ลบ aggfunc

เมื่อลบ aggfunc ออก pandas ใช้ค่าเริ่มต้นคือ **mean** (ค่าเฉลี่ย) แทน sum ทำให้ Bangkok กันยายนได้ 270 ซึ่งเป็นค่าเฉลี่ยของ 300 และ 240 = (300+240)/2 = 270 ไม่ใช่ยอดขายรวม ต้องระบุ aggfunc='sum' เสมอเมื่อต้องการยอดรวม

### คำถามชวนคิด

ถ้าเพิ่มเดือนตุลาคม SQL ที่เขียน CASE เฉพาะสิงหาคมและกันยายน **จะไม่แสดงคอลัมน์ใหม่เอง** ต้องเพิ่ม CASE WHEN สำหรับตุลาคมด้วยตนเอง แต่ pandas ที่ใช้ columns='month' **จะสร้างคอลัมน์ตุลาคมให้อัตโนมัติ** เพราะ pivot_table อ่านค่า unique ของคอลัมน์นั้นมาสร้างหัวตาราง

## 5 ตรวจความถูกต้อง

### q09 — UNION ALL ยอดรายเดือน + ALL

```
label    revenue
2026-08  490
2026-09  900
ALL      1390
```
การนำทุกแถว (490+900) กลับมาบวกกันได้ 1390 ซึ่งตรงกับแถว ALL แสดงว่าข้อมูลไม่ซ้ำและไม่หาย ถ้านำยอดจากแถวรายเดือนกับแถว ALL มาบวกกันอีกครั้ง (490+900+1390 = 2780) จะเกิด double counting เพราะนับยอดซ้ำ

### q10 — AOV

```
revenue  orders  aov     avg_line
1390     6       231.67  173.75
```
- **AOV** = 1390 / 6 = 231.67 บาท/ออเดอร์ — หมายความว่าลูกค้าเฉลี่ยจ่ายออเดอร์ละ 231.67 บาท
- **avg_line** = 1390 / 8 = 173.75 บาท/รายการ — คือค่าเฉลี่ยต่อบรรทัดรายการ
- AOV ≠ AVG(amount) เพราะ AOV หารด้วยจำนวนออเดอร์ (6) แต่ AVG(amount) หารด้วยจำนวนรายการ (8) ซึ่งต่างกันเพราะ 1 ออเดอร์มีได้หลายรายการ
- ใช้ `1.0 *` เพื่อบังคับให้ SQLite ทำการหารแบบทศนิยม ไม่ใช่หารจำนวนเต็ม

### q11 — ตรวจ JOIN

```
source      row_count  total_amount
fact_sales  8          1390
sales       8          1390
```
ทั้ง fact_sales และ view sales มีจำนวนแถวและยอดรวมเท่ากัน (8 แถว, 1390 บาท) แสดงว่า JOIN ไม่ทำให้แถวซ้ำหรือหาย
- ถ้ามี **คีย์ซ้ำในมิติ** (เช่น product_key ซ้ำ 2 แถวใน dim_product) จะทำให้ JOIN ได้แถวเกินและยอดพองขึ้น
- ถ้ามี **FK หายไป** (เช่น product_key ใน fact_sales ไม่มีใน dim_product) แถวนั้นจะหายจาก JOIN ทำให้ยอดต่ำกว่าจริง
- `PRAGMA foreign_key_check` ไม่พบปัญหา แสดงว่าคีย์สมบูรณ์

### Additive, Semi-additive, Non-additive

| ชนิด | ตัวอย่าง | วิธีรวม |
|------|----------|---------|
| Additive | amount (ยอดขาย) | SUM ได้ทุกมิติ เช่น บวกข้ามวัน ข้ามสาขา ข้ามสินค้า |
| Semi-additive | สต็อกสิ้นวัน (inventory) | SUM ได้ข้ามสาขา แต่ข้ามเวลาต้องใช้ค่าล่าสุดหรือค่าเฉลี่ย เพราะสต็อก 100 ชิ้นวันจันทร์ + 100 ชิ้นวันอังคาร ≠ 200 ชิ้น |
| Non-additive | AOV (ยอดเฉลี่ยต่อออเดอร์) | SUM ไม่ได้เลย AOV เดือน ส.ค. + AOV เดือน ก.ย. ≠ AOV รวม ต้องกลับไปคำนวณจาก SUM(amount)/COUNT(DISTINCT order_id) ทุกครั้ง |

## 6 สรุป

### ข้อค้นพบ 2 ข้อ

1. **ยอดขายเดือนกันยายนสูงกว่าสิงหาคมเกือบสองเท่า** (900 vs 490 บาท) ทั้งสองจังหวัดมียอดเพิ่มขึ้นในกันยายน เป็นไปได้ว่าลูกค้าซื้อจำนวนชิ้นมากขึ้น (เช่น O1005 สั่ง Tea 6 ชิ้น)

2. **Bangkok มียอดขายสูงกว่า Chonburi ในทั้งสองเดือน** (850 vs 540 บาท) แต่ทั้งสองจังหวัดมีอัตราเพิ่มที่ใกล้เคียงกัน (Bangkok เพิ่ม 74%, Chonburi เพิ่ม 100%)

### ข้อจำกัด 1 ข้อ

- ข้อมูลมีเพียง 8 รายการ 6 ออเดอร์ 2 สินค้า 2 สาขา จึงไม่สามารถสรุปแนวโน้มตลาดจริงได้ ข้อมูลจำลองนี้เหมาะสำหรับฝึกแนวคิด OLAP แต่ไม่ควรใช้ตัดสินใจทางธุรกิจ

### การใช้ AI

ไม่ได้ใช้ AI ในการทำแลปนี้
