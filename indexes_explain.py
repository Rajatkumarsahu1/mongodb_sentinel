
from mongodb_client import transactions_collection

# Get a real customer ID from the imported dataset
sample = transactions_collection.find_one(
    {},
    {"_id": 0, "customer_id": 1}
)

if not sample:
    raise RuntimeError("No transactions found!")

customer_id = sample["customer_id"]

query = {"customer_id": customer_id}

print("Testing customer:", customer_id)

# Remove the existing customer index for a clean comparison
try:
    transactions_collection.drop_index("customer_id_1")
except Exception:
    pass

# BEFORE INDEX
before = transactions_collection.find(query).explain()

print("\nBEFORE INDEX")
print("Winning plan:",
      before["queryPlanner"]["winningPlan"])

print("Execution stats:",
      before["executionStats"])

# CREATE INDEXES
transactions_collection.create_index("customer_id")
transactions_collection.create_index("transaction_time")

# AFTER INDEX
after = transactions_collection.find(query).explain()

print("\nAFTER INDEX")
print("Winning plan:",
      after["queryPlanner"]["winningPlan"])

print("Execution stats:",
      after["executionStats"])

print("\nTotal matching transactions:",
      transactions_collection.count_documents(query))

print("\nAvailable indexes:")
for index in transactions_collection.list_indexes():
    print(index["name"])
