import customtkinter as ctk
import sqlite3
from tkinter import messagebox
from datetime import datetime
import os
import tempfile
import subprocess
import webbrowser
from pathlib import Path


# =========================================================
# SETTINGS
# =========================================================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DB_NAME = "auction.db"
COMMISSION_PERCENT = 10


# =========================================================
# DATABASE FUNCTIONS
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS farmers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        village TEXT,
        mobile TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS buyers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        mobile TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS vegetables(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS auctions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auction_date TEXT NOT NULL,
        farmer_id INTEGER,
        vegetable_id INTEGER,
        buyer_id INTEGER,
        weight REAL NOT NULL,
        price REAL NOT NULL,
        total REAL NOT NULL,
        commission REAL DEFAULT 10,
        farmer_amount REAL NOT NULL,

        FOREIGN KEY (farmer_id) REFERENCES farmers(id),
        FOREIGN KEY (vegetable_id) REFERENCES vegetables(id),
        FOREIGN KEY (buyer_id) REFERENCES buyers(id)
    )
    """)

    conn.commit()
    conn.close()



# =========================================================
# PRINT / REPORT HELPERS
# =========================================================

def html_escape(value):
    import html
    return html.escape("" if value is None else str(value))

def money(value):
    return f"₹{float(value or 0):,.2f}"

def write_and_open_html(filename, html_text):
    path = Path(tempfile.gettempdir()) / filename
    path.write_text(html_text, encoding="utf-8")
    webbrowser.open(path.as_uri())
    return str(path)

def get_farmer_bill_rows(farmer_id, auction_date=None):
    conn = get_connection()
    cur = conn.cursor()
    sql = """
        SELECT a.*, f.name AS farmer_name, f.village, f.mobile,
               v.name AS vegetable_name, b.name AS buyer_name
        FROM auctions a
        JOIN farmers f ON a.farmer_id = f.id
        JOIN vegetables v ON a.vegetable_id = v.id
        JOIN buyers b ON a.buyer_id = b.id
        WHERE a.farmer_id = ?
    """
    params = [farmer_id]
    if auction_date:
        sql += " AND a.auction_date = ?"
        params.append(auction_date)
    sql += " ORDER BY a.id"
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def farmer_bill_html(farmer_id, auction_date=None, copies=1, thermal=False):
    rows = get_farmer_bill_rows(farmer_id, auction_date)
    if not rows:
        return None

    f = rows[0]
    total = sum(float(r["total"] or 0) for r in rows)
    commission = sum(float(r["total"] or 0) * float(r["commission"] or 0) / 100 for r in rows)
    farmer_amount = sum(float(r["farmer_amount"] or 0) for r in rows)

    body_rows = "".join(
        f"<tr><td>{html_escape(r['vegetable_name'])}</td>"
        f"<td>{float(r['weight']):g}</td><td>{money(r['price'])}</td>"
        f"<td>{money(r['total'])}</td></tr>"
        for r in rows
    )

    bill = f"""
    <div class="bill">
      <h3>શાકભાજી ઓક્શન હિસાબ સિસ્ટમ</h3>
      <div class="sub">ખેડૂત બિલ</div>
      <div class="meta"><b>ખેડૂત:</b> {html_escape(f['farmer_name'])}<br>
      <b>ગામ:</b> {html_escape(f['village'])}<br>
      <b>મોબાઇલ:</b> {html_escape(f['mobile'])}<br>
      <b>તારીખ:</b> {html_escape(auction_date or 'બધી તારીખ')}</div>
      <table><tr><th>શાકભાજી</th><th>વજન</th><th>ભાવ</th><th>રકમ</th></tr>
      {body_rows}</table>
      <div class="totals">
        <div>કુલ વેચાણ <b>{money(total)}</b></div>
        <div>કમિશન <b>{money(commission)}</b></div>
        <div class="net">ખેડૂતને ચૂકવવાની રકમ <b>{money(farmer_amount)}</b></div>
      </div>
    </div>
    """

    if thermal:
        css = """
        @page { size: 80mm auto; margin: 3mm; }
        body { font-family: Arial, sans-serif; width: 74mm; margin:0 auto; font-size:12px; }
        .bill { width:100%; } h3,.sub{text-align:center;margin:3px 0;}
        table{width:100%;border-collapse:collapse;margin-top:6px;}
        th,td{border-bottom:1px dashed #000;padding:3px;text-align:left;}
        .totals{margin-top:8px;border-top:1px dashed #000;padding-top:5px;}
        .totals div{display:flex;justify-content:space-between;margin:3px 0;}
        .net{font-weight:bold;}
        """
        return f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{bill}</body></html>"

    css = """
    @page { size: A4 portrait; margin: 8mm; }
    body{font-family:Arial,sans-serif;margin:0;}
    .sheet{display:grid;grid-template-columns:1fr 1fr;gap:6mm;}
    .bill{border:1px solid #000;padding:6mm;min-height:125mm;box-sizing:border-box;page-break-inside:avoid;}
    h3,.sub{text-align:center;margin:2px 0;} .sub{font-weight:bold;}
    .meta{font-size:12px;margin:5px 0;}
    table{width:100%;border-collapse:collapse;font-size:11px;}
    th,td{border:1px solid #555;padding:3px;text-align:left;}
    .totals{font-size:12px;margin-top:6px;}
    .totals div{display:flex;justify-content:space-between;padding:2px 0;}
    .net{font-size:14px;border-top:1px solid #000;margin-top:3px;padding-top:4px;}
    """
    bills = bill * max(1, min(4, int(copies)))
    return f"<html><head><meta charset='utf-8'><style>{css}</style></head><body><div class='sheet'>{bills}</div></body></html>"

def daily_report_html(report_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) AS entries,
               COALESCE(SUM(total),0) AS gross,
               COALESCE(SUM(total * commission / 100),0) AS commission,
               COALESCE(SUM(farmer_amount),0) AS farmer_amount,
               COUNT(DISTINCT farmer_id) AS farmers,
               COUNT(DISTINCT buyer_id) AS buyers,
               COUNT(DISTINCT vegetable_id) AS vegetables,
               COALESCE(SUM(weight),0) AS weight
        FROM auctions WHERE auction_date = ?
    """, (report_date,))
    s = cur.fetchone()

    cur.execute("""
        SELECT v.name, SUM(a.weight) AS weight, SUM(a.total) AS total
        FROM auctions a JOIN vegetables v ON a.vegetable_id=v.id
        WHERE a.auction_date=? GROUP BY v.id ORDER BY total DESC
    """, (report_date,))
    veg = cur.fetchall()

    cur.execute("""
        SELECT b.name, SUM(a.total) AS total
        FROM auctions a JOIN buyers b ON a.buyer_id=b.id
        WHERE a.auction_date=? GROUP BY b.id ORDER BY total DESC
    """, (report_date,))
    buyers = cur.fetchall()
    conn.close()

    veg_rows = "".join(f"<tr><td>{html_escape(r['name'])}</td><td>{float(r['weight']):g} Kg</td><td>{money(r['total'])}</td></tr>" for r in veg) or "<tr><td colspan='3'>કોઈ એન્ટ્રી નથી.</td></tr>"
    buyer_rows = "".join(f"<tr><td>{html_escape(r['name'])}</td><td>{money(r['total'])}</td></tr>" for r in buyers) or "<tr><td colspan='2'>કોઈ એન્ટ્રી નથી.</td></tr>"

    css = """
    @page { size:A4 portrait; margin:12mm; }
    body{font-family:Arial,sans-serif;} h2{text-align:center;margin-bottom:2px;}
    .summary{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:14px 0;}
    .card{border:1px solid #555;padding:9px;border-radius:4px;} .value{font-size:18px;font-weight:bold;margin-top:4px;}
    table{width:100%;border-collapse:collapse;margin-top:8px;} th,td{border:1px solid #777;padding:6px;text-align:left;}
    """
    return f"""<html><head><meta charset='utf-8'><style>{css}</style></head><body>
    <h2>દૈનિક સંપૂર્ણ ઓક્શન રિપોર્ટ</h2><div style='text-align:center'>તારીખ: {html_escape(report_date)}</div>
    <div class='summary'>
      <div class='card'>કુલ એન્ટ્રીઓ<div class='value'>{s['entries']}</div></div>
      <div class='card'>કુલ વજન<div class='value'>{float(s['weight']):g} Kg</div></div>
      <div class='card'>કુલ વેચાણ<div class='value'>{money(s['gross'])}</div></div>
      <div class='card'>કુલ કમિશન<div class='value'>{money(s['commission'])}</div></div>
      <div class='card'>ખેડૂતોને ચૂકવવાની રકમ<div class='value'>{money(s['farmer_amount'])}</div></div>
      <div class='card'>ખરીદદારો પાસેથી લેવાની રકમ<div class='value'>{money(s['gross'])}</div></div>
      <div class='card'>કુલ ખેડૂત<div class='value'>{s['farmers']}</div></div>
      <div class='card'>કુલ ખરીદદારો<div class='value'>{s['buyers']}</div></div>
      <div class='card'>કુલ શાકભાજી પ્રકાર<div class='value'>{s['vegetables']}</div></div>
    </div>
    <h3>શાકભાજી પ્રમાણે હિસાબ</h3><table><tr><th>શાકભાજી</th><th>કુલ વજન</th><th>કુલ રકમ</th></tr>{veg_rows}</table>
    <h3>ખરીદદાર પ્રમાણે હિસાબ</h3><table><tr><th>ખરીદદાર</th><th>કુલ ખરીદી</th></tr>{buyer_rows}</table>
    </body></html>"""

def open_farmer_print(farmer_id, auction_date, thermal=False):
    html_text = farmer_bill_html(farmer_id, auction_date, copies=1 if thermal else 4, thermal=thermal)
    if not html_text:
        messagebox.showwarning("માહિતી", "આ ખેડૂતની કોઈ એન્ટ્રી નથી.")
        return
    write_and_open_html("farmer_bill_thermal.html" if thermal else "farmer_bill_a4.html", html_text)


# =========================================================
# GLOBAL VARIABLES
# =========================================================

farmer_data = {}
buyer_data = {}
vegetable_data = {}

total_label = None
commission_label = None
farmer_amount_label = None

auction_listbox = None

date_entry = None
farmer_combo = None
vegetable_combo = None
buyer_combo = None
weight_entry = None
price_entry = None

app = None
content_frame = None


# =========================================================
# COMMON FUNCTIONS
# =========================================================

def clear_screen():

    for widget in content_frame.winfo_children():
        widget.destroy()


def title_label(text):

    ctk.CTkLabel(
        content_frame,
        text=text,
        font=("Arial", 28, "bold")
    ).pack(pady=(20, 20))


def back_button():

    ctk.CTkButton(
        content_frame,
        text="← પાછા જાઓ",
        command=home_screen,
        width=160,
        height=40
    ).pack(pady=20)


# =========================================================
# LOAD DATA
# =========================================================

def load_farmers():

    global farmer_data

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM farmers ORDER BY name")

    rows = cur.fetchall()

    conn.close()

    farmer_data = {}

    names = []

    for row in rows:

        display = row["name"]

        if row["village"]:
            display += f" ({row['village']})"

        farmer_data[display] = row["id"]

        names.append(display)

    return names


def load_buyers():

    global buyer_data

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM buyers ORDER BY name")

    rows = cur.fetchall()

    conn.close()

    buyer_data = {}

    names = []

    for row in rows:

        display = row["name"]

        buyer_data[display] = row["id"]

        names.append(display)

    return names


def load_vegetables():

    global vegetable_data

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM vegetables ORDER BY name")

    rows = cur.fetchall()

    conn.close()

    vegetable_data = {}

    names = []

    for row in rows:

        vegetable_data[row["name"]] = row["id"]

        names.append(row["name"])

    return names


# =========================================================
# HOME SCREEN
# =========================================================

def home_screen():

    clear_screen()

    title_label("🥬 શાકભાજી ઓક્શન હિસાબ સિસ્ટમ")

    ctk.CTkLabel(
        content_frame,
        text="મુખ્ય મેનુ",
        font=("Arial", 22, "bold")
    ).pack(pady=10)

    button_frame = ctk.CTkFrame(
        content_frame,
        fg_color="transparent"
    )

    button_frame.pack(pady=10)

    buttons = [

        ("👨‍🌾 ખેડૂત ઉમેરો", farmer_screen),

        ("👥 ખરીદનાર ઉમેરો", buyer_screen),

        ("🥬 શાકભાજી ઉમેરો", vegetable_screen),

        ("📝 ઓક્શન એન્ટ્રી કરો", auction_screen),

        ("📊 રિપોર્ટ", report_screen)

    ]

    for text, command in buttons:

        ctk.CTkButton(
            button_frame,
            text=text,
            command=command,
            width=300,
            height=50,
            font=("Arial", 17)
        ).pack(pady=7)


# =========================================================
# FARMER SCREEN
# =========================================================

def farmer_screen():

    clear_screen()

    title_label("👨‍🌾 ખેડૂત ઉમેરો")

    form = ctk.CTkFrame(content_frame)

    form.pack(pady=10)

    ctk.CTkLabel(
        form,
        text="ખેડૂતનું નામ"
    ).pack(pady=(15, 5))

    name_entry = ctk.CTkEntry(
        form,
        width=350
    )

    name_entry.pack(pady=5)

    ctk.CTkLabel(
        form,
        text="ગામ"
    ).pack(pady=5)

    village_entry = ctk.CTkEntry(
        form,
        width=350
    )

    village_entry.pack(pady=5)

    ctk.CTkLabel(
        form,
        text="મોબાઇલ નંબર"
    ).pack(pady=5)

    mobile_entry = ctk.CTkEntry(
        form,
        width=350
    )

    mobile_entry.pack(pady=5)


    def save_farmer():

        name = name_entry.get().strip()

        village = village_entry.get().strip()

        mobile = mobile_entry.get().strip()

        if name == "":

            messagebox.showerror(
                "Error",
                "ખેડૂતનું નામ લખો"
            )

            return

        conn = get_connection()

        cur = conn.cursor()

        try:

            cur.execute(
                """
                INSERT INTO farmers(name,village,mobile)
                VALUES(?,?,?)
                """,
                (
                    name,
                    village,
                    mobile
                )
            )

            conn.commit()

            messagebox.showinfo(
                "Success",
                "ખેડૂત સફળતાપૂર્વક સેવ થયો."
            )

            name_entry.delete(0, "end")

            village_entry.delete(0, "end")

            mobile_entry.delete(0, "end")

        except sqlite3.IntegrityError:

            messagebox.showerror(
                "Error",
                "આ ખેડૂત પહેલેથી હાજર છે."
            )

        conn.close()


    ctk.CTkButton(
        form,
        text="💾 સેવ કરો",
        command=save_farmer,
        width=220,
        height=45
    ).pack(pady=20)

    back_button()


# =========================================================
# BUYER SCREEN
# =========================================================

def buyer_screen():

    clear_screen()

    title_label("👥 ખરીદનાર ઉમેરો")

    form = ctk.CTkFrame(content_frame)

    form.pack(pady=20)

    ctk.CTkLabel(
        form,
        text="ખરીદનારનું નામ"
    ).pack(pady=(20, 5))

    name_entry = ctk.CTkEntry(
        form,
        width=350
    )

    name_entry.pack(pady=5)

    ctk.CTkLabel(
        form,
        text="મોબાઇલ નંબર"
    ).pack(pady=5)

    mobile_entry = ctk.CTkEntry(
        form,
        width=350
    )

    mobile_entry.pack(pady=5)


    def save_buyer():

        name = name_entry.get().strip()

        mobile = mobile_entry.get().strip()

        if name == "":

            messagebox.showerror(
                "Error",
                "ખરીદનારનું નામ લખો"
            )

            return

        conn = get_connection()

        cur = conn.cursor()

        try:

            cur.execute(
                """
                INSERT INTO buyers(name,mobile)
                VALUES(?,?)
                """,
                (
                    name,
                    mobile
                )
            )

            conn.commit()

            messagebox.showinfo(
                "Success",
                "ખરીદનાર સફળતાપૂર્વક સેવ થયો."
            )

            name_entry.delete(0, "end")

            mobile_entry.delete(0, "end")

        except sqlite3.IntegrityError:

            messagebox.showerror(
                "Error",
                "આ ખરીદનાર પહેલેથી હાજર છે."
            )

        conn.close()


    ctk.CTkButton(
        form,
        text="💾 સેવ કરો",
        command=save_buyer,
        width=220,
        height=45
    ).pack(pady=20)

    back_button()


# =========================================================
# VEGETABLE SCREEN
# =========================================================

def vegetable_screen():

    clear_screen()

    title_label("🥬 શાકભાજી ઉમેરો")

    form = ctk.CTkFrame(content_frame)

    form.pack(pady=30)

    ctk.CTkLabel(
        form,
        text="શાકભાજીનું નામ"
    ).pack(pady=(20, 5))

    vegetable_entry = ctk.CTkEntry(
        form,
        width=350
    )

    vegetable_entry.pack(pady=5)


    def save_vegetable():

        name = vegetable_entry.get().strip()

        if name == "":

            messagebox.showerror(
                "Error",
                "શાકભાજીનું નામ લખો"
            )

            return

        conn = get_connection()

        cur = conn.cursor()

        try:

            cur.execute(
                """
                INSERT INTO vegetables(name)
                VALUES(?)
                """,
                (name,)
            )

            conn.commit()

            messagebox.showinfo(
                "Success",
                "શાકભાજી સફળતાપૂર્વક સેવ થયું."
            )

            vegetable_entry.delete(0, "end")

        except sqlite3.IntegrityError:

            messagebox.showerror(
                "Error",
                "આ શાકભાજી પહેલેથી હાજર છે."
            )

        conn.close()


    ctk.CTkButton(
        form,
        text="💾 સેવ કરો",
        command=save_vegetable,
        width=220,
        height=45
    ).pack(pady=20)

    back_button()


# =========================================================
# CALCULATE AUCTION
# =========================================================

def calculate_amount(event=None):

    global total_label
    global commission_label
    global farmer_amount_label

    try:

        weight = float(weight_entry.get())

        price = float(price_entry.get())

        total = weight * price

        commission = (
            total * COMMISSION_PERCENT / 100
        )

        farmer_amount = total - commission

        total_label.configure(
            text=f"કુલ : ₹ {total:.2f}"
        )

        commission_label.configure(
            text=f"કમિશન : ₹ {commission:.2f}"
        )

        farmer_amount_label.configure(
            text=f"ખેડૂતને : ₹ {farmer_amount:.2f}"
        )

    except:

        total_label.configure(
            text="કુલ : ₹ 0.00"
        )

        commission_label.configure(
            text="કમિશન : ₹ 0.00"
        )

        farmer_amount_label.configure(
            text="ખેડૂતને : ₹ 0.00"
        )


# =========================================================
# SAVE AUCTION
# =========================================================

def save_auction():

    auction_date = date_entry.get().strip()

    farmer_name = farmer_combo.get()

    vegetable_name = vegetable_combo.get()

    buyer_name = buyer_combo.get()

    weight_text = weight_entry.get().strip()

    price_text = price_entry.get().strip()

    if (
        auction_date == ""
        or farmer_name == ""
        or vegetable_name == ""
        or buyer_name == ""
        or weight_text == ""
        or price_text == ""
    ):

        messagebox.showerror(
            "Error",
            "બધી માહિતી ભરો."
        )

        return

    try:

        weight = float(weight_text)

        price = float(price_text)

    except:

        messagebox.showerror(
            "Error",
            "વજન અને ભાવ નંબર માં લખો."
        )

        return

    total = weight * price

    commission = (
        total * COMMISSION_PERCENT / 100
    )

    farmer_amount = total - commission

    farmer_id = farmer_data.get(farmer_name)

    vegetable_id = vegetable_data.get(vegetable_name)

    buyer_id = buyer_data.get(buyer_name)

    if not farmer_id or not vegetable_id or not buyer_id:

        messagebox.showerror(
            "Error",
            "ખેડૂત, શાકભાજી અથવા ખરીદનાર પસંદ કરો."
        )

        return

    conn = get_connection()

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO auctions(
            auction_date,
            farmer_id,
            vegetable_id,
            buyer_id,
            weight,
            price,
            total,
            commission,
            farmer_amount
        )
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            auction_date,
            farmer_id,
            vegetable_id,
            buyer_id,
            weight,
            price,
            total,
            COMMISSION_PERCENT,
            farmer_amount
        )
    )

    conn.commit()

    conn.close()

    messagebox.showinfo(
        "Success",
        "ઓક્શન એન્ટ્રી સફળતાપૂર્વક સેવ થઈ."
    )

    weight_entry.delete(0, "end")

    price_entry.delete(0, "end")

    calculate_amount()

    load_auction_history()


# =========================================================
# LOAD AUCTION HISTORY
# =========================================================

def load_auction_history():

    if auction_listbox is None:
        return

    auction_listbox.delete(
        "1.0",
        "end"
    )

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.*,
            f.name AS farmer_name,
            v.name AS vegetable_name,
            b.name AS buyer_name

        FROM auctions a

        LEFT JOIN farmers f
        ON a.farmer_id = f.id

        LEFT JOIN vegetables v
        ON a.vegetable_id = v.id

        LEFT JOIN buyers b
        ON a.buyer_id = b.id

        ORDER BY a.id DESC

        LIMIT 50
    """)

    rows = cur.fetchall()

    conn.close()

    if len(rows) == 0:

        auction_listbox.insert(
            "end",
            "હજુ કોઈ એન્ટ્રી નથી."
        )

        return

    for row in rows:

        text = (
            f"{row['auction_date']} | "
            f"ખેડૂત: {row['farmer_name']} | "
            f"{row['vegetable_name']} | "
            f"{row['weight']} Kg × ₹{row['price']} "
            f"= ₹{row['total']:.2f} | "
            f"ખરીદનાર: {row['buyer_name']}\n"
        )

        auction_listbox.insert(
            "end",
            text
        )


# =========================================================
# AUCTION SCREEN
# =========================================================

def auction_screen():

    global date_entry
    global farmer_combo
    global vegetable_combo
    global buyer_combo
    global weight_entry
    global price_entry

    global total_label
    global commission_label
    global farmer_amount_label

    global auction_listbox

    clear_screen()

    title_label("📝 ઓક્શન એન્ટ્રી")

    main = ctk.CTkFrame(
        content_frame
    )

    main.pack(pady=5)

    today = datetime.now().strftime(
        "%d-%m-%Y"
    )

    # DATE

    ctk.CTkLabel(
        main,
        text="તારીખ"
    ).grid(
        row=0,
        column=0,
        padx=10,
        pady=10
    )

    date_entry = ctk.CTkEntry(
        main,
        width=300
    )

    date_entry.grid(
        row=0,
        column=1,
        padx=10,
        pady=10
    )

    date_entry.insert(
        0,
        today
    )

    # FARMER

    ctk.CTkLabel(
        main,
        text="ખેડૂત"
    ).grid(
        row=1,
        column=0,
        padx=10,
        pady=10
    )

    farmer_combo = ctk.CTkComboBox(
        main,
        values=load_farmers(),
        width=300
    )

    farmer_combo.grid(
        row=1,
        column=1,
        padx=10,
        pady=10
    )

    # VEGETABLE

    ctk.CTkLabel(
        main,
        text="શાકભાજી"
    ).grid(
        row=2,
        column=0,
        padx=10,
        pady=10
    )

    vegetable_combo = ctk.CTkComboBox(
        main,
        values=load_vegetables(),
        width=300
    )

    vegetable_combo.grid(
        row=2,
        column=1,
        padx=10,
        pady=10
    )

    # BUYER

    ctk.CTkLabel(
        main,
        text="ખરીદનાર"
    ).grid(
        row=3,
        column=0,
        padx=10,
        pady=10
    )

    buyer_combo = ctk.CTkComboBox(
        main,
        values=load_buyers(),
        width=300
    )

    buyer_combo.grid(
        row=3,
        column=1,
        padx=10,
        pady=10
    )

    # WEIGHT

    ctk.CTkLabel(
        main,
        text="વજન (Kg)"
    ).grid(
        row=4,
        column=0,
        padx=10,
        pady=10
    )

    weight_entry = ctk.CTkEntry(
        main,
        width=300,
        placeholder_text="જેમ કે 50"
    )

    weight_entry.grid(
        row=4,
        column=1,
        padx=10,
        pady=10
    )

    weight_entry.bind(
        "<KeyRelease>",
        calculate_amount
    )

    # PRICE

    ctk.CTkLabel(
        main,
        text="ભાવ પ્રતિ Kg"
    ).grid(
        row=5,
        column=0,
        padx=10,
        pady=10
    )

    price_entry = ctk.CTkEntry(
        main,
        width=300,
        placeholder_text="જેમ કે 30"
    )

    price_entry.grid(
        row=5,
        column=1,
        padx=10,
        pady=10
    )

    price_entry.bind(
        "<KeyRelease>",
        calculate_amount
    )


    # TOTAL AREA

    amount_frame = ctk.CTkFrame(
        content_frame,
        fg_color="transparent"
    )

    amount_frame.pack(
        pady=15
    )

    total_label = ctk.CTkLabel(
        amount_frame,
        text="કુલ : ₹ 0.00",
        font=("Arial", 18, "bold")
    )

    total_label.grid(
        row=0,
        column=0,
        padx=20
    )

    commission_label = ctk.CTkLabel(
        amount_frame,
        text="કમિશન : ₹ 0.00",
        font=("Arial", 18, "bold")
    )

    commission_label.grid(
        row=0,
        column=1,
        padx=20
    )

    farmer_amount_label = ctk.CTkLabel(
        amount_frame,
        text="ખેડૂતને : ₹ 0.00",
        font=("Arial", 18, "bold")
    )

    farmer_amount_label.grid(
        row=0,
        column=2,
        padx=20
    )


    # BUTTONS

    button_frame = ctk.CTkFrame(
        content_frame,
        fg_color="transparent"
    )

    button_frame.pack(
        pady=10
    )

    ctk.CTkButton(
        button_frame,
        text="💾 હિસાબ સેવ કરો",
        command=save_auction,
        width=200,
        height=45
    ).grid(
        row=0,
        column=0,
        padx=10
    )

    ctk.CTkButton(
        button_frame,
        text="🧹 એન્ટ્રી સાફ કરો",
        command=lambda: (
            weight_entry.delete(0, "end"),
            price_entry.delete(0, "end"),
            calculate_amount()
        ),
        width=200,
        height=45
    ).grid(
        row=0,
        column=1,
        padx=10
    )


    # HISTORY

    ctk.CTkLabel(
        content_frame,
        text="📋 આજની એન્ટ્રીઓ",
        font=("Arial", 20, "bold")
    ).pack(
        pady=(15, 5)
    )

    auction_listbox = ctk.CTkTextbox(
        content_frame,
        width=800,
        height=250
    )

    auction_listbox.pack(
        pady=10
    )

    load_auction_history()

    back_button()


# =========================================================
# REPORT SCREEN
# =========================================================

def report_screen():
    clear_screen()
    title_label("📊 રિપોર્ટ અને હિસાબ")

    ctk.CTkButton(content_frame, text="🧾 ખેડૂતનું બિલ પ્રિન્ટ", command=farmer_bill_screen,
                  width=350, height=55, font=("Arial", 18)).pack(pady=10)
    ctk.CTkButton(content_frame, text="👥 ખરીદનારનું બિલ પ્રિન્ટ", command=buyer_bill_screen,
                  width=350, height=55, font=("Arial", 18)).pack(pady=10)

    ctk.CTkLabel(content_frame, text="નવી પ્રિન્ટ અને કુલ હિસાબ સુવિધા",
                 font=("Arial", 20, "bold")).pack(pady=(20, 8))

    selected_farmer = ctk.StringVar()
    selected_date = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

    ctk.CTkLabel(content_frame, text="ખેડૂત પસંદ કરો").pack(pady=(6, 2))
    values = load_farmers()
    combo = ctk.CTkComboBox(content_frame, values=values, variable=selected_farmer, width=420)
    combo.pack(pady=4)

    ctk.CTkLabel(content_frame, text="તારીખ (YYYY-MM-DD)").pack(pady=(8, 2))
    ctk.CTkEntry(content_frame, textvariable=selected_date, width=220).pack(pady=4)

    def selected_farmer_id():
        name = selected_farmer.get().strip()
        if not name or name not in farmer_data:
            messagebox.showwarning("માહિતી", "ખેડૂત પસંદ કરો.")
            return None
        return farmer_data[name]

    def a4():
        fid = selected_farmer_id()
        if fid:
            open_farmer_print(fid, selected_date.get().strip(), False)

    def thermal():
        fid = selected_farmer_id()
        if fid:
            open_farmer_print(fid, selected_date.get().strip(), True)

    ctk.CTkButton(content_frame, text="📄 A4 પેપર પર 4 બિલ", command=a4,
                  width=350, height=45).pack(pady=6)
    ctk.CTkButton(content_frame, text="🧾 Thermal Bill", command=thermal,
                  width=350, height=45).pack(pady=6)

    def daily():
        d = selected_date.get().strip()
        if not d:
            messagebox.showwarning("માહિતી", "તારીખ લખો.")
            return
        write_and_open_html("daily_auction_report.html", daily_report_html(d))

    ctk.CTkButton(content_frame, text="📊 તે તારીખનો સંપૂર્ણ ઓક્શન રિપોર્ટ",
                  command=daily, width=380, height=52, font=("Arial", 17)).pack(pady=(18, 10))

    ctk.CTkButton(content_frame, text="📊 સંપૂર્ણ હિસાબ (જૂનો રિપોર્ટ)",
                  command=full_report_screen, width=350, height=45).pack(pady=6)
    back_button()

# =========================================================
# CREATE BILL FILE
# =========================================================

def print_bill(text):

    try:

        temp_folder = tempfile.gettempdir()

        file_path = os.path.join(
            temp_folder,
            "auction_bill.txt"
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(text)

        if os.name == "nt":

            os.startfile(
                file_path,
                "print"
            )

            messagebox.showinfo(
                "Print",
                "Bill પ્રિન્ટ માટે મોકલવામાં આવ્યું છે."
            )

        else:

            subprocess.run(
                ["lp", file_path]
            )

    except Exception as e:

        messagebox.showerror(
            "Print Error",
            str(e)
        )


# =========================================================
# FARMER BILL SCREEN
# =========================================================

def farmer_bill_screen():

    clear_screen()

    title_label("🧾 ખેડૂતનું બિલ")

    farmers = load_farmers()

    ctk.CTkLabel(
        content_frame,
        text="ખેડૂત પસંદ કરો"
    ).pack(
        pady=5
    )

    farmer_select = ctk.CTkComboBox(
        content_frame,
        values=farmers,
        width=400
    )

    farmer_select.pack(
        pady=10
    )

    bill_box = ctk.CTkTextbox(
        content_frame,
        width=850,
        height=400,
        font=("Courier New", 14)
    )

    bill_box.pack(
        pady=15
    )


    def generate_bill():

        selected = farmer_select.get()

        farmer_id = farmer_data.get(
            selected
        )

        if not farmer_id:

            messagebox.showerror(
                "Error",
                "ખેડૂત પસંદ કરો."
            )

            return

        conn = get_connection()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                a.*,
                f.name AS farmer_name,
                f.village,
                f.mobile,
                v.name AS vegetable_name,
                b.name AS buyer_name

            FROM auctions a

            JOIN farmers f
            ON a.farmer_id = f.id

            JOIN vegetables v
            ON a.vegetable_id = v.id

            JOIN buyers b
            ON a.buyer_id = b.id

            WHERE a.farmer_id = ?

            ORDER BY a.id DESC
            """,
            (farmer_id,)
        )

        rows = cur.fetchall()

        conn.close()

        if not rows:

            bill_box.delete(
                "1.0",
                "end"
            )

            bill_box.insert(
                "end",
                "આ ખેડૂતની કોઈ એન્ટ્રી નથી."
            )

            return

        farmer = rows[0]

        total = 0

        commission_total = 0

        farmer_total = 0

        bill = ""

        bill += "========================================\n"

        bill += "      શાકભાજી ઓક્શન હિસાબ સિસ્ટમ\n"

        bill += "              ખેડૂત બિલ\n"

        bill += "========================================\n\n"

        bill += f"ખેડૂત : {farmer['farmer_name']}\n"

        bill += f"ગામ   : {farmer['village'] or ''}\n"

        bill += f"મોબાઇલ: {farmer['mobile'] or ''}\n"

        bill += "\n----------------------------------------\n"

        for row in rows:

            total += row["total"]

            commission = (
                row["total"]
                * row["commission"]
                / 100
            )

            commission_total += commission

            farmer_total += row["farmer_amount"]

            bill += (
                f"તારીખ: {row['auction_date']}\n"
            )

            bill += (
                f"{row['vegetable_name']} | "
                f"{row['weight']} Kg × "
                f"₹{row['price']:.2f}\n"
            )

            bill += (
                f"કુલ: ₹{row['total']:.2f}\n\n"
            )

        bill += "----------------------------------------\n"

        bill += f"કુલ વેચાણ      : ₹ {total:.2f}\n"

        bill += f"કમિશન ({COMMISSION_PERCENT}%) : ₹ {commission_total:.2f}\n"

        bill += f"ખેડૂતને ચૂકવવાના : ₹ {farmer_total:.2f}\n"

        bill += "========================================\n"

        bill += (
            "\nઆભાર!\n"
        )

        bill_box.delete(
            "1.0",
            "end"
        )

        bill_box.insert(
            "end",
            bill
        )


    def print_current_bill():

        text = bill_box.get(
            "1.0",
            "end"
        ).strip()

        if text == "":

            messagebox.showerror(
                "Error",
                "પહેલા બિલ બનાવો."
            )

            return

        print_bill(text)


    button_frame = ctk.CTkFrame(
        content_frame,
        fg_color="transparent"
    )

    button_frame.pack(
        pady=10
    )

    ctk.CTkButton(
        button_frame,
        text="📋 બિલ બનાવો",
        command=generate_bill,
        width=200,
        height=45
    ).grid(
        row=0,
        column=0,
        padx=10
    )

    ctk.CTkButton(
        button_frame,
        text="🖨️ બિલ પ્રિન્ટ કરો",
        command=print_current_bill,
        width=200,
        height=45
    ).grid(
        row=0,
        column=1,
        padx=10
    )

    ctk.CTkButton(
        content_frame,
        text="← પાછા જાઓ",
        command=report_screen,
        width=180
    ).pack(
        pady=15
    )


# =========================================================
# BUYER BILL SCREEN
# =========================================================

def buyer_bill_screen():

    clear_screen()

    title_label("👥 ખરીદનારનું બિલ")

    buyers = load_buyers()

    ctk.CTkLabel(
        content_frame,
        text="ખરીદનાર પસંદ કરો"
    ).pack(
        pady=5
    )

    buyer_select = ctk.CTkComboBox(
        content_frame,
        values=buyers,
        width=400
    )

    buyer_select.pack(
        pady=10
    )

    bill_box = ctk.CTkTextbox(
        content_frame,
        width=850,
        height=400,
        font=("Courier New", 14)
    )

    bill_box.pack(
        pady=15
    )


    def generate_bill():

        selected = buyer_select.get()

        buyer_id = buyer_data.get(
            selected
        )

        if not buyer_id:

            messagebox.showerror(
                "Error",
                "ખરીદનાર પસંદ કરો."
            )

            return

        conn = get_connection()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                a.*,
                f.name AS farmer_name,
                v.name AS vegetable_name,
                b.name AS buyer_name,
                b.mobile AS buyer_mobile

            FROM auctions a

            JOIN farmers f
            ON a.farmer_id = f.id

            JOIN vegetables v
            ON a.vegetable_id = v.id

            JOIN buyers b
            ON a.buyer_id = b.id

            WHERE a.buyer_id = ?

            ORDER BY a.id DESC
            """,
            (buyer_id,)
        )

        rows = cur.fetchall()

        conn.close()

        if not rows:

            bill_box.delete(
                "1.0",
                "end"
            )

            bill_box.insert(
                "end",
                "આ ખરીદનારની કોઈ એન્ટ્રી નથી."
            )

            return

        buyer = rows[0]

        total = 0

        bill = ""

        bill += "========================================\n"

        bill += "      શાકભાજી ઓક્શન હિસાબ સિસ્ટમ\n"

        bill += "            ખરીદનાર બિલ\n"

        bill += "========================================\n\n"

        bill += f"ખરીદનાર : {buyer['buyer_name']}\n"

        bill += f"મોબાઇલ  : {buyer['buyer_mobile'] or ''}\n"

        bill += "\n----------------------------------------\n"

        for row in rows:

            total += row["total"]

            bill += (
                f"તારીખ: {row['auction_date']}\n"
            )

            bill += (
                f"ખેડૂત: {row['farmer_name']}\n"
            )

            bill += (
                f"{row['vegetable_name']} | "
                f"{row['weight']} Kg × "
                f"₹{row['price']:.2f}\n"
            )

            bill += (
                f"રકમ: ₹{row['total']:.2f}\n\n"
            )

        bill += "----------------------------------------\n"

        bill += f"કુલ ચૂકવવાની રકમ : ₹ {total:.2f}\n"

        bill += "========================================\n"

        bill += "\nઆભાર!\n"

        bill_box.delete(
            "1.0",
            "end"
        )

        bill_box.insert(
            "end",
            bill
        )


    def print_current_bill():

        text = bill_box.get(
            "1.0",
            "end"
        ).strip()

        if text == "":

            messagebox.showerror(
                "Error",
                "પહેલા બિલ બનાવો."
            )

            return

        print_bill(text)


    button_frame = ctk.CTkFrame(
        content_frame,
        fg_color="transparent"
    )

    button_frame.pack(
        pady=10
    )

    ctk.CTkButton(
        button_frame,
        text="📋 બિલ બનાવો",
        command=generate_bill,
        width=200,
        height=45
    ).grid(
        row=0,
        column=0,
        padx=10
    )

    ctk.CTkButton(
        button_frame,
        text="🖨️ બિલ પ્રિન્ટ કરો",
        command=print_current_bill,
        width=200,
        height=45
    ).grid(
        row=0,
        column=1,
        padx=10
    )

    ctk.CTkButton(
        content_frame,
        text="← પાછા જાઓ",
        command=report_screen,
        width=180
    ).pack(
        pady=15
    )


# =========================================================
# FULL REPORT
# =========================================================

def full_report_screen():

    clear_screen()

    title_label("📊 સંપૂર્ણ હિસાબ")

    report_box = ctk.CTkTextbox(
        content_frame,
        width=900,
        height=500,
        font=("Courier New", 14)
    )

    report_box.pack(
        pady=15
    )

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total_entries,
            COALESCE(SUM(total), 0) AS total_sales,
            COALESCE(SUM(farmer_amount), 0) AS total_farmer_amount
        FROM auctions
    """)

    result = cur.fetchone()

    conn.close()

    total_entries = result["total_entries"]

    total_sales = result["total_sales"]

    total_commission = (
        total_sales
        - result["total_farmer_amount"]
    )

    report = ""

    report += "========================================\n"

    report += "       શાકભાજી ઓક્શન સંપૂર્ણ હિસાબ\n"

    report += "========================================\n\n"

    report += f"કુલ ઓક્શન એન્ટ્રી : {total_entries}\n\n"

    report += f"કુલ વેચાણ        : ₹ {total_sales:.2f}\n"

    report += f"કુલ કમિશન       : ₹ {total_commission:.2f}\n"

    report += (
        f"ખેડૂતોને ચૂકવવાની રકમ : "
        f"₹ {result['total_farmer_amount']:.2f}\n"
    )

    report += "\n========================================\n"

    report_box.insert(
        "end",
        report
    )

    ctk.CTkButton(
        content_frame,
        text="← પાછા જાઓ",
        command=report_screen,
        width=180
    ).pack(
        pady=15
    )



