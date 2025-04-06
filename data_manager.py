import json
import os
import fcntl
from datetime import datetime

DB_FILE = "users.db"

def load_data():
    """Load data from the local database file"""
    if not os.path.exists(DB_FILE):
        return {"users": [], "offers": []}
    
    with open(DB_FILE, "r") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            return json.load(f)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

def save_data(data):
    """Save data to the local database file with file locking"""
    with open(DB_FILE, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            json.dump(data, f, indent=2)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

def get_user(user_id):
    """Get user by Telegram ID"""
    data = load_data()
    return next((u for u in data["users"] if u["id"] == user_id), None)

def update_wallet(user_id, amount):
    """Update user's wallet balance"""
    data = load_data()
    user = next((u for u in data["users"] if u["id"] == user_id), None)
    if user:
        user["wallet_balance"] = user.get("wallet_balance", 0) + amount
        save_data(data)
        return True
    return False

def add_transaction(user_id, transaction_type, amount, currency=None):
    """Add transaction to user history"""
    data = load_data()
    user = next((u for u in data["users"] if u["id"] == user_id), None)
    if user:
        if "history" not in user:
            user["history"] = []
        user["history"].append({
            "type": transaction_type,
            "amount": amount,
            "currency": currency,
            "timestamp": datetime.now().isoformat()
        })
        save_data(data)
        return True
    return False