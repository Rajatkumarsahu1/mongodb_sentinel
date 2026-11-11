from mongodb_client import client, db

print("Testing MongoDB...")

print("Database:", db.name)

print("Ping:", client.admin.command("ping"))

print("Connection successful!")