# =========================================================
# ENHANCED FEATURES
# =========================================================

def get_commission_percent():
    conn=get_connection(); cur=conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    cur.execute("SELECT value FROM settings WHERE key='commission_percent'")
    row=cur.fetchone()
    if not row:
        cur.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('commission_percent','10')")
        conn.commit(); value=10.0
    else:
        value=float(row["value"])
    conn.close()
    return value

def refresh_commission():
    global COMMISSION_PERCENT
    COMMISSION_PERCENT=get_commission_percent()

def settings_screen():
    clear_screen(); title_label("⚙️ Settings")
    refresh_commission()
    ctk.CTkLabel(content_frame,text="કમિશન ટકા (%)",font=("Arial",18,"bold")).pack(pady=(30,5))
    e=ctk.CTkEntry(content_frame,width=250); e.pack(pady=5); e.insert(0,str(COMMISSION_PERCENT))
    def save():
        try: v=float(e.get())
        except: messagebox.showerror("Error","માન્ય કમિશન ટકા લખો."); return
        if v<0 or v>100: messagebox.showerror("Error","કમિશન 0 થી 100 વચ્ચે હોવું જોઈએ."); return
        conn=get_connection(); cur=conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        cur.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('commission_percent',?)",(str(v),))
        conn.commit(); conn.close(); refresh_commission()
        messagebox.showinfo("Success",f"કમિશન {v:g}% સેવ થયું.")
    ctk.CTkButton(content_frame,text="💾 કમિશન સેવ કરો",command=save,width=250,height=45).pack(pady=15)
    back_button()

