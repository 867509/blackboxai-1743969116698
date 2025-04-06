import requests
import hmac
import hashlib
import json
from datetime import datetime
from data_manager import add_transaction

class NOWPayments:
    def __init__(self, api_key, ipn_secret):
        self.base_url = "https://api.nowpayments.io/v1"
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        self.ipn_secret = ipn_secret

    def create_payment(self, amount, currency, order_id, user_id):
        """Create a new crypto payment invoice"""
        data = {
            "price_amount": amount,
            "price_currency": "usd",
            "pay_currency": currency,
            "ipn_callback_url": "https://yourdomain.com/webhook/nowpayments",
            "order_id": order_id,
            "order_description": f"Deposit for user {user_id}",
            "success_url": "https://yourdomain.com/success",
            "cancel_url": "https://yourdomain.com/cancel"
        }

        response = requests.post(
            f"{self.base_url}/payment",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def verify_webhook(self, request_data, signature):
        """Verify the authenticity of a webhook notification"""
        expected_signature = hmac.new(
            self.ipn_secret.encode(),
            json.dumps(request_data).encode(),
            hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)

    def process_webhook(self, data):
        """Process a valid payment webhook"""
        payment_status = data.get("payment_status")
        if payment_status == "finished":
            user_id = int(data["order_id"].split("_")[-1])
            amount = float(data["price_amount"])
            currency = data["pay_currency"]
            
            # Add transaction to user history
            add_transaction(
                user_id=user_id,
                transaction_type="deposit",
                amount=amount,
                currency=currency
            )
            
            # Update wallet balance
            from data_manager import update_wallet
            update_wallet(user_id, amount)
            
            return True
        return False

    def get_currencies(self):
        """Get list of supported cryptocurrencies"""
        response = requests.get(
            f"{self.base_url}/currencies",
            headers=self.headers
        )
        response.raise_for_status()
        return [c["currency"] for c in response.json()]

    def get_min_amount(self, currency):
        """Get minimum payment amount for a currency"""
        response = requests.get(
            f"{self.base_url}/min-amount",
            params={"currency_from": "usd", "currency_to": currency},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json().get("min_amount")