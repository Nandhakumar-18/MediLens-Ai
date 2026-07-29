import hmac
import hashlib
import time
import struct
import base64
import random
import string
import io
from urllib.parse import quote
import qrcode
import qrcode.image.svg

class TOTPAuthenticator:
    """
    100% Offline RFC 6238 Time-Based One-Time Password (TOTP) Authenticator.
    100% Compatible with Google Authenticator, Microsoft Authenticator, Authy, and Apple Keychain.
    Requires 0% Internet and 0% external cloud services.
    """

    def generate_secret(self, length=16) -> str:
        """Generates a random 16-character Base32 secret key."""
        base32_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
        return "".join(random.choice(base32_chars) for _ in range(length))

    def _get_time_counter(self, time_step=30, for_time=None) -> int:
        current_time = int(time.time()) if for_time is None else int(for_time)
        return current_time // time_step

    def get_totp_token(self, secret_base32: str, time_step=30, for_time=None) -> str:
        """Computes current 6-digit TOTP token using HMAC-SHA1 algorithm (RFC 6238)."""
        try:
            secret_clean = secret_base32.upper().strip()
            missing_padding = len(secret_clean) % 8
            if missing_padding:
                secret_clean += '=' * (8 - missing_padding)
            
            key = base64.b32decode(secret_clean, casefold=True)
            counter = self._get_time_counter(time_step, for_time)
            
            msg = struct.pack(">Q", counter)
            hmac_hash = hmac.new(key, msg, hashlib.sha1).digest()
            
            offset = hmac_hash[-1] & 0x0F
            binary_code = (
                ((hmac_hash[offset] & 0x7F) << 24) |
                ((hmac_hash[offset + 1] & 0xFF) << 16) |
                ((hmac_hash[offset + 2] & 0xFF) << 8) |
                (hmac_hash[offset + 3] & 0xFF)
            )
            
            totp = binary_code % 1000000
            return f"{totp:06d}"
        except Exception as e:
            print("TOTP generation error:", e)
            return "000000"

    def verify_totp_token(self, secret_base32: str, token: str, time_step=30, window=1) -> bool:
        """Verifies if input token matches TOTP within current or adjacent time windows."""
        clean_token = ''.join(filter(str.isdigit, str(token)))
        if len(clean_token) != 6:
            return False

        current_time = int(time.time())
        for offset in range(-window, window + 1):
            target_time = current_time + (offset * time_step)
            expected_token = self.get_totp_token(secret_base32, time_step=time_step, for_time=target_time)
            if hmac.compare_digest(clean_token, expected_token):
                return True
        return False

    def generate_otpauth_uri(self, username: str, secret_base32: str, issuer: str = "MediLensAI") -> str:
        """Generates standard otpauth:// URI string compatible with Google Authenticator."""
        label = quote(f"{issuer}:{username}")
        issuer_encoded = quote(issuer)
        return f"otpauth://totp/{label}?secret={secret_base32}&issuer={issuer_encoded}&algorithm=SHA1&digits=6&period=30"

    def generate_svg_qr(self, data: str) -> str:
        """
        Generates a 100% compliant, scannable SVG QR code for Google & Microsoft Authenticator.
        """
        try:
            factory = qrcode.image.svg.SvgPathImage
            img = qrcode.make(data, image_factory=factory, box_size=8, border=2)
            stream = io.BytesIO()
            img.save(stream)
            svg_xml = stream.getvalue().decode('utf-8')
            
            # Custom styling container
            styled_svg = f'<div style="background:#ffffff; padding:12px; border-radius:12px; display:inline-block; border:2px solid #00d4ff;">{svg_xml}</div>'
            return styled_svg
        except Exception as e:
            print("QR code SVG error:", e)
            return "<div>QR Code Generation Failed</div>"
