"""
SQLite Mock Database Generator for WideResolve Multi-Tenant Platform.
Generates 3 clients (quickcart, telenet, carelink) with ~15 customers and ~40 orders each,
and explicitly plants the 9 requested evaluation scenarios.
"""

import sqlite3
import os
import json
import hashlib
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "omni_resolve.db")

def init_db(db_path=DB_PATH):
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables with client_id on every table
    cursor.executescript("""
    CREATE TABLE customers (
        id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        tier TEXT NOT NULL DEFAULT 'Standard',
        ltv REAL NOT NULL DEFAULT 0.0,
        churn_risk BOOLEAN NOT NULL DEFAULT 0,
        repeat_complaint_count INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE orders (
        id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        order_date TEXT NOT NULL,
        status TEXT NOT NULL,
        total_amount REAL NOT NULL,
        carrier_status TEXT,
        delivery_notes TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    );

    CREATE TABLE payments (
        id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        order_id TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        amount REAL NOT NULL,
        status TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        transaction_ref TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    );

    CREATE TABLE tickets (
        id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        order_id TEXT,
        issue_type TEXT NOT NULL,
        status TEXT NOT NULL,
        sentiment TEXT NOT NULL,
        complaint_text TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    );

    CREATE TABLE refunds (
        id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        order_id TEXT NOT NULL,
        amount REAL NOT NULL,
        reason TEXT NOT NULL,
        approved_by TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id)
    );

    CREATE TABLE audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        case_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        action TEXT NOT NULL,
        payload TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        current_hash TEXT NOT NULL
    );
    """)

    conn.commit()
    return conn

