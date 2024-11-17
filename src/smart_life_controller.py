import requests
from config.settings import SMART_LIFE_BASE_URL, SMART_LIFE_ACCESS_ID, SMART_LIFE_ACCESS_KEY, SMART_LIFE_DEVICE_ID

class SmartLifeController:
    def __init__(self):
        self.base_url = SMART_LIFE_BASE_URL
        self.access_id = SMART_LIFE_ACCESS_ID
        self.access_key = SMART_LIFE_ACCESS_KEY
        self.device_id = SMART_LIFE_DEVICE_ID

    def control_device(self, action):
        """Contrôle un appareil Smart Life."""
        url = f"{self.base_url}/v1.0/devices/{self.device_id}/commands"
        headers = {
            "Client-Id": self.access_id,
            "Sign": self.access_key,
            "Content-Type": "application/json"
        }
        payload = {
            "commands": [{"code": "switch", "value": action}]
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return f"Commande '{action}' envoyée avec succès !"
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur lors du contrôle de l'appareil : {e}")
