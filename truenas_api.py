import requests
from config import (
    TRUENAS_ROOT_URL,
    TRUENAS_TOKEN,
    )
from helpers import to_gb


class TrueNASClient:
    base_url = f'http://{TRUENAS_ROOT_URL}/api/v2.0'
    headers = {'Authorization': f'Bearer {TRUENAS_TOKEN}'}

    def get_used_space_gb(self, pool):
        r = requests.get(
                f'{self.base_url}/pool/dataset/id/{pool}',
                headers=self.headers)
        data = r.json()
        used_space = data['used']['value']
        return to_gb(used_space)
