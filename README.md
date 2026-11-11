# SENTINEL: MongoDB with Python

A Python-based implementation of the SENTINEL transaction data model using **MongoDB Atlas**, **PyMongo**, and **Supabase** as the source of the existing dataset.

The project demonstrates document modelling, data ingestion, CRUD operations, indexing with query-plan comparison, and aggregation pipelines for fraud analysis.

## Project objectives

- Connect a Python application to MongoDB Atlas.
- Model SENTINEL customers and transactions in MongoDB.
- Import at least 5,000 transactions from the existing SENTINEL Supabase project.
- Demonstrate MongoDB insert, read, update, and delete operations.
- Create indexes and compare query execution plans using `explain()`.
- Use aggregation pipelines to calculate fraud rates and identify high-value customers.

## Architecture and data model

The source data is read from Supabase and loaded into the `sentinel_db` MongoDB database.

Two MongoDB collections are used:

| Collection | Contents | Design choice |
|---|---|---|
| `transactions` | Transaction records, customer/merchant/device IDs, merchant and device details, and fraud label | References related entities using IDs. Transaction records remain independently queryable without duplicating full customer profiles. |
| `customers` | Customer profile fields and associated device information | Devices are embedded in the customer document because they are useful when retrieving a customer's profile. |

The ingestion script enriches transaction documents with merchant details, device details, and `fraud_label` by matching the source records on their IDs. It preserves the source transaction fields returned by Supabase.

### Data flow

```text
SENTINEL Supabase
       |
       | Python + Supabase SDK
       v
  Data ingestion
       |
       | PyMongo (upsert)
       v
 MongoDB Atlas
   |          |
   v          v
transactions customers
   |
   +--> CRUD demonstrations
   +--> Indexes and explain()
   +--> Fraud analytics aggregations
```

## Technology stack

- Python 3
- MongoDB Atlas
- PyMongo
- Supabase Python SDK
- `python-dotenv`
- `certifi` for TLS certificate verification

## Repository structure

```text
sentinel-mongodb/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── config.py
├── supabase_client.py
├── mongodb_client.py
├── ingest.py
├── crud_operations.py
├── indexes_explain.py
└── aggregations.py
```

## Prerequisites

1. Python 3.10 or later.
2. A Supabase project containing the SENTINEL tables used by this project: `transactions`, `customers`, `merchants`, `devices`, and `labels`.
3. A MongoDB Atlas cluster and a database user with read/write permissions.
4. Your current IP address added to the Atlas Network Access allowlist.
5. Supabase Row Level Security policies that permit the configured key to read the required tables.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Rajatkumarsahu1/mongodb_sentinel
cd sentinel-mongodb
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your own credentials:

```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=YOUR_SUPABASE_API_KEY
MONGODB_URI=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=sentinel_db
TRANSACTION_LIMIT=5000
BATCH_SIZE=1000
```

Do not commit `.env` or share credentials in screenshots, terminal recordings, or the public repository. Use a read-authorized Supabase key with only the access required for this task. Never put a MongoDB password or Supabase secret/service-role key in source code.

## Run the project

Run the scripts from the repository root, with the virtual environment activated and `.env` configured.

### 1. Ingest SENTINEL data

```bash
python ingest.py
```

The script imports up to 5,000 transactions by default, retrieves related customer, merchant, device, and label records, builds the two document collections, and performs repeatable upserts.

**Verified ingestion result:**

| Item | Result |
|---|---:|
| Transactions retrieved and loaded | 5,000 |
| Related customers matched | 1,577 |
| Related merchants matched | 200 |
| Related devices matched | 1,706 |
| Fraud labels matched | 5,000 |
| MongoDB transaction documents | 5,000 |
| MongoDB customer documents | 1,577 |

### 2. Demonstrate CRUD operations

```bash
python crud_operations.py
```

The script demonstrates:

- `insert_one()` — inserts a demonstration customer.
- `insert_many()` — inserts demonstration transaction documents.
- `find()` — retrieves fraud-labelled transactions using a filter and field projection.
- `update_many()` — updates demonstration records.
- `delete_one()` — deletes a demonstration record.

