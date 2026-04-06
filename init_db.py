import sqlite3

DB_NAME = "directory.db"

schema = """
CREATE TABLE IF NOT EXISTS nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT UNIQUE NOT NULL,
    node_name TEXT NOT NULL,
    role TEXT NOT NULL,
    public_key TEXT NOT NULL,
    wg_tunnel_ip TEXT NOT NULL,
    reported_public_ip TEXT,
    reported_public_port INTEGER,
    available_bandwidth REAL DEFAULT 0,
    credit INTEGER DEFAULT 100,
    status TEXT DEFAULT 'offline',
    last_heartbeat TEXT
);
"""

def main():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.executescript(schema)
    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_NAME}")

if __name__ == "__main__":
    main()

