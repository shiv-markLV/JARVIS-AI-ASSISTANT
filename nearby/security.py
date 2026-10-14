import hashlib
import secrets


class SecurityManager:

    def __init__(self):

        self.device_secret = secrets.token_hex(32)

    def generate_pairing_code(self):

        return str(
            secrets.randbelow(900000) + 100000
        )

    def create_device_fingerprint(self, device_id):

        return hashlib.sha256(
            device_id.encode("utf-8")
        ).hexdigest()

    def verify_device(self, device_id, fingerprint):

        expected = self.create_device_fingerprint(
            device_id
        )

        return secrets.compare_digest(
            expected,
            fingerprint,
        )