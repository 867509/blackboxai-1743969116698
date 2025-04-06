import requests
import random
import string
import time
from requests.auth import HTTPBasicAuth

class PleskAPI:
    def __init__(self, host, username, password):
        self.base_url = f"https://{host}/api/v2"
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _request(self, method, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.request(
                    method,
                    url,
                    json=data,
                    headers=self.headers,
                    auth=self.auth,
                    timeout=10
                )
                if response.status_code == 429:  # Rate limited
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Plesk API request failed: {str(e)}")
                time.sleep(1)

    def client_exists(self, client_id):
        """Check if a client exists in Plesk"""
        endpoint = f"/clients/{client_id}"
        try:
            self._request("GET", endpoint)
            return True
        except:
            return False

    def create_client(self, email=None):
        """Create a new Plesk client with random credentials"""
        username = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%^&*', k=12))
        
        data = {
            "name": username,
            "login": username,
            "password": password,
            "email": email or f"{username}@example.com"
        }
        
        response = self._request("POST", "/clients", data)
        return {
            "plesk_client_id": response["id"],
            "username": username,
            "password": password
        }

    def create_subscription(self, client_id, plan_id, domain=None):
        """Create a subscription for a client"""
        if not domain:
            domain = f"temp-{random.randint(1000, 9999)}.example.com"
            
        data = {
            "name": domain,
            "service_plan": {"id": plan_id},
            "hosting_type": "virtual",
            "owner_client": {"id": client_id},
            "external_id": str(random.randint(100000, 999999))
        }
        
        response = self._request("POST", "/subscriptions", data)
        return {
            "subscription_id": response["id"],
            "domain": domain
        }

    def update_subscription(self, subscription_id, new_plan_id):
        """Update a subscription's service plan"""
        data = {
            "service_plan": {"id": new_plan_id}
        }
        return self._request("PUT", f"/subscriptions/{subscription_id}", data)

    def delete_client(self, client_id):
        """Delete a client and all associated resources"""
        return self._request("DELETE", f"/clients/{client_id}")