def manage_people_screen(kind):
    clear_screen()
    table = "farmers" if kind=="farmer" else "buyers"
    title_label("👨‍🌾 ખેડૂત વ્યવસ્થા" if kind=="farmer" else "👥 ખરીદનાર વ્યવસ્થા")
    values = load_farmers() if kind=="farmer" else load_buyers()
    combo=ctk.CTkComboBox(content_frame,values=values,width=420); combo.pack(pady=(30,10))
    def delete():
        name=combo.get().strip()
        data=farmer_data if kind=="farmer" else buyer_data
        item_id=data.get(name)
        if not item_id: messagebox.showwarning("માહિતી","નામ પસંદ કરો."); return
        conn=get_connection(); cur=conn.cursor()
        col="farmer_id" if kind=="farmer" else "buyer_id"
        cur.execute(f"SELECT COUNT(*) AS c FROM auctions WHERE {col}=?",(item_id,))
        used=cur.fetchone()["c"]
        if used:
            conn.close(); messagebox.showwarning("માહિતી","આ નામ સાથે ઓક્શન એન્ટ્રીઓ છે, તેથી સુરક્ષા માટે Delete કરી શકાતું નથી."); return
        if not messagebox.askyesno("Confirm",f"'{name}' ને Delete કરવું છે?"): conn.close(); return
        cur.execute(f"DELETE FROM {table} WHERE id=?",(item_id,)); conn.commit(); conn.close()
        if kind=="farmer": load_farmers()
        else: load_buyers()
        combo.configure(values=load_farmers() if kind=="farmer" else load_buyers()); combo.set("")
        messagebox.showinfo("Success","નામ Delete થયું.")
    ctk.CTkButton(content_frame,text="🗑️ પસંદ કરેલું નામ Delete કરો",command=delete,width=320,height=45).pack(pady=10)
    back_button()

