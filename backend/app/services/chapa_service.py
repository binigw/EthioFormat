import os
import requests
from typing import Dict, Any, Optional
from app.config import settings

class ChapaPaymentService:
    def __init__(self):
        self.secret_key = settings.CHAPA_SECRET_KEY
        self.api_url = settings.CHAPA_API_URL.rstrip("/")

    def initialize_payment(
        self,
        amount: float,
        currency: str,
        email: str,
        first_name: str,
        last_name: str,
        tx_ref: str,
        callback_url: Optional[str] = None,
        return_url: Optional[str] = None,
        customization_title: str = "EthioFormat Thesis Download",
        customization_description: str = "Standard Thesis Formatting Service"
    ) -> Dict[str, Any]:
        """
        Initializes a transaction with Chapa Payment Gateway.
        """
        url = f"{self.api_url}/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "amount": str(amount),
            "currency": currency,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": tx_ref,
            "customization": {
                "title": customization_title,
                "description": customization_description
            }
        }
        if callback_url:
            payload["callback_url"] = callback_url
        if return_url:
            payload["return_url"] = return_url

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            data = response.json()
            return data
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Could not reach Chapa API: {str(e)}"
            }

    def verify_payment(self, tx_ref: str) -> Dict[str, Any]:
        """
        Verifies a transaction using Chapa API.
        """
        url = f"{self.api_url}/transaction/verify/{tx_ref}"
        headers = {
            "Authorization": f"Bearer {self.secret_key}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            data = response.json()
            return data
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Chapa verification error: {str(e)}"
            }

chapa_service = ChapaPaymentService()
