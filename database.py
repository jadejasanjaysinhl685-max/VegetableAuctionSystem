import sqlite3

conn = sqlite3.connect("auction.db")
cur = conn.cursor()

# ખેડૂત ટેબલ
cur.execute("""
CREATE TABLE IF NOT EXISTS farmers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    village TEXT,
    mobile TEXT
)
""")

# ખરીદનાર ટેબલ
cur.execute("""
CREATE TABLE IF NOT EXISTS buyers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mobile TEXT
)
""")

# શાકભાજી ટેબલ
cur.execute("""
CREATE TABLE IF NOT EXISTS vegetables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
""")

# હરાજી ટેબલ
cur.execute("""
CREATE TABLE IF NOT EXISTS auctions (
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

print("Database Ready")