def farmer_screen():
    clear_screen(); title_label("👨‍🌾 ખેડૂત ઉમેરો")
    form=ctk.CTkFrame(content_frame); form.pack(pady=10)
    fields=[]
    for label in ["ખેડૂતનું નામ","ગામ","મોબાઇલ નંબર"]:
        ctk.CTkLabel(form,text=label).pack(pady=(10,3)); e=ctk.CTkEntry(form,width=380); e.pack(pady=3); fields.append(e)
    def save():
        vals=[x.get().strip() for x in fields]
        if not vals[0]: messagebox.showerror("Error","ખેડૂતનું નામ લખો"); return
        try:
            conn=get_connection(); cur=conn.cursor(); cur.execute("INSERT INTO farmers(name,village,mobile) VALUES(?,?,?)",vals); conn.commit(); conn.close()
            load_farmers(); [x.delete(0,"end") for x in fields]; messagebox.showinfo("Success","ખેડૂત સફળતાપૂર્વક સેવ થયો.")
        except sqlite3.IntegrityError: messagebox.showerror("Error","આ ખેડૂત પહેલેથી હાજર છે.")
    ctk.CTkButton(form,text="💾 સેવ કરો",command=save,width=250,height=45).pack(pady=15)
    ctk.CTkButton(form,text="🗑️ ખેડૂત Delete / વ્યવસ્થા",command=lambda:manage_people_screen("farmer"),width=250,height=42).pack(pady=5)
    back_button()

def buyer_screen():
    clear_screen(); title_label("👥 ખરીદનાર ઉમેરો")
    form=ctk.CTkFrame(content_frame); form.pack(pady=20)
    fields=[]
    for label in ["ખરીદનારનું નામ","મોબાઇલ નંબર"]:
        ctk.CTkLabel(form,text=label).pack(pady=(10,3)); e=ctk.CTkEntry(form,width=380); e.pack(pady=3); fields.append(e)
    def save():
        vals=[x.get().strip() for x in fields]
        if not vals[0]: messagebox.showerror("Error","ખરીદનારનું નામ લખો"); return
        try:
            conn=get_connection(); cur=conn.cursor(); cur.execute("INSERT INTO buyers(name,mobile) VALUES(?,?)",vals); conn.commit(); conn.close()
            load_buyers(); [x.delete(0,"end") for x in fields]; messagebox.showinfo("Success","ખરીદનાર સફળતાપૂર્વક સેવ થયો.")
        except sqlite3.IntegrityError: messagebox.showerror("Error","આ ખરીદનાર પહેલેથી હાજર છે.")
    ctk.CTkButton(form,text="💾 સેવ કરો",command=save,width=250,height=45).pack(pady=15)
    ctk.CTkButton(form,text="🗑️ ખરીદનાર Delete / વ્યવસ્થા",command=lambda:manage_people_screen("buyer"),width=250,height=42).pack(pady=5)
    back_button()

