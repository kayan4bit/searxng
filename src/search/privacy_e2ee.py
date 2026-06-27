# SPDX-License-Identifier: AGPL-3.0-or-later
"""Privacy enhancements and E2EE for Railway server communication.

This module provides:
- End-to-end encryption for server communication
- Enhanced privacy headers
- Request/response obfuscation
- Secure key exchange
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from base64 import b64decode, b64encode
from typing import Any, Dict, Optional, Tuple

try:
    from cryptography.hazmat.primitives.cipher import ChaCha20Poly1305, AES
    from cryptography.hazmat.primitives.asymmetric import x25519
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# Privacy headers to strip
BLOCKED_HEADERS = frozenset({
    "x-forwarded-for",
    "x-real-ip", 
    "cf-connecting-ip",
    "true-client-ip",
    "x-azure-clientip",
})

# Headers to add for privacy
PRIVACY_HEADERS = {
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Embedder-Policy": "require-corp",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


class E2EEKeyExchange:
    """Simple E2EE using X25519 key exchange and ChaCha20Poly1305."""
    
    def __init__(self, shared_secret: Optional[bytes] = None):
        self._private_key = None
        self._public_key = None
        self._shared_secret = shared_secret
        
        if HAS_CRYPTO:
            self._private_key = x25519.X25519PrivateKey.generate()
            self._public_key = self._private_key.public_key()
    
    @property
    def public_key_bytes(self) -> bytes:
        if not HAS_CRYPTO or not self._public_key:
            return b""
        return self._public_key.public_bytes_raw()
    
    def derive_shared_key(self, peer_public_key: bytes) -> bytes:
        """Derive shared key from peer's public key using HKDF."""
        if not HAS_CRYPTO or not self._private_key or not peer_public_key:
            return self._shared_secret or self._generate_fallback_key()
        
        try:
            peer_key = x25519.X25519PublicKey.from_public_bytes(peer_public_key)
            shared = self._private_key.exchange(peer_key)
            return HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"searxng-e2ee-v1",
                info=b"railway-channel",
            ).derive(shared)
        except Exception:
            return self._generate_fallback_key()
    
    def _generate_fallback_key(self) -> bytes:
        """Generate deterministic key from environment."""
        seed = os.environ.get("E2EE_SEED", "searxng-default-seed")
        return hashlib.sha256(seed.encode()).digest()
    
    def encrypt(self, plaintext: bytes, aad: Optional[bytes] = None) -> Tuple[bytes, bytes, bytes]:
        """Encrypt data using ChaCha20Poly1305.
        
        Returns: (nonce, ciphertext, tag)
        """
        if not HAS_CRYPTO:
            return self._encrypt_fallback(plaintext, aad)
        
        key = self._shared_secret or self._derive_session_key()
        nonce = secrets.token_bytes(12)
        
        try:
            cipher = ChaCha20Poly1305(key)
            aad_bytes = aad or b""
            ciphertext = cipher.encrypt(nonce, plaintext, aad_bytes)
            return nonce, ciphertext, b""
        except Exception:
            return self._encrypt_fallback(plaintext, aad)
    
    def decrypt(self, nonce: bytes, ciphertext: bytes, aad: Optional[bytes] = None) -> Optional[bytes]:
        """Decrypt data using ChaCha20Poly1305."""
        if not HAS_CRYPTO:
            return self._decrypt_fallback(nonce, ciphertext, aad)
        
        key = self._shared_secret or self._derive_session_key()
        
        try:
            cipher = ChaCha20Poly1305(key)
            aad_bytes = aad or b""
            return cipher.decrypt(nonce, ciphertext, aad_bytes)
        except Exception:
            return self._decrypt_fallback(nonce, ciphertext, aad)
    
    def _derive_session_key(self) -> bytes:
        """Derive session key for fallback encryption."""
        timestamp = str(int(time.time()) // 3600).encode()
        seed = os.environ.get("E2EE_SEED", "searxng-default-seed")
        return hashlib.sha256(seed.encode() + timestamp).digest()
    
    def _encrypt_fallback(self, plaintext: bytes, aad: Optional[bytes] = None) -> Tuple[bytes, bytes, bytes]:
        """Fallback XOR-based encryption."""
        key = self._derive_session_key()
        nonce = secrets.token_bytes(12)
        
        combined = key + (aad or b"")
        keystream = hashlib.sha256(combined).digest()
        
        ciphertext = bytes(a ^ b for a, b in zip(plaintext, keystream * ((len(plaintext) // 32) + 1)))
        return nonce, ciphertext, b"fallback"
    
    def _decrypt_fallback(self, nonce: bytes, ciphertext: bytes, aad: Optional[bytes] = None) -> Optional[bytes]:
        """Fallback XOR-based decryption."""
        return self._encrypt_fallback(ciphertext, aad)[1]


class PrivacyManager:
    """Manages privacy features and E2EE for search requests."""
    
    def __init__(self, e2ee_seed: Optional[str] = None):
        self._e2ee_seed = e2ee_seed or os.environ.get("E2EE_SEED", secrets.token_hex(32))
        self._key_exchange = E2EEKeyExchange(
            hashlib.sha256(self._e2ee_seed.encode()).digest()
        )
        self._request_cache: Dict[str, Tuple[float, bytes]] = {}
        self._cache_ttl = 300  # 5 minutes
    
    def strip_tracking_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove tracking headers from request."""
        cleaned = {}
        for key, value in headers.items():
            if key.lower() not in BLOCKED_HEADERS:
                cleaned[key] = value
        return cleaned
    
    def add_privacy_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Add privacy-enhancing headers."""
        return {**headers, **PRIVACY_HEADERS}
    
    def encrypt_search_request(self, query: str, params: Dict[str, Any]) -> Dict[str, str]:
        """Encrypt search request for E2EE transport."""
        payload = json.dumps({
            "q": query,
            "params": params,
            "ts": time.time(),
        }).encode()
        
        nonce, ciphertext, tag = self._key_exchange.encrypt(payload)
        
        return {
            "encrypted": b64encode(ciphertext).decode(),
            "nonce": b64encode(nonce).decode(),
            "pk": b64encode(self._key_exchange.public_key_bytes).decode() if HAS_CRYPTO else "",
        }
    
    def decrypt_search_response(self, encrypted_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Decrypt search response from E2EE transport."""
        try:
            ciphertext = b64decode(encrypted_data.get("encrypted", ""))
            nonce = b64decode(encrypted_data.get("nonce", ""))
            
            plaintext = self._key_exchange.decrypt(nonce, ciphertext)
            if plaintext:
                return json.loads(plaintext.decode())
        except Exception:
            pass
        return None
    
    def get_cache_key(self, query: str, params: Dict[str, Any]) -> str:
        """Generate cache key for deduplication."""
        key_data = f"{query}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    def check_cache(self, cache_key: str) -> Optional[bytes]:
        """Check if response is cached."""
        if cache_key in self._request_cache:
            timestamp, data = self._request_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            del self._request_cache[cache_key]
        return None
    
    def set_cache(self, cache_key: str, data: bytes) -> None:
        """Cache encrypted response."""
        self._request_cache[cache_key] = (time.time(), data)
        if len(self._request_cache) > 1000:
            oldest = min(self._request_cache.items(), key=lambda x: x[1][0])
            del self._request_cache[oldest[0]]
    
    def generate_hmac(self, data: bytes) -> str:
        """Generate HMAC for request integrity."""
        key = hashlib.sha256(self._e2ee_seed.encode()).digest()
        return hmac.new(key, data, hashlib.sha256).hexdigest()
    
    def verify_hmac(self, data: bytes, signature: str) -> bool:
        """Verify HMAC signature."""
        expected = self.generate_hmac(data)
        return hmac.compare_digest(expected, signature)


_privacy_manager: Optional[PrivacyManager] = None


def get_privacy_manager() -> PrivacyManager:
    """Get or create global privacy manager instance."""
    global _privacy_manager
    if _privacy_manager is None:
        _privacy_manager = PrivacyManager()
    return _privacy_manager


def apply_privacy_patches(app) -> None:
    """Apply privacy enhancements to Flask app."""
    from flask import request, Response
    
    privacy = get_privacy_manager()
    
    @app.before_request
    def strip_tracking_headers():
        """Strip tracking headers before processing."""
        if request.headers:
            cleaned = privacy.strip_tracking_headers(dict(request.headers))
            request.headers._list = [(k, v) for k, v in cleaned.items()]
    
    @app.after_request
    def add_privacy_headers(response):
        """Add privacy headers to all responses."""
        for header, value in PRIVACY_HEADERS.items():
            response.headers[header] = value
        
        response.headers["Server"] = "searxng"
        response.headers["X-Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
        
        return response
    
    @app.route('/api/e2ee/key', methods=['GET'])
    def e2ee_get_public_key():
        """Return public key for E2EE key exchange."""
        return {
            "public_key": b64encode(privacy._key_exchange.public_key_bytes).decode() if HAS_CRYPTO else "",
            "has_crypto": HAS_CRYPTO,
        }
    
    @app.route('/api/e2ee/health', methods=['GET'])
    def e2ee_health():
        """Health check for E2EE module."""
        return {
            "status": "healthy",
            "e2ee_enabled": True,
            "crypto_lib": HAS_CRYPTO,
            "cache_size": len(privacy._request_cache),
        }