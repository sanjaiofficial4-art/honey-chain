import hashlib, json
from datetime import datetime
from database import get_db

GENESIS_DATA = {"type": "GENESIS", "message": "Honey Chain local prototype"}

def canonical_json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def calculate_hash(block_index, timestamp, data_json, previous_hash):
    payload = canonical_json({
        "block_index": int(block_index),
        "timestamp": timestamp,
        "data_json": data_json,
        "previous_hash": previous_hash
    })
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def genesis_block():
    timestamp = "2026-01-01T00:00:00Z"
    data_json = canonical_json(GENESIS_DATA)
    previous_hash = "0" * 64
    return {"timestamp": timestamp, "data_json": data_json, "previous_hash": previous_hash,
            "current_hash": calculate_hash(0, timestamp, data_json, previous_hash)}

def create_block_for_batch(batch_id):
    with get_db() as db:
        exists = db.execute("SELECT id FROM blocks WHERE batch_id=?", (batch_id,)).fetchone()
        if exists:
            return
        batch = db.execute("""SELECT b.batch_id,b.harvest_date,b.quantity,b.unit,b.flower_source,b.location,
            b.quality_status,b.notes,b.created_at,h.location AS hive_location,k.name AS beekeeper_name
            FROM batches b JOIN hives h ON h.id=b.hive_id JOIN beekeepers k ON k.id=h.beekeeper_id
            WHERE b.batch_id=?""", (batch_id,)).fetchone()
        if not batch:
            raise ValueError("Cannot create a block for a missing batch.")
        previous = db.execute("SELECT block_index,current_hash FROM blocks ORDER BY block_index DESC LIMIT 1").fetchone()
        index = previous["block_index"] + 1
        prev_hash = previous["current_hash"]
        timestamp = datetime.utcnow().isoformat(timespec="seconds")+"Z"
        data = dict(batch)
        data_json = canonical_json(data)
        digest = calculate_hash(index, timestamp, data_json, prev_hash)
        db.execute("""INSERT INTO blocks(batch_id,block_index,timestamp,data_json,previous_hash,current_hash)
                      VALUES(?,?,?,?,?,?)""", (batch_id,index,timestamp,data_json,prev_hash,digest))

def verify_chain(batch_id=None):
    with get_db() as db:
        rows = [dict(r) for r in db.execute("SELECT * FROM blocks ORDER BY block_index")]
    if not rows:
        return {"valid": False, "message": "No blocks found.", "checked": 0, "target": None}
    previous_hash = "0" * 64
    target = None
    for row in rows:
        expected = calculate_hash(row["block_index"], row["timestamp"], row["data_json"], row["previous_hash"])
        if expected != row["current_hash"]:
            return {"valid": False, "message": f"Hash mismatch at block #{row['block_index']}.", "checked": row["block_index"]+1, "target": row}
        if row["previous_hash"] != previous_hash:
            return {"valid": False, "message": f"Previous-hash link mismatch at block #{row['block_index']}.", "checked": row["block_index"]+1, "target": row}
        previous_hash = row["current_hash"]
        if batch_id and row["batch_id"] == batch_id:
            target = row
    if batch_id and target is None:
        return {"valid": False, "message": "Batch exists but no linked block was found.", "checked": len(rows), "target": None}
    return {"valid": True, "message": f"Chain valid: {len(rows)} block(s) checked.", "checked": len(rows), "target": target}