The script uses temporary demonstration records and cleans them up after the demonstration.

### 3. Create indexes and compare query plans

```bash
python indexes_explain.py
```

The indexing demonstration compares a customer lookup before and after creating an index on `customer_id`. It also creates an index on `transaction_time`.

**Verified explain() comparison for one customer:**

| Metric | Before index | After index |
|---|---:|---:|
| Query plan | `COLLSCAN` | `IXSCAN` followed by `FETCH` |
| Documents examined | 5,000 | 11 |
| Index keys examined | 0 | 11 |
| Matching documents | 11 | 11 |
| Reported execution time | 3 ms | 1 ms |

The comparison shows that the customer index allows MongoDB to locate the 11 matching records without scanning all 5,000 transaction documents. Execution times are from one run and can vary between runs; documents and keys examined provide the more meaningful comparison.

### 4. Run aggregation pipelines

```bash
python aggregations.py
```

The script runs two aggregation pipelines:

1. **Fraud rate by merchant category:** counts labelled transactions and fraud transactions per category, then calculates the fraud percentage.
2. **Top 10 customers by transaction amount in the latest 24-hour data window:** groups transactions by customer, sums transaction amounts, counts transactions, sorts by amount, and returns up to 10 customers.

The 24-hour window ends at the latest `transaction_time` in the imported dataset. This is intentional because the SENTINEL sample is historical; using the computer's current date could produce an empty result.

**Observed fraud-rate output from the tested dataset:**

| Merchant category | Transactions | Fraud transactions | Fraud rate |
|---|---:|---:|---:|
| gaming | 512 | 10 | 1.95% |
| gift_cards | 352 | 6 | 1.70% |
| electronics | 742 | 9 | 1.21% |
| grocery | 958 | 0 | 0.00% |
| travel | 253 | 0 | 0.00% |
| healthcare | 346 | 0 | 0.00% |
| other | 276 | 0 | 0.00% |
| food | 616 | 0 | 0.00% |
| education | 207 | 0 | 0.00% |
| quick_commerce | 738 | 0 | 0.00% |

In the tested 24-hour window, the top-customer pipeline returned one customer with one transaction and a total transaction amount of `640.55`. The pipeline returns up to 10 customers; fewer may be returned when fewer customers have transactions in that window.

## MongoDB indexes

The project creates these indexes on the `transactions` collection:

- `customer_id_1` — supports customer-based transaction lookups.
- `transaction_time_1` — supports time-based filtering, including the latest-24-hour aggregation.
- `transaction_id_1` — unique index used to support repeatable transaction upserts.

MongoDB also maintains the default `_id_` index.

## Screenshots and submission evidence

Add your own screenshots to a folder such as `screenshots/` before submitting. Recommended evidence:

1. Atlas connection success and database/collection names.
2. Ingestion output showing 5,000 transactions and 1,577 customers.
3. CRUD output showing insert, find, update, and delete operations.
4. `explain()` output showing `COLLSCAN` before and `IXSCAN` after indexing.
5. Fraud rate by merchant category and top customers aggregation output.

Do not include screenshots that expose connection strings, API keys, passwords, or other secrets.

## Limitations and assumptions
## Limitations and assumptions

- The ingestion code expects the source table names and key columns used in the SENTINEL Supabase project. If the source schema changes, update the table names or field mappings in `ingest.py`.
- Fraud-rate calculations include records with a `fraud_label` of `0` or `1`; records without a label are excluded from the denominator.
- The top-customer aggregation uses the latest available transaction timestamp as the end of its 24-hour window.
- The reported counts and sample aggregation results describe the dataset at the time this project was run. They may change if the source data changes or a different transaction limit is used.

## Author

**Rajat Kumar Sahu**

## Learning outcomes

This project demonstrates how to move relational source data into a document database, choose between embedding and referencing, perform CRUD operations with PyMongo, improve query efficiency with indexes, inspect query execution plans, and build MongoDB aggregation pipelines for fraud analytics.
