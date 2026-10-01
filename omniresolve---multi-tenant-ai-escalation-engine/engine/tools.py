"""
Tenant-isolated database access tools for OmniResolve.
Every function strictly enforces client_id filtering to guarantee zero cross-tenant leakage.
"""

import sqlite3
import os
from typing import List, Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "omni_resolve.db")

def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def _row_to_dict(cursor: sqlite3.Cursor, row: Any) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    if isinstance(row, sqlite3.Row) or hasattr(row, 'keys'):
        return dict(row)
    cols = [col[0] for col in cursor.description]
    return dict(zip(cols, row))

def get_customer(client_id: str, customer_id: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    """Retrieve customer by ID, strictly scoped to client_id."""
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM customers WHERE client_id = ? AND id = ?",
            (client_id.lower(), customer_id)
        )
        row = cursor.fetchone()
        return _row_to_dict(cursor, row)
    finally:
        if close_conn:
            conn.close()

def get_orders(client_id: str, customer_id: Optional[str] = None, order_id: Optional[str] = None, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """Retrieve orders, strictly scoped to client_id."""
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    try:
        cursor = conn.cursor()
        if order_id:
            cursor.execute(
                "SELECT * FROM orders WHERE client_id = ? AND id = ?",
                (client_id.lower(), order_id)
            )
        elif customer_id:
            cursor.execute(
                "SELECT * FROM orders WHERE client_id = ? AND customer_id = ? ORDER BY order_date DESC",
                (client_id.lower(), customer_id)
            )
        else:
            cursor.execute(
                "SELECT * FROM orders WHERE client_id = ? ORDER BY order_date DESC LIMIT 50",
                (client_id.lower(),)
            )
        rows = cursor.fetchall()
        return [_row_to_dict(cursor, r) for r in rows]
    finally:
        if close_conn:
            conn.close()

def get_payments(client_id: str, order_id: str, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """Retrieve payment records for an order, strictly scoped to client_id."""
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM payments WHERE client_id = ? AND order_id = ? ORDER BY created_at ASC",
            (client_id.lower(), order_id)
        )
        rows = cursor.fetchall()
        return [_row_to_dict(cursor, r) for r in rows]
    finally:
        if close_conn:
            conn.close()

def get_past_tickets(client_id: str, customer_id: str, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """Retrieve previous support tickets, strictly scoped to client_id."""
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tickets WHERE client_id = ? AND customer_id = ? ORDER BY created_at DESC",
            (client_id.lower(), customer_id)
        )
        rows = cursor.fetchall()
        return [_row_to_dict(cursor, r) for r in rows]
    finally:
        if close_conn:
            conn.close()

def issue_refund(
    client_id: str,
    order_id: str,
    amount: float,
    reason: str,
    approved_by: str,
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """Execute refund insert after policy validation passes."""
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    try:
        cursor = conn.cursor()
        import uuid
        from datetime import datetime
        refund_id = f"REF-{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.utcnow().isoformat()
        
        cursor.execute("""
        INSERT INTO refunds (id, client_id, order_id, amount, reason, approved_by, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'Completed', ?)
        """, (refund_id, client_id.lower(), order_id, amount, reason, approved_by, now_str))
        
        conn.commit()
        return {
            "refund_id": refund_id,
            "client_id": client_id.lower(),
            "order_id": order_id,
            "amount": amount,
            "reason": reason,
            "approved_by": approved_by,
            "status": "Completed",
            "created_at": now_str
        }
    finally:
        if close_conn:
            conn.close()
