from datetime import datetime, timedelta, timezone
from mongodb_client import transactions_collection

# Pipeline 1: fraud rate by merchant_category.
# Assumes labels were joined into transactions as fraud_label (0/1).
fraud_rate_pipeline = [
    {"$match": {"fraud_label": {"$in": [0, 1]}}},
    {
        "$group": {
            "_id": "$merchant_category",
            "total_transactions": {"$sum": 1},
            "fraud_transactions": {
                "$sum": {
                    "$cond": [{"$eq": ["$fraud_label", 1]}, 1, 0]
                }
            }
        }
    },
    {
        "$project": {
            "_id": 0,
            "merchant_category": "$_id",
            "total_transactions": 1,
            "fraud_transactions": 1,
            "fraud_rate_percent": {
                "$cond": [
                    {"$gt": ["$total_transactions", 0]},
                    {
                        "$multiply": [
                            {"$divide": ["$fraud_transactions", "$total_transactions"]},
                            100
                        ]
                    },
                    0
                ]
            }
        }
    },
    {"$sort": {"fraud_rate_percent": -1}}
]

print("FRAUD RATE BY MERCHANT CATEGORY")
for row in transactions_collection.aggregate(fraud_rate_pipeline):
    print(row)

# Pipeline 2: top 10 customers in the 24 hours ending at the latest
# transaction timestamp in the imported sample. This makes the query useful
# for historical SENTINEL data rather than returning no rows due to today's date.
latest = transactions_collection.find_one(
    {"transaction_time": {"$type": "date"}},
    sort=[("transaction_time", -1)],
    projection={"transaction_time": 1}
)

if latest:
    window_end = latest["transaction_time"]
    window_start = window_end - timedelta(hours=24)

    top_customers_pipeline = [
        {
            "$match": {
                "transaction_time": {
                    "$gte": window_start,
                    "$lte": window_end
                }
            }
        },
        {
            "$group": {
                "_id": "$customer_id",
                "total_amount": {"$sum": "$transaction_amount"},
                "transaction_count": {"$sum": 1}
            }
        },
        {"$sort": {"total_amount": -1}},
        {"$limit": 10},
        {
            "$project": {
                "_id": 0,
                "customer_id": "$_id",
                "total_amount": 1,
                "transaction_count": 1
            }
        }
    ]

    print(f"\nTOP 10 CUSTOMERS: {window_start} to {window_end}")
    for row in transactions_collection.aggregate(top_customers_pipeline):
        print(row)
else:
    print(
        "No BSON Date transaction_time values found. "
        "Check that transaction_time was converted to a datetime during ingestion."
    )
