import base64
import logging
import math

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

DARAJA_BASE_URLS = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}


class DarajaError(Exception):
    """Raised when Daraja API communication fails."""


class DarajaAPI:
    """Safaricom Daraja M-Pesa API client. Settings only — no Django models/views."""

    def __init__(self):
        env = getattr(settings, "MPESA_ENVIRONMENT", "sandbox").lower()
        self.base_url = DARAJA_BASE_URLS.get(env, DARAJA_BASE_URLS["sandbox"])
        self.consumer_key = getattr(settings, "MPESA_CONSUMER_KEY", "")
        self.consumer_secret = getattr(settings, "MPESA_CONSUMER_SECRET", "")
        self.shortcode = getattr(settings, "MPESA_SHORTCODE", "174379")
        self.passkey = getattr(settings, "MPESA_PASSKEY", "")
        self.callback_url = getattr(settings, "MPESA_CALLBACK_URL", "")

    def get_access_token(self):
        if not self.consumer_key or not self.consumer_secret:
            logger.warning("Daraja: MPESA_CONSUMER_KEY or MPESA_CONSUMER_SECRET not set")
            raise DarajaError("M-Pesa API credentials are not configured")

        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        try:
            response = requests.get(
                url,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("access_token")
            if not token:
                raise DarajaError("No access_token in Daraja OAuth response")
            return token
        except requests.RequestException as exc:
            logger.exception("Daraja OAuth request failed: %s", exc)
            raise DarajaError(f"Could not obtain M-Pesa access token: {exc}") from exc

    def _build_password_and_timestamp(self):
        ts = timezone.localtime(timezone.now()).strftime("%Y%m%d%H%M%S")
        raw = f"{self.shortcode}{self.passkey}{ts}"
        password = base64.b64encode(raw.encode()).decode()
        return password, ts

    def stk_push(self, phone_number, amount, order_number):
        """
        Initiate STK Push. Returns full Daraja JSON on success, or
        {"success": False, "error": "..."} on failure.
        """
        try:
            token = self.get_access_token()
        except DarajaError as exc:
            return {"success": False, "error": str(exc)}

        password, timestamp = self._build_password_and_timestamp()
        amount_int = math.ceil(float(amount))
        account_ref = str(order_number)[:12]

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount_int,
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_ref,
            "TransactionDesc": f"Haznex {account_ref}",
        }

        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            data = response.json()
            if response.status_code >= 400:
                logger.error("Daraja STK Push HTTP %s: %s", response.status_code, data)
                return {
                    "success": False,
                    "error": data.get("errorMessage", "STK Push request failed"),
                }
            if data.get("ResponseCode") != "0":
                return {
                    "success": False,
                    "error": data.get("ResponseDescription", "STK Push rejected"),
                }
            return data
        except requests.RequestException as exc:
            logger.exception("Daraja STK Push request failed: %s", exc)
            return {"success": False, "error": f"STK Push request failed: {exc}"}
        except ValueError as exc:
            logger.exception("Daraja STK Push invalid JSON: %s", exc)
            return {"success": False, "error": "Invalid response from M-Pesa API"}

    @staticmethod
    def parse_callback(callback_data):
        """Parse Daraja STK callback JSON into a normalized dict."""
        result = {
            "result_code": None,
            "result_desc": "",
            "mpesa_receipt_number": "",
            "checkout_request_id": "",
        }

        if not isinstance(callback_data, dict):
            return result

        stk = callback_data.get("Body", {}).get("stkCallback", {})
        if not stk:
            return result

        result["result_code"] = stk.get("ResultCode")
        result["result_desc"] = stk.get("ResultDesc", "")
        result["checkout_request_id"] = stk.get("CheckoutRequestID", "")

        metadata = stk.get("CallbackMetadata", {}).get("Item", [])
        for item in metadata:
            if item.get("Name") == "MpesaReceiptNumber":
                result["mpesa_receipt_number"] = str(item.get("Value", ""))
                break

        return result
