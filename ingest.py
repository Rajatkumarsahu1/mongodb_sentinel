from collections import defaultdict
from datetime import datetime
from pymongo import ReplaceOne
from config import TRANSACTION_LIMIT, BATCH_SIZE
from supabase_client import fetch_all, fetch_by_values
from mongodb_client import db, transactions_collection, customers_collection


def index_by(rows, key):
    return {row[key]: row for row in rows if row.get(key) is not None}


def normalize_timestamps(value, key=None):
    """Convert ISO timestamp strings to Python datetimes for BSON Date storage."""
    if isinstance(value, dict):
        return {k: normalize_timestamps(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_timestamps(v, key) for v in value]
    if isinstance(value, str) and key and (
        key.endswith("_at") or key.endswith("_time") or key.endswith("_timestamp")
    ):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    return value


def dedupe_devices(device_rows):
    """Remove duplicate device IDs while preserving first-seen order."""
    result = {}
    for device in device_rows:
        device_id = device.get("device_id")
        if device_id is not None:
            result[device_id] = dict(device)
    return list(result.values())


def run_ingestion():
    print("1/6 Fetching source transactions...")
    tx_rows = fetch_all("transactions", BATCH_SIZE, TRANSACTION_LIMIT)
    if not tx_rows:
        raise RuntimeError(
            "No transactions returned. Check table name, API key and Supabase RLS policies."
        )
    print(f"   Retrieved {len(tx_rows):,} transactions")

    customer_ids = {r.get("customer_id") for r in tx_rows if r.get("customer_id")}
    merchant_ids = {r.get("merchant_id") for r in tx_rows if r.get("merchant_id")}
    device_ids = {r.get("device_id") for r in tx_rows if r.get("device_id")}
    transaction_ids = {r.get("transaction_id") for r in tx_rows if r.get("transaction_id")}

    print("2/6 Fetching related tables...")
    # Fetch only related rows instead of downloading every lookup/label row.
    customers = fetch_by_values("customers", "customer_id", customer_ids)
    merchants = fetch_by_values("merchants", "merchant_id", merchant_ids)
    devices = fetch_by_values("devices", "device_id", device_ids)
    labels = fetch_by_values("labels", "transaction_id", transaction_ids)

    customer_map = index_by(customers, "customer_id")
    merchant_map = index_by(merchants, "merchant_id")
    device_map = index_by(devices, "device_id")
    label_map = index_by(labels, "transaction_id")

    print(
        f"   Matched customers={len(customer_map):,}, merchants={len(merchant_map):,}, "
        f"devices={len(device_map):,}, labels={len(label_map):,}"
    )

    print("3/6 Building transaction documents...")
    transaction_docs = []
    customer_device_map = defaultdict(list)

    for source in tx_rows:
        doc = normalize_timestamps(dict(source))  # preserve fields and store timestamps as BSON Dates
        tx_id = doc.get("transaction_id")
        customer_id = doc.get("customer_id")
        merchant_id = doc.get("merchant_id")
        device_id = doc.get("device_id")

        merchant = merchant_map.get(merchant_id, {})
        device = device_map.get(device_id, {})
        label = label_map.get(tx_id, {})

        # Add related-table data without overwriting source fields unnecessarily.
        doc["merchant_details"] = merchant or None
        doc["device_details"] = device or None
        if label:
            doc["fraud_label"] = label.get("fraud_label")
            doc["label_source"] = label.get("label_source")
            doc["label_available_at"] = label.get("label_available_at")
            doc["label_split"] = label.get("split")
        else:
            # Do not infer fraud labels when no matching label exists.
            doc["fraud_label"] = doc.get("fraud_label")

        if customer_id and device:
            customer_device_map[customer_id].append(device)

        if not tx_id:
            raise ValueError("A transaction row has no transaction_id; cannot safely upsert.")

        transaction_docs.append(doc)

    print("4/6 Building customer documents with embedded devices...")
    customer_docs = []
    for source in customers:
        doc = normalize_timestamps(dict(source))
        doc["devices"] = dedupe_devices(customer_device_map.get(source.get("customer_id"), []))
        customer_docs.append(doc)

    print("5/6 Upserting documents into MongoDB...")
    tx_ops = [
        ReplaceOne({"transaction_id": doc["transaction_id"]}, doc, upsert=True)
        for doc in transaction_docs
    ]
    customer_ops = [
        ReplaceOne({"customer_id": doc["customer_id"]}, doc, upsert=True)
        for doc in customer_docs
        if doc.get("customer_id") is not None
    ]

    tx_result = transactions_collection.bulk_write(tx_ops, ordered=False)
    customer_result = customers_collection.bulk_write(customer_ops, ordered=False)

    print("6/6 Verifying MongoDB...")
    print(f"   Transactions in this run: {len(transaction_docs):,}")
    print(f"   Transaction upserts inserted: {tx_result.upserted_count:,}")
    print(f"   Transaction documents modified: {tx_result.modified_count:,}")
    print(f"   Customer documents in this run: {len(customer_ops):,}")
    print(f"   Customer upserts inserted: {customer_result.upserted_count:,}")
    print(f"   MongoDB transaction count: {transactions_collection.count_documents({}):,}")
    print(f"   MongoDB customer count: {customers_collection.count_documents({}):,}")

    # Useful uniqueness constraints for repeatable ingestion.
    transactions_collection.create_index("transaction_id", unique=True)
    customers_collection.create_index("customer_id", unique=True)

    print("Ingestion completed successfully.")


if __name__ == "__main__":
    run_ingestion()
