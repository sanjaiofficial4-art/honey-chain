import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "honey_chain.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS beekeepers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT DEFAULT '',
            location TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS hives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            beekeeper_id INTEGER NOT NULL REFERENCES beekeepers(id),
            location TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active',
            temperature REAL,
            humidity REAL,
            inspection_date TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL UNIQUE,
            hive_id INTEGER NOT NULL REFERENCES hives(id),
            harvest_date TEXT NOT NULL,
            quantity REAL NOT NULL CHECK(quantity > 0),
            unit TEXT NOT NULL,
            flower_source TEXT NOT NULL,
            location TEXT DEFAULT '',
            quality_status TEXT DEFAULT 'Not assessed',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT UNIQUE REFERENCES batches(batch_id),
            block_index INTEGER NOT NULL UNIQUE,
            timestamp TEXT NOT NULL,
            data_json TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            current_hash TEXT NOT NULL
        );
        """)
        # Genesis block persists as the anchor for the local demonstration chain.
        row = db.execute("SELECT id FROM blocks WHERE block_index=0").fetchone()
        if not row:
            from blockchain import genesis_block
            b = genesis_block()
            db.execute("INSERT INTO blocks(batch_id,block_index,timestamp,data_json,previous_hash,current_hash) VALUES(NULL,?,?,?,?,?)",
                       (0, b["timestamp"], b["data_json"], b["previous_hash"], b["current_hash"]))

def register_beekeeper(name, contact="", location=""):
    name = name.strip()
    if not name:
        raise ValueError("Beekeeper name is required.")
    with get_db() as db:
        db.execute("INSERT INTO beekeepers(name,contact,location,created_at) VALUES(?,?,?,?)",
                   (name, contact.strip(), location.strip(), datetime.utcnow().isoformat(timespec="seconds")+"Z"))

def register_hive(beekeeper_id, location, status="Active", temperature=None, humidity=None, inspection_date=""):
    try:
        beekeeper_id = int(beekeeper_id)
        temperature = float(temperature) if temperature not in (None, "") else None
        humidity = float(humidity) if humidity not in (None, "") else None
    except ValueError:
        raise ValueError("Choose a valid beekeeper and enter numeric temperature/humidity values.")
    if not location.strip():
        raise ValueError("Hive location is required.")
    with get_db() as db:
        if not db.execute("SELECT id FROM beekeepers WHERE id=?", (beekeeper_id,)).fetchone():
            raise ValueError("Selected beekeeper does not exist.")
        db.execute("""INSERT INTO hives(beekeeper_id,location,status,temperature,humidity,inspection_date,created_at)
                      VALUES(?,?,?,?,?,?,?)""",
                   (beekeeper_id, location.strip(), status, temperature, humidity, inspection_date,
                    datetime.utcnow().isoformat(timespec="seconds")+"Z"))

def register_batch(batch_id, hive_id, harvest_date, quantity, unit, flower_source, location="", quality_status="Not assessed", notes=""):
    batch_id, unit, flower_source = batch_id.strip(), unit.strip(), flower_source.strip()
    try:
        hive_id, quantity = int(hive_id), float(quantity)
    except ValueError:
        raise ValueError("Select a valid hive and enter a numeric quantity.")
    if not batch_id or not harvest_date or not unit or not flower_source:
        raise ValueError("Batch ID, harvest date, unit, and flower source are required.")
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")
    try:
        datetime.strptime(harvest_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Harvest date must be valid.")
    with get_db() as db:
        if not db.execute("SELECT id FROM hives WHERE id=?", (hive_id,)).fetchone():
            raise ValueError("Selected hive does not exist.")
        try:
            db.execute("""INSERT INTO batches(batch_id,hive_id,harvest_date,quantity,unit,flower_source,location,quality_status,notes,created_at)
                          VALUES(?,?,?,?,?,?,?,?,?,?)""",
                       (batch_id, hive_id, harvest_date, quantity, unit, flower_source, location.strip(),
                        quality_status, notes.strip(), datetime.utcnow().isoformat(timespec="seconds")+"Z"))
        except sqlite3.IntegrityError:
            raise ValueError("That Batch ID already exists.")
    from blockchain import create_block_for_batch
    create_block_for_batch(batch_id)

def list_beekeepers():
    with get_db() as db:
        return [dict(r) for r in db.execute("SELECT * FROM beekeepers ORDER BY id DESC")]

def list_hives():
    with get_db() as db:
        return [dict(r) for r in db.execute("""SELECT h.*, b.name AS beekeeper_name FROM hives h
            JOIN beekeepers b ON b.id=h.beekeeper_id ORDER BY h.id DESC""")]

def list_batches(limit=None):
    sql = """SELECT b.*, h.location AS hive_location, k.name AS beekeeper_name
             FROM batches b JOIN hives h ON h.id=b.hive_id
             JOIN beekeepers k ON k.id=h.beekeeper_id ORDER BY b.id DESC"""
    if limit:
        sql += " LIMIT ?"
    with get_db() as db:
        return [dict(r) for r in db.execute(sql, (limit,) if limit else ())]

def get_batch(batch_id):
    with get_db() as db:
        r = db.execute("""SELECT b.*, h.location AS hive_location, h.status AS hive_status,
            h.temperature, h.humidity, h.inspection_date, k.name AS beekeeper_name,
            k.location AS beekeeper_location FROM batches b JOIN hives h ON h.id=b.hive_id
            JOIN beekeepers k ON k.id=h.beekeeper_id WHERE b.batch_id=?""", (batch_id,)).fetchone()
        return dict(r) if r else None

def list_blocks():
    with get_db() as db:
        return [dict(r) for r in db.execute("SELECT * FROM blocks ORDER BY block_index")]

def get_dashboard():
    with get_db() as db:
        return {
            "beekeepers": db.execute("SELECT COUNT(*) FROM beekeepers").fetchone()[0],
            "hives": db.execute("SELECT COUNT(*) FROM hives").fetchone()[0],
            "batches": db.execute("SELECT COUNT(*) FROM batches").fetchone()[0],
            "blocks": db.execute("SELECT COUNT(*) FROM blocks").fetchone()[0],
        }
