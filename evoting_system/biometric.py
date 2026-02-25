from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CancellableTemplate:
    template_id: str
    transformed: bytes
    cancel_token: bytes


class BiometricProcessor:
    """Build cancellable templates from fingerprint files."""

    @staticmethod
    def extract_feature_vector(image_path: Path) -> bytes:
        data = image_path.read_bytes()
        return hashlib.sha3_512(data).digest()

    @staticmethod
    def create_cancellable_template(feature_vec: bytes, user_id: str) -> CancellableTemplate:
        cancel_token = secrets.token_bytes(32)
        transformed = bytes(a ^ b for a, b in zip(feature_vec[:32], cancel_token))
        template_id = hashlib.sha256(user_id.encode() + transformed).hexdigest()
        return CancellableTemplate(template_id=template_id, transformed=transformed, cancel_token=cancel_token)

    @staticmethod
    def revoke_and_reissue(feature_vec: bytes, user_id: str) -> CancellableTemplate:
        return BiometricProcessor.create_cancellable_template(feature_vec, user_id)