def buyer_bill_screen():
    clear_screen(); title_label("👥 ખરીદનારનું બિલ")
    vals=load_buyers(); combo=ctk.CTkComboBox(content_frame,values=vals,width=420); combo.pack(pady=10)
    date_e=ctk.CTkEntry(content_frame,width=220,placeholder_text="તારીખ (ખાલી = બધી)"); date_e.pack(pady=5)
    box=ctk.CTkTextbox(content_frame,width=850,height=430,font=("Courier New",14)); box.pack(pady=10)
    def generate():
        bid=buyer_data.get(combo.get().strip())
        if not bid: messagebox.showerror("Error","ખરીદનાર પસંદ કરો."); return
        conn=get_connection(); cur=conn.cursor()
        sql="""SELECT a.auction_date,v.name vegetable,a.weight,a.price,a.total,b.name buyer,b.mobile
               FROM auctions a JOIN vegetables v ON v.id=a.vegetable_id JOIN buyers b ON b.id=a.buyer_id WHERE a.buyer_id=?"""
        params=[bid]; d=date_e.get().strip()
        if d: sql+=" AND a.auction_date=?"; params.append(d)
        sql+=" ORDER BY a.id"; cur.execute(sql,params); rows=cur.fetchall(); conn.close()
        box.delete("1.0","end")
        if not rows: box.insert("end","આ ખરીદનારની કોઈ એન્ટ્રી નથી."); return
        total=sum(float(r["total"]) for r in rows); tw=sum(float(r["weight"]) for r in rows)
        box.insert("end",f"શાકભાજી ઓક્શન હિસાબ સિસ્ટમ\nખરીદનાર બિલ\n\nખરીદનાર: {rows[0]['buyer']}\nમોબાઇલ: {rows[0]['mobile'] or ''}\n\n")
        for i,r in enumerate(rows,1):
            box.insert("end",f"{i}. {r['auction_date']} | {r['vegetable']} | {r['weight']:g} Kg × ₹{r['price']:.2f} = ₹{r['total']:.2f}\n")
        box.insert("end",f"\n{'-'*55}\nકુલ વજન: {tw:g} Kg\nકુલ ચૂકવવાની રકમ: ₹ {total:.2f}")
    ctk.CTkButton(content_frame,text="બિલ બનાવો",command=generate,width=220,height=45).pack(pady=8)
    back_button()

