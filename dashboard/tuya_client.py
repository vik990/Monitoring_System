import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass
class TuyaCredentials:
    access_id: str
    access_secret: str
    base_url: str


class TuyaCloudClient:
    """Minimal Tuya Cloud API client for server-side polling in Django."""

    def __init__(self, credentials: TuyaCredentials):
        self.credentials = credentials
        self._access_token: Optional[str] = None
        self._token_expire_at: float = 0

    @staticmethod
    def _sha256_hex(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _hmac_sha256_upper(self, value: str) -> str:
        digest = hmac.new(
            self.credentials.access_secret.encode("utf-8"),
            value.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return digest.upper()

    def _string_to_sign(self, method: str, path_with_query: str, body: str = "") -> str:
        content_sha256 = self._sha256_hex(body or "")
        # No custom signed headers for this integration.
        return "\n".join([method.upper(), content_sha256, "", path_with_query])

    def _http_json(self, method: str, path: str, query: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        query = query or {}
        headers = headers or {}
        qs = urlencode(query)
        path_with_query = f"{path}?{qs}" if qs else path
        url = f"{self.credentials.base_url}{path_with_query}"

        req = Request(url=url, method=method.upper(), headers=headers)
        try:
            with urlopen(req, timeout=15) as resp:
                payload = resp.read().decode("utf-8")
                return json.loads(payload)
        except HTTPError as err:
            body = err.read().decode("utf-8", errors="ignore")
            try:
                parsed = json.loads(body) if body else {}
            except Exception:
                parsed = {"raw": body}
            raise RuntimeError(f"Tuya HTTP {err.code}: {parsed}")

    def _ensure_token(self) -> str:
        now = time.time()
        if self._access_token and now < self._token_expire_at:
            return self._access_token

        method = "GET"
        path = "/v1.0/token"
        query = {"grant_type": 1}
        qs = urlencode(query)
        path_with_query = f"{path}?{qs}"

        t = str(int(time.time() * 1000))
        nonce = uuid.uuid4().hex
        string_to_sign = self._string_to_sign(method, path_with_query)
        sign_payload = f"{self.credentials.access_id}{t}{nonce}{string_to_sign}"
        sign = self._hmac_sha256_upper(sign_payload)

        headers = {
            "client_id": self.credentials.access_id,
            "t": t,
            "nonce": nonce,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
        }

        response = self._http_json(method, path, query=query, headers=headers)
        if not response.get("success"):
            raise RuntimeError(f"Tuya token request failed: {response}")

        result = response.get("result", {})
        self._access_token = result.get("access_token")
        # keep a small safety margin
        expires_in = int(result.get("expire_time", 3600))
        self._token_expire_at = time.time() + max(60, expires_in - 30)

        if not self._access_token:
            raise RuntimeError("Tuya token response missing access_token")
        return self._access_token

    def request(self, method: str, path: str, query: Optional[Dict] = None, body: str = "") -> Dict:
        access_token = self._ensure_token()
        query = query or {}
        qs = urlencode(query)
        path_with_query = f"{path}?{qs}" if qs else path

        t = str(int(time.time() * 1000))
        nonce = uuid.uuid4().hex
        string_to_sign = self._string_to_sign(method, path_with_query, body=body)
        sign_payload = f"{self.credentials.access_id}{access_token}{t}{nonce}{string_to_sign}"
        sign = self._hmac_sha256_upper(sign_payload)

        headers = {
            "client_id": self.credentials.access_id,
            "access_token": access_token,
            "t": t,
            "nonce": nonce,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json",
        }

        response = self._http_json(method, path, query=query, headers=headers)
        if not response.get("success"):
            raise RuntimeError(f"Tuya API request failed: {response}")
        return response

    def get_device_status(self, device_id: str) -> Dict:
        # Try IoT Core endpoint first, then legacy endpoint fallback.
        try:
            return self.request("GET", f"/v1.0/iot-03/devices/{device_id}/status")
        except Exception:
            return self.request("GET", f"/v1.0/devices/{device_id}/status")

    def get_device_info(self, device_id: str) -> Dict:
        # Try common device-info endpoints (Tuya cloud varies by project API set).
        try:
            return self.request("GET", f"/v1.0/iot-03/devices/{device_id}")
        except Exception:
            return self.request("GET", f"/v1.0/devices/{device_id}")


def extract_live_metrics(status_items: List[Dict]) -> Dict:
    """Normalize common Tuya plug DPS values into dashboard-friendly metrics."""
    dps = {item.get("code"): item.get("value") for item in (status_items or [])}

    power_raw = dps.get("cur_power", dps.get("power"))
    current_raw = dps.get("cur_current", dps.get("current"))
    voltage_raw = dps.get("cur_voltage", dps.get("voltage"))
    energy_raw = dps.get("add_ele", dps.get("cur_energy"))

    # Common Tuya scaling for plugs:
    # cur_power -> W * 10, cur_voltage -> V * 10, add_ele -> kWh * 100
    power_w = round((float(power_raw) / 10.0), 2) if power_raw is not None else None
    current_a = round((float(current_raw) / 1000.0), 3) if current_raw is not None else None
    voltage_v = round((float(voltage_raw) / 10.0), 1) if voltage_raw is not None else None
    total_energy_kwh = round((float(energy_raw) / 100.0), 3) if energy_raw is not None else None

    switch_codes = [k for k in dps.keys() if isinstance(k, str) and k.startswith("switch")]
    if switch_codes:
        is_on = any(bool(dps.get(code)) for code in switch_codes)
    elif "switch" in dps or "switch_1" in dps:
        is_on = bool(dps.get("switch") or dps.get("switch_1"))
    else:
        # Some metering-only devices may not expose switch status DP.
        is_on = None

    return {
        "is_on": is_on,
        "power_w": power_w,
        "current_a": current_a,
        "voltage_v": voltage_v,
        "total_energy_kwh": total_energy_kwh,
        "raw_dps": dps,
    }
