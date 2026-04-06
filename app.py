from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB_NAME = "directory.db"
HEARTBEAT_TIMEOUT_SECONDS = 90


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def mark_offline_nodes():
    conn = get_db_connection()
    cur = conn.cursor()

    threshold = datetime.utcnow() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)
    threshold_str = threshold.isoformat()

    cur.execute("""
        UPDATE nodes
        SET status = 'offline'
        WHERE last_heartbeat IS NOT NULL
          AND last_heartbeat < ?
    """, (threshold_str,))

    conn.commit()
    conn.close()


@app.route("/api/register", methods=["POST"])
def register_node():
    data = request.get_json()

    required_fields = [
        "node_id", "node_name", "role",
        "public_key", "wg_tunnel_ip"
    ]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    now = datetime.utcnow().isoformat()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT credit FROM nodes WHERE node_id = ?", (data["node_id"],))
    existing = cur.fetchone()
    credit_value = existing["credit"] if existing else 100

    cur.execute("""
        INSERT INTO nodes (
            node_id, node_name, role, public_key, wg_tunnel_ip,
            reported_public_ip, reported_public_port,
            available_bandwidth, credit, status, last_heartbeat
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(node_id) DO UPDATE SET
            node_name=excluded.node_name,
            role=excluded.role,
            public_key=excluded.public_key,
            wg_tunnel_ip=excluded.wg_tunnel_ip,
            reported_public_ip=excluded.reported_public_ip,
            reported_public_port=excluded.reported_public_port,
            available_bandwidth=excluded.available_bandwidth,
            status='online',
            last_heartbeat=excluded.last_heartbeat
    """, (
        data["node_id"],
        data["node_name"],
        data["role"],
        data["public_key"],
        data["wg_tunnel_ip"],
        data.get("reported_public_ip"),
        data.get("reported_public_port"),
        data.get("available_bandwidth", 0),
        credit_value,
        "online",
        now
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Node registered successfully"}), 200


@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    data = request.get_json()

    if "node_id" not in data:
        return jsonify({"error": "Missing field: node_id"}), 400

    now = datetime.utcnow().isoformat()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE nodes
        SET last_heartbeat = ?,
            status = 'online',
            reported_public_ip = ?,
            reported_public_port = ?,
            available_bandwidth = ?
        WHERE node_id = ?
    """, (
        now,
        data.get("reported_public_ip"),
        data.get("reported_public_port"),
        data.get("available_bandwidth", 0),
        data["node_id"]
    ))

    if cur.rowcount == 0:
        conn.close()
        return jsonify({"error": "Node not found"}), 404

    conn.commit()
    conn.close()

    return jsonify({"message": "Heartbeat received"}), 200


@app.route("/api/nodes", methods=["GET"])
def list_nodes():
    mark_offline_nodes()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM nodes ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()

    nodes = [dict(row) for row in rows]
    return jsonify(nodes), 200


@app.route("/api/match", methods=["POST"])
def match_node():
    mark_offline_nodes()

    data = request.get_json()
    requester_id = data.get("node_id")

    if not requester_id:
        return jsonify({"error": "Missing field: node_id"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM nodes
        WHERE status = 'online'
          AND node_id != ?
        ORDER BY credit DESC, available_bandwidth DESC
        LIMIT 1
    """, (requester_id,))
    target = cur.fetchone()

    if not target:
        conn.close()
        return jsonify({"error": "No available node found"}), 404

    cur.execute("""
        UPDATE nodes
        SET credit = credit - 1
        WHERE node_id = ?
    """, (requester_id,))

    cur.execute("""
        UPDATE nodes
        SET credit = credit + 1
        WHERE node_id = ?
    """, (target["node_id"],))

    conn.commit()

    cur.execute("SELECT * FROM nodes WHERE node_id = ?", (target["node_id"],))
    updated_target = cur.fetchone()

    conn.close()

    return jsonify({
        "matched_node": {
            "node_id": updated_target["node_id"],
            "node_name": updated_target["node_name"],
            "role": updated_target["role"],
            "public_key": updated_target["public_key"],
            "wg_tunnel_ip": updated_target["wg_tunnel_ip"],
            "reported_public_ip": updated_target["reported_public_ip"],
            "reported_public_port": updated_target["reported_public_port"],
            "available_bandwidth": updated_target["available_bandwidth"],
            "credit": updated_target["credit"],
            "status": updated_target["status"]
        }
    }), 200


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Crowd VPN Directory Server is running"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