def auction_screen():
    clear_screen(); title_label("📝 ઓક્શન એન્ટ્રી")
    refresh_commission()
    form=ctk.CTkFrame(content_frame); form.pack(pady=5)
    date=ctk.CTkEntry(form,width=300); date.insert(0,datetime.now().strftime("%d-%m-%Y"))
    fc=ctk.CTkComboBox(form,values=load_farmers(),width=300)
    vc=ctk.CTkComboBox(form,values=load_vegetables(),width=300)
    bc=ctk.CTkComboBox(form,values=load_buyers(),width=300)
    we=ctk.CTkEntry(form,width=300); pe=ctk.CTkEntry(form,width=300)
    for i,(lab,w) in enumerate([("તારીખ",date),("ખેડૂત",fc),("શાકભાજી",vc),("ખરીદનાર",bc),("વજન (Kg)",we),("ભાવ પ્રતિ Kg",pe)]):
        ctk.CTkLabel(form,text=lab).grid(row=i,column=0,padx=10,pady=7); w.grid(row=i,column=1,padx=10,pady=7)
    info=ctk.CTkLabel(content_frame,text=f"કમિશન: {COMMISSION_PERCENT:g}%",font=("Arial",17,"bold")); info.pack(pady=8)
    selected={"id":None}
    history=ctk.CTkTextbox(content_frame,width=950,height=260); history.pack(pady=8)
    def calc():
        try: return float(we.get())*float(pe.get())
        except: return 0
    def clear():
        selected["id"] = None
        selected_line_id["id"] = None
        we.delete(0,"end")
        pe.delete(0,"end")
    def save():
        try: weight=float(we.get()); price=float(pe.get())
        except: messagebox.showerror("Error","વજન અને ભાવ સાચા લખો."); return
        ids=(farmer_data.get(fc.get()),vegetable_data.get(vc.get()),buyer_data.get(bc.get()))
        if not all(ids): messagebox.showerror("Error","ખેડૂત, શાકભાજી અને ખરીદનાર પસંદ કરો."); return
        total=weight*price; comm=total*COMMISSION_PERCENT/100; fam=total-comm
        conn=get_connection(); cur=conn.cursor()
        if selected["id"]:
            cur.execute("""UPDATE auctions SET auction_date=?,farmer_id=?,vegetable_id=?,buyer_id=?,weight=?,price=?,total=?,commission=?,farmer_amount=? WHERE id=?""",(date.get().strip(),*ids,weight,price,total,COMMISSION_PERCENT,fam,selected["id"]))
        else:
            cur.execute("""INSERT INTO auctions(auction_date,farmer_id,vegetable_id,buyer_id,weight,price,total,commission,farmer_amount) VALUES(?,?,?,?,?,?,?,?,?)""",(date.get().strip(),*ids,weight,price,total,COMMISSION_PERCENT,fam))
        conn.commit(); conn.close(); clear(); load(); messagebox.showinfo("Success","એન્ટ્રી સેવ/સુધારાઈ ગઈ.")
    def load():
        selected_line_id["id"] = None
        history.delete("1.0","end"); conn=get_connection(); cur=conn.cursor()
        cur.execute("""SELECT a.id,a.auction_date,f.name farmer,v.name veg,b.name buyer,a.weight,a.price,a.total FROM auctions a JOIN farmers f ON f.id=a.farmer_id JOIN vegetables v ON v.id=a.vegetable_id JOIN buyers b ON b.id=a.buyer_id ORDER BY a.id DESC LIMIT 100""")
        rows=cur.fetchall(); conn.close()
        for r in rows: history.insert("end",f"ID:{r['id']} | {r['auction_date']} | {r['farmer']} | {r['veg']} | {r['weight']:g} Kg × ₹{r['price']:.2f} = ₹{r['total']:.2f} | {r['buyer']}\n")
    selected_line_id = {"id": None}

    def remember_selected_line(event=None):
        import re
        try:
            # If text is highlighted, always use the highlighted line.
            ranges = history.tag_ranges("sel")
            if ranges:
                line_text = history.get(f"{ranges[0]} linestart", f"{ranges[0]} lineend")
            else:
                line_text = history.get("insert linestart", "insert lineend")

            m = re.search(r"ID\s*:\s*(\d+)", line_text)
            if m:
                selected_line_id["id"] = int(m.group(1))
                history.tag_remove("selected_auction", "1.0", "end")
                line_start = history.index(f"{ranges[0] if ranges else 'insert'} linestart")
                history.tag_add("selected_auction", line_start, f"{line_start} lineend")
        except Exception:
            pass

    history.tag_config("selected_auction", background="#2b5d85")

    def get_id():
        import re

        # First use the ID remembered when the user clicked a line.
        if selected_line_id["id"] is not None:
            return selected_line_id["id"]

        # Otherwise try highlighted text, then the cursor line.
        ranges = history.tag_ranges("sel")
        if ranges:
            text = history.get(f"{ranges[0]} linestart", f"{ranges[0]} lineend")
        else:
            text = history.get("insert linestart", "insert lineend")

        m = re.search(r"ID\s*:\s*(\d+)", text)
        if not m:
            messagebox.showwarning(
                "માહિતી",
                "પહેલા ઓક્શન લિસ્ટમાં જે એન્ટ્રી Edit/Delete કરવી હોય તેની લાઇન પર એકવાર ક્લિક કરો."
            )
            return None

        aid = int(m.group(1))
        selected_line_id["id"] = aid
        return aid
    def edit():
        aid=get_id()
        if not aid:return
        conn=get_connection(); cur=conn.cursor(); cur.execute("SELECT * FROM auctions WHERE id=?",(aid,)); r=cur.fetchone(); conn.close()
        if not r:return
        selected["id"]=aid; date.delete(0,"end"); date.insert(0,r["auction_date"])
        # reverse maps
        for widget,data_map,key in [(fc,farmer_data,"farmer_id"),(vc,vegetable_data,"vegetable_id"),(bc,buyer_data,"buyer_id")]:
            widget.set(next((n for n,i in data_map.items() if i==r[key]),""))
        we.delete(0,"end"); we.insert(0,str(r["weight"])); pe.delete(0,"end"); pe.insert(0,str(r["price"]))
        messagebox.showinfo("Edit","માહિતી ઉપર આવી ગઈ છે. સુધારીને સેવ કરો.")
    def delete():
        aid=get_id()
        if not aid:return
        if not messagebox.askyesno("Confirm","આ ઓક્શન એન્ટ્રી Delete કરવી છે?"):return
        conn=get_connection(); conn.execute("DELETE FROM auctions WHERE id=?",(aid,)); conn.commit(); conn.close(); load()
    bf=ctk.CTkFrame(content_frame,fg_color="transparent"); bf.pack(pady=5)
    ctk.CTkButton(bf,text="💾 સેવ / Update",command=save,width=180,height=42).grid(row=0,column=0,padx=5)
    ctk.CTkButton(bf,text="✏️ પસંદ કરેલી Edit",command=edit,width=180,height=42).grid(row=0,column=1,padx=5)
    ctk.CTkButton(bf,text="🗑️ પસંદ કરેલી Delete",command=delete,width=180,height=42).grid(row=0,column=2,padx=5)
    ctk.CTkButton(bf,text="🧹 સાફ",command=clear,width=120,height=42).grid(row=0,column=3,padx=5)
    ctk.CTkLabel(content_frame,text="📋 છેલ્લી 100 એન્ટ્રીઓ — લાઇન પર ક્લિક કરીને Edit/Delete કરો",font=("Arial",17,"bold")).pack(pady=(10,2))
    history.bind("<ButtonRelease-1>", remember_selected_line)
    history.bind("<KeyRelease-Up>", remember_selected_line)
    history.bind("<KeyRelease-Down>", remember_selected_line)
    load(); back_button()

