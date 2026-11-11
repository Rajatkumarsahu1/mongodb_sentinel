from mongodb_client import db

transactions = db["transactions"]
customers = db["customers"]

# INSERT ONE: use a clearly marked temporary demonstration customer.
insert_one_result = customers.insert_one({
    "customer_id": "DEMO_CUSTOMER_INSERT_ONE",
    "customer_age": 30,
    "home_city": "Demo City",
    "region": "demo",
    "is_demo": True,
    "devices": []
})
print("insert_one:", insert_one_result.inserted_id)

# INSERT MANY: use temporary demo transactions, not production source IDs.
demo_transactions = [
    {
        "transaction_id": "DEMO_TXN_INSERT_MANY_001",
        "customer_id": "DEMO_CUSTOMER_INSERT_ONE",
        "transaction_amount": 125.50,
        "merchant_category": "demo",
        "fraud_label": 0,
        "is_demo": True
    },
    {
        "transaction_id": "DEMO_TXN_INSERT_MANY_002",
        "customer_id": "DEMO_CUSTOMER_INSERT_ONE",
        "transaction_amount": 999.00,
        "merchant_category": "demo",
        "fraud_label": 1,
        "is_demo": True
    }
]
insert_many_result = transactions.insert_many(demo_transactions)
print("insert_many:", insert_many_result.inserted_ids)

# FIND with filter and projection.
for row in transactions.find(
    {"fraud_label": 1},
    {"_id": 0, "transaction_id": 1, "customer_id": 1,
     "transaction_amount": 1, "merchant_category": 1}
).limit(5):
    print("fraud sample:", row)

# UPDATE MANY: update only the temporary demo documents.
update_result = transactions.update_many(
    {"is_demo": True},
    {"$set": {"review_status": "demo_reviewed"}}
)
print("update_many matched/modified:", update_result.matched_count, update_result.modified_count)

# DELETE ONE: remove one temporary demo transaction.
delete_result = transactions.delete_one(
    {"transaction_id": "DEMO_TXN_INSERT_MANY_002", "is_demo": True}
)
print("delete_one deleted:", delete_result.deleted_count)

# Clean up the remaining temporary demo data.
transactions.delete_many({"is_demo": True})
customers.delete_one({"customer_id": "DEMO_CUSTOMER_INSERT_ONE", "is_demo": True})