def seed_data(conn):
    cursor = conn.cursor()
    now = datetime(2026, 10, 1, 10, 0, 0)
    
    clients = ["quickcart", "telenet", "carelink"]
    
    # 1. Populate standard customers (~15 per client)
    customers = []
    customer_names = {
        "quickcart": ["Alice Smith", "Bob Jones", "Charlie Brown", "David Miller", "Emma Watson",
                      "Frank Castle", "Grace Hopper", "Hannah Abbott", "Ian Malcolm", "Julia Roberts",
                      "Kevin Hart", "Laura Croft", "Michael Scott", "Nora Jones", "Oscar Martinez"],
        "telenet": ["Arthur Dent", "Bella Swan", "Clark Kent", "Diana Prince", "Edward Elric",
                    "Fiona Gallagher", "George Costanza", "Harry Potter", "Iris West", "Jack Bauer",
                    "Karen Page", "Luke Skywalker", "Mona Lisa", "Neo Anderson", "Oliver Queen"],
        "carelink": ["Adam West", "Betty White", "Charles Xavier", "Donna Noble", "Eleanor Vance",
                     "Forest Gump", "Gemma Simmons", "Harold Finch", "Ida Wells", "John Watson",
                     "Katy Perry", "Logan Howlett", "Martha Stewart", "Norman Bates", "Oprah Gail"]
    }

    client_prefixes = {
        "quickcart": "QC",
        "telenet": "TN",
        "carelink": "CL"
    }

    for client in clients:
        prefix = client_prefixes[client]
        for i, name in enumerate(customer_names[client]):
            cid = f"{prefix}-CUST-{100 + i}"
            tier = "VIP" if i in [0, 1] else ("Gold" if i in [2, 3, 4] else "Standard")
            ltv = 2400.0 if tier == "VIP" else (950.0 if tier == "Gold" else 210.0)
            email = f"{name.lower().replace(' ', '.')}@example.com"
            phone = f"+1-555-01{i:02d}"
            churn_risk = 1 if i == 0 else 0
            repeat_cnt = 3 if i == 10 else (1 if i in [5, 6] else 0)
            customers.append((cid, client, name, email, phone, tier, ltv, churn_risk, repeat_cnt,
                              (now - timedelta(days=180 - i*5)).isoformat()))

    cursor.executemany("""
    INSERT INTO customers (id, client_id, name, email, phone, tier, ltv, churn_risk, repeat_complaint_count, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, customers)

    # 2. Populate ~40 orders per client
    orders = []
    payments = []
    
    for client in clients:
        prefix = client_prefixes[client]
        for ord_idx in range(1, 41):
            oid = f"{prefix}-ORD-{8000 + ord_idx}"
            cust_idx = ord_idx % 15
            cid = f"{prefix}-CUST-{100 + cust_idx}"
            order_date = (now - timedelta(days=50 - ord_idx)).isoformat()
            
            # Base amounts by client
            if client == "quickcart":
                amount = round(25.0 + (ord_idx * 3.75) % 150.0, 2)
                status = "Delivered" if ord_idx < 35 else "In Transit"
                carrier_status = "Delivered to front door" if ord_idx < 35 else "Out for delivery"
                notes = "Standard packaging"
            elif client == "telenet":
                amount = 79.99 if ord_idx % 2 == 0 else 129.99
                status = "Billed"
                carrier_status = "Service Active"
                notes = "Fiber gigabit subscription"
            else: # carelink
                amount = 50.0 if ord_idx % 3 == 0 else (120.0 if ord_idx % 3 == 1 else 250.0)
                status = "Completed"
                carrier_status = "Clinic Visit Completed"
                notes = "Outpatient copay / consultation fee"

            orders.append((oid, client, cid, order_date, status, amount, carrier_status, notes))
            
            # Payment record
            pid = f"{prefix}-PAY-{5000 + ord_idx}"
            payments.append((pid, client, oid, cid, amount, "Captured", "CreditCard", f"TXN-{prefix}-{90000+ord_idx}", order_date))

    cursor.executemany("""
    INSERT INTO orders (id, client_id, customer_id, order_date, status, total_amount, carrier_status, delivery_notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, orders)

    cursor.executemany("""
    INSERT INTO payments (id, client_id, order_id, customer_id, amount, status, payment_method, transaction_ref, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, payments)

    # =========================================================================
    # 3. Explicitly Plant the 9 Scenarios
    # =========================================================================
    planted_summary = []

    # Scenario 1: QuickCart Double Charge
    # Order QC-ORD-8901 with two identical payment captures of $42.50
    s1_cid = "QC-CUST-103"
    s1_oid = "QC-ORD-8901"
    cursor.execute("""
    INSERT INTO orders (id, client_id, customer_id, order_date, status, total_amount, carrier_status, delivery_notes)
    VALUES (?, 'quickcart', ?, ?, 'Delivered', 42.50, 'Delivered', 'Duplicate checkout gateway glitch')
    """, (s1_oid, s1_cid, (now - timedelta(days=2)).isoformat()))
    cursor.execute("""
    INSERT INTO payments (id, client_id, order_id, customer_id, amount, status, payment_method, transaction_ref, created_at)
    VALUES ('QC-PAY-9001', 'quickcart', ?, ?, 42.50, 'Captured', 'CreditCard', 'TXN-QC-DUP-A', ?)
    """, (s1_oid, s1_cid, (now - timedelta(days=2, hours=1)).isoformat()))
    cursor.execute("""
    INSERT INTO payments (id, client_id, order_id, customer_id, amount, status, payment_method, transaction_ref, created_at)
    VALUES ('QC-PAY-9002', 'quickcart', ?, ?, 42.50, 'Captured', 'CreditCard', 'TXN-QC-DUP-B', ?)
    """, (s1_oid, s1_cid, (now - timedelta(days=2, minutes=58)).isoformat()))
    planted_summary.append({
        "scenario": "1. Double Charge",
        "client": "quickcart",
        "customer": s1_cid,
        "order": s1_oid,
        "detail": "Customer charged twice ($42.50) within 2 minutes for order QC-ORD-8901.",
        "expected": "AUTO_RESOLVE (Refund $42.50)"
    })

    # Scenario 2: QuickCart Late Delivery (SLA breach)
    s2_cid = "QC-CUST-104"
    s2_oid = "QC-ORD-8902"
    cursor.execute("""
    INSERT INTO orders (id, client_id, customer_id, order_date, status, total_amount, carrier_status, delivery_notes)
    VALUES (?, 'quickcart', ?, ?, 'Delayed', 78.00, 'Delayed - Severe Hub Transit Delay (+5 days)', 'Guaranteed 2-day delivery missed by 5 days')
    """, (s2_oid, s2_cid, (now - timedelta(days=7)).isoformat()))
    cursor.execute("""
    INSERT INTO payments (id, client_id, order_id, customer_id, amount, status, payment_method, transaction_ref, created_at)
    VALUES ('QC-PAY-9003', 'quickcart', ?, ?, 78.00, 'Captured', 'CreditCard', 'TXN-QC-LATE-01', ?)
    """, (s2_oid, s2_cid, (now - timedelta(days=7)).isoformat()))
    planted_summary.append({
        "scenario": "2. Late Delivery",
        "client": "quickcart",
        "customer": s2_cid,
        "order": s2_oid,
        "detail": "Express shipment delayed by 5 days past promised SLA delivery window.",
        "expected": "AUTO_RESOLVE ($10 courtesy SLA credit)"
    })

    # Scenario 3: TeleNet Outage Billing
    s3_cid = "TN-CUST-102"
    s3_oid = "TN-ORD-8903"
    cursor.execute("""
    INSERT INTO orders (id, client_id, customer_id, order_date, status, total_amount, carrier_status, delivery_notes)
    VALUES (?, 'telenet', ?, ?, 'Outage Recorded', 89.99, 'Outage Logged - Node 42 South Offline 48h', 'Documented 48-hour network blackout')
    """, (s3_oid, s3_cid, (now - timedelta(days=10)).isoformat()))
    cursor.execute("""
    INSERT INTO payments (id, client_id, order_id, customer_id, amount, status, payment_method, transaction_ref, created_at)
    VALUES ('TN-PAY-9004', 'telenet', ?, ?, 89.99, 'Captured', 'AutoDebit', 'TXN-TN-OUT-01', ?)
    """, (s3_oid, s3_cid, (now - timedelta(days=10)).isoformat()))
    planted_summary.append({
        "scenario": "3. Outage Billing",
        "client": "telenet",
        "customer": s3_cid,
        "order": s3_oid,
        "detail": "Customer billed full $89.99 monthly fee despite logged 48h system blackout.",
        "expected": "RESOLVE_WITH_APPROVAL (Service credit of $35.00)"
    })

    # Scenario 4: CareLink Duplicate Medical Bill
    s4_cid = "CL-CUST-104"
    s4_oid = "CL-ORD-8904"
    cursor.execute("""
    INSERT INTO orders (id, client_id, customer_id, order_date, status, total_amount, carrier_status, delivery_notes)
    VALUES (?, 'carelink', ?, ?, 'Completed', 50.00, 'Encounter Copay - Routine Blood Work', 'Lab copay duplicate billing error')
    """, (s4_oid, s4_cid, (now - timedelta(days=12)).isoformat()))
    cursor.execute("""
    INSERT INTO payments (id, client_id, order_id, customer_id, amount, status, payment_method, transaction_ref, created_at)
    VALUES ('CL-PAY-9005', 'carelink', ?, ?, 50.00, 'Captured', 'HSA_Card', 'TXN-CL-COPAY-A', ?)
    """, (s4_oid, s4_cid, (now - timedelta(days=12, hours=2)).isoformat()))
    cursor.execute("""
    INSERT INTO payments (id, client_id, order_id, customer_id, amount, status, payment_method, transaction_ref, created_at)
    VALUES ('CL-PAY-9006', 'carelink', ?, ?, 50.00, 'Captured', 'HSA_Card', 'TXN-CL-COPAY-B', ?)
    """, (s4_oid, s4_cid, (now - timedelta(days=12, hours=1)).isoformat()))
    planted_summary.append({
        "scenario": "4. Duplicate Medical Bill",
        "client": "carelink",
        "customer": s4_cid,
        "order": s4_oid,
        "detail": "Patient charged $50.00 copay twice for single routine lab visit.",
        "expected": "AUTO_RESOLVE (Refund duplicate $50.00)"
    })

    # Scenario 5: QuickCart Fraud Claim
    s5_cid = "QC-CUST-105"
    s5_oid = "QC-ORD-8905"
    cursor.execute("""
    INSERT INTO orders (id, client_id, customer_id, order_date, status, total_amount, carrier_status, delivery_notes)
    VALUES (?, 'quickcart', ?, ?, 'Completed', 320.00, 'Delivered', 'Luxury electronics package')
    """, (s5_oid, s5_cid, (now - timedelta(days=1)).isoformat()))
    cursor.execute("""
    INSERT INTO payments (id, client_id, order_id, customer_id, amount, status, payment_method, transaction_ref, created_at)
    VALUES ('QC-PAY-9007', 'quickcart', ?, ?, 320.00, 'Captured', 'CreditCard', 'TXN-QC-FRD-01', ?)
    """, (s5_oid, s5_cid, (now - timedelta(days=1)).isoformat()))
    planted_summary.append({
        "scenario": "5. Fraud Claim",
        "client": "quickcart",
        "customer": s5_cid,
        "order": s5_oid,
        "detail": "Customer claims card was stolen and unauthorized transaction placed.",
        "expected": "ESCALATE (Hard rule: Fraud/Security claim)"
    })

    # Scenario 6: TeleNet Repeat Complainer (3 past tickets)
    s6_cid = "TN-CUST-110"  # repeat_complaint_count=3
    cursor.execute("UPDATE customers SET repeat_complaint_count = 3 WHERE id = ?", (s6_cid,))
    cursor.executemany("""
    INSERT INTO tickets (id, client_id, customer_id, order_id, issue_type, status, sentiment, complaint_text, created_at)
    VALUES (?, 'telenet', ?, 'TN-ORD-8010', 'Billing', 'Closed', 'Angry', ?, ?)
    """, [
        ("TN-TCK-7001", s6_cid, "Router fee was billed improperly last month", (now - timedelta(days=28)).isoformat()),
        ("TN-TCK-7002", s6_cid, "Slow fiber speed in evening hours again", (now - timedelta(days=15)).isoformat()),
        ("TN-TCK-7003", s6_cid, "Billing discrepancy on unreturned cable box", (now - timedelta(days=4)).isoformat())
    ])
    planted_summary.append({
        "scenario": "6. Repeat Complainer",
        "client": "telenet",
        "customer": s6_cid,
        "order": "TN-ORD-8010",
        "detail": "Customer has 3 prior logged disputes in 30 days and submits 4th complaint.",
        "expected": "ESCALATE (Hard rule: 3rd repeat contact)"
    })

    # Scenario 7: CareLink Legal Threat
    s7_cid = "CL-CUST-107"
    s7_oid = "CL-ORD-8907"
    cursor.execute("""
    INSERT INTO orders (id, client_id, customer_id, order_date, status, total_amount, carrier_status, delivery_notes)
    VALUES (?, 'carelink', ?, ?, 'Completed', 180.00, 'Completed', 'Specialist consultation fee')
    """, (s7_oid, s7_cid, (now - timedelta(days=3)).isoformat()))
    cursor.execute("""
    INSERT INTO payments (id, client_id, order_id, customer_id, amount, status, payment_method, transaction_ref, created_at)
    VALUES ('CL-PAY-9008', 'carelink', ?, ?, 180.00, 'Captured', 'CreditCard', 'TXN-CL-LEG-01', ?)
    """, (s7_oid, s7_cid, (now - timedelta(days=3)).isoformat()))
    planted_summary.append({
        "scenario": "7. Legal Threat",
        "client": "carelink",
        "customer": s7_cid,
        "order": s7_oid,
        "detail": "Customer states 'My attorney will file a regulatory lawsuit against CareLink'.",
        "expected": "ESCALATE (Hard rule: Legal/Regulatory threat)"
    })

    # Scenario 8: TeleNet VIP Customer with Churn Risk
    s8_cid = "TN-CUST-100"  # Tier VIP, churn_risk=1
    s8_oid = "TN-ORD-8908"
    cursor.execute("""
    INSERT INTO orders (id, client_id, customer_id, order_date, status, total_amount, carrier_status, delivery_notes)
    VALUES (?, 'telenet', ?, ?, 'Billed', 249.99, 'Service Active', 'Enterprise Dedicated Fiber Tier')
    """, (s8_oid, s8_cid, (now - timedelta(days=5)).isoformat()))
    cursor.execute("""
    INSERT INTO payments (id, client_id, order_id, customer_id, amount, status, payment_method, transaction_ref, created_at)
    VALUES ('TN-PAY-9009', 'telenet', ?, ?, 249.99, 'Captured', 'CorporateACH', 'TXN-TN-VIP-01', ?)
    """, (s8_oid, s8_cid, (now - timedelta(days=5)).isoformat()))
    planted_summary.append({
        "scenario": "8. VIP Churn Risk",
        "client": "telenet",
        "customer": s8_cid,
        "order": s8_oid,
        "detail": "VIP Tier enterprise account ($2,400 LTV) threatening immediate contract termination.",
        "expected": "ESCALATE (Hard rule: VIP customer with churn risk)"
    })

    # Scenario 9: Delivered vs Not Received (Carrier contradiction)
    s9_cid = "QC-CUST-108"
    s9_oid = "QC-ORD-8909"
    cursor.execute("""
    INSERT INTO orders (id, client_id, customer_id, order_date, status, total_amount, carrier_status, delivery_notes)
    VALUES (?, 'quickcart', ?, ?, 'Delivered', 95.00, 'Carrier GPS Tag: Delivered to porch at 3:14 PM', 'Customer ring doorbell footage shows no courier present')
    """, (s9_oid, s9_cid, (now - timedelta(days=2)).isoformat()))
    cursor.execute("""
    INSERT INTO payments (id, client_id, order_id, customer_id, amount, status, payment_method, transaction_ref, created_at)
    VALUES ('QC-PAY-9010', 'quickcart', ?, ?, 95.00, 'Captured', 'CreditCard', 'TXN-QC-DISP-01', ?)
    """, (s9_oid, s9_cid, (now - timedelta(days=2)).isoformat()))
    planted_summary.append({
        "scenario": "9. Delivered vs Not Received",
        "client": "quickcart",
        "customer": s9_cid,
        "order": s9_oid,
        "detail": "Carrier marked 'Delivered to porch' but customer video evidence shows missing parcel.",
        "expected": "RESOLVE_WITH_APPROVAL or ESCALATE (Contradictory evidence)"
    })

    conn.commit()

    # Save planted summary to json for evaluation runner
    summary_path = os.path.join(os.path.dirname(__file__), "planted_summary.json")
    with open(summary_path, "w") as f:
        json.dump(planted_summary, f, indent=2)

    return planted_summary

if __name__ == "__main__":
    conn = init_db()
    summary = seed_data(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT client_id, count(*) FROM customers GROUP BY client_id")
    cust_counts = cursor.fetchall()
    cursor.execute("SELECT client_id, count(*) FROM orders GROUP BY client_id")
    order_counts = cursor.fetchall()
    cursor.execute("SELECT client_id, count(*) FROM payments GROUP BY client_id")
    pay_counts = cursor.fetchall()
    
    print("\n=======================================================")
    print(" WideResolve Multi-Tenant Database Created Successfully")
    print("=======================================================\n")
    print("Customer Counts by Client:", dict(cust_counts))
    print("Order Counts by Client:   ", dict(order_counts))
    print("Payment Counts by Client: ", dict(pay_counts))
    print("\nPlanted Evaluation Scenarios (9 Scenarios):")
    for s in summary:
        print(f" - [{s['client'].upper()}] {s['scenario']}: {s['detail']} => Expected: {s['expected']}")
    conn.close()