def payment_recovery_report_screen():
    clear_screen(); title_label("📊 તારીખ પ્રમાણે ચુકવણું અને ઉઘરાણું રિપોર્ટ")
    d=ctk.CTkEntry(content_frame,width=250); d.insert(0,datetime.now().strftime("%d-%m-%Y")); d.pack(pady=10)
    box=ctk.CTkTextbox(content_frame,width=1000,height=500,font=("Courier New",13)); box.pack(pady=10)
    def make():
        day=d.get().strip(); conn=get_connection(); cur=conn.cursor()
        cur.execute("""SELECT f.name,COALESCE(f.village,'') village,SUM(a.total) gross,SUM(a.total*a.commission/100) comm,SUM(a.farmer_amount) payable FROM auctions a JOIN farmers f ON f.id=a.farmer_id WHERE a.auction_date=? GROUP BY f.id ORDER BY f.name""",(day,)); fr=cur.fetchall()
        cur.execute("""SELECT b.name,SUM(a.total) receivable FROM auctions a JOIN buyers b ON b.id=a.buyer_id WHERE a.auction_date=? GROUP BY b.id ORDER BY b.name""",(day,)); br=cur.fetchall(); conn.close()
        box.delete("1.0","end"); lines=[f"તારીખ પ્રમાણે ચુકવણું અને ઉઘરાણું રિપોર્ટ\nતારીખ: {day}\n\nખેડૂતોને ચુકવવાના રૂપિયા\n"+ "-"*95]
        pg=pc=pay=0
        for r in fr: pg+=r["gross"]; pc+=r["comm"]; pay+=r["payable"]; lines.append(f"{r['name']:<25} {r['village']:<18} કુલ ₹{r['gross']:>10.2f} | કમિ ₹{r['comm']:>8.2f} | ચુકવવા ₹{r['payable']:>10.2f}")
        rec=sum(r["receivable"] for r in br)
        lines+=["\n"+"-"*95,f"કુલ વેચાણ: ₹{pg:.2f} | કુલ કમિશન: ₹{pc:.2f} | ખેડૂતોને કુલ ચુકવણું: ₹{pay:.2f}","\nખરીદદાર પાસેથી ઉઘરાવવાના રૂપિયા","-"*70]
        for r in br: lines.append(f"{r['name']:<35} ઉઘરાવવાના: ₹{r['receivable']:>12.2f}")
        lines += ["-"*70,f"કુલ ઉઘરાણું: ₹{rec:.2f}"]
        box.insert("end","\n".join(lines))
    ctk.CTkButton(content_frame,text="📊 રિપોર્ટ બનાવો",command=make,width=250,height=45).pack(pady=5)
    ctk.CTkButton(content_frame,text="🖨️ A4 Print",command=lambda: print_bill(box.get('1.0','end').strip()) if box.get('1.0','end').strip() else messagebox.showwarning("માહિતી","પહેલા રિપોર્ટ બનાવો."),width=250,height=45).pack(pady=5)
    back_button()

def report_screen():
    clear_screen(); title_label("📊 રિપોર્ટ અને પ્રિન્ટ")
    for text,cmd in [
        ("👨‍🌾 ખેડૂતનું બિલ",farmer_bill_screen),
        ("👥 ખરીદનારનું બિલ",buyer_bill_screen),
        ("📊 સંપૂર્ણ ઓક્શન હિસાબ",full_report_screen),
        ("💰 ચુકવણું અને ઉઘરાણું A4 રિપોર્ટ",payment_recovery_report_screen),
        ("⚙️ Commission Settings",settings_screen)
    ]:
        ctk.CTkButton(content_frame,text=text,command=cmd,width=420,height=52,font=("Arial",17)).pack(pady=8)
    back_button()

# Extend home with Settings button
_old_home_screen = home_screen
def home_screen():
    clear_screen()
    title_label("🥬 શાકભાજી ઓક્શન હિસાબ સિસ્ટમ")
    button_frame=ctk.CTkFrame(content_frame,fg_color="transparent"); button_frame.pack(pady=10)
    for text,cmd in [
        ("👨‍🌾 ખેડૂત ઉમેરો",farmer_screen),("👥 ખરીદનાર ઉમેરો",buyer_screen),
        ("🥬 શાકભાજી ઉમેરો",vegetable_screen),("📝 ઓક્શન એન્ટ્રી કરો",auction_screen),
        ("📊 રિપોર્ટ",report_screen),("⚙️ Settings",settings_screen)]:
        ctk.CTkButton(button_frame,text=text,command=cmd,width=330,height=50,font=("Arial",17)).pack(pady=7)

# =========================================================
# MAIN WINDOW
# =========================================================

create_tables()

app = ctk.CTk()

app.title(
    "શાકભાજી ઓક્શન હિસાબ સિસ્ટમ"
)

app.geometry(
    "1100x800"
)

app.minsize(
    900,
    650
)

content_frame = ctk.CTkScrollableFrame(
    app,
    width=1050,
    height=750
)

content_frame.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

home_screen()

app.mainloop()