from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class ZKProof:
    commitment: int
    response: int


class ToyZKP:
    p = 2_147_483_647
    g = 5

    @classmethod
    def make_secret(cls) -> int:
        return secrets.randbelow(cls.p - 2) + 1

    @classmethod
    def public_from_secret(cls, secret: int) -> int:
        return pow(cls.g, secret, cls.p)

    @classmethod
    def _challenge(cls, commitment: int, public: int, context: str) -> int:
        payload = f"{commitment}|{public}|{context}".encode()
        digest = hashlib.sha256(payload).hexdigest()
        return int(digest, 16) % (cls.p - 1)

    @classmethod
    def prove_knowledge(cls, secret: int, context: str) -> ZKProof:
        r = secrets.randbelow(cls.p - 2) + 1
        t = pow(cls.g, r, cls.p)
        y = cls.public_from_secret(secret)
        c = cls._challenge(t, y, context)
        s = (r + c * secret) % (cls.p - 1)
        return ZKProof(commitment=t, response=s)

    @classmethod
    def verify_knowledge(cls, public: int, proof: ZKProof, context: str) -> bool:
        c = cls._challenge(proof.commitment, public, context)
        lhs = pow(cls.g, proof.response, cls.p)
        rhs = (proof.commitment * pow(public, c, cls.p)) % cls.p
        return lhs == rhs


@dataclass
class ToyFHEPublicKey:
    n: int


@dataclass
class ToyFHEPrivateKey:
    n: int


class ToyFHE:
    """Tiny integer additive-homomorphic scheme used when real HE backend is unavailable."""

    @staticmethod
    def keygen(modulus_bits: int = 31) -> Tuple[ToyFHEPublicKey, ToyFHEPrivateKey]:
        n = secrets.randbits(modulus_bits) | 1
        return ToyFHEPublicKey(n=n), ToyFHEPrivateKey(n=n)

    @staticmethod
    def encrypt(value: int, pk: ToyFHEPublicKey) -> int:
        r = secrets.randbelow(pk.n)
        return (value + r * pk.n) % (pk.n * pk.n)

    @staticmethod
    def add(c1: int, c2: int, pk: ToyFHEPublicKey) -> int:
        return (c1 + c2) % (pk.n * pk.n)

    @staticmethod
    def decrypt(ciphertext: int, sk: ToyFHEPrivateKey) -> int:
        return ciphertext % sk.n


class HomomorphicTally:
    """Backend-agnostic tally layer.

    Uses Microsoft SEAL via TenSEAL if available, otherwise falls back to ToyFHE.
    """

    def __init__(self) -> None:
        self.backend = "toy-fhe"
        self._ts = None
        try:
            import tenseal as ts  # type: ignore

            self._ts = ts
            self._ctx = ts.context(
                ts.SCHEME_TYPE.BFV,
                poly_modulus_degree=4096,
                plain_modulus=1032193,
            )
            self._ctx.generate_galois_keys()
            self.backend = "seal-bfv-tenseal"
        except Exception:
            self.pk, self.sk = ToyFHE.keygen()

    def encrypt_scalar(self, value: int):
        if self.backend == "seal-bfv-tenseal":
            return self._ts.bfv_vector(self._ctx, [value])
        return ToyFHE.encrypt(value, self.pk)

    def add(self, c1, c2):
        if self.backend == "seal-bfv-tenseal":
            return c1 + c2
        return ToyFHE.add(c1, c2, self.pk)

    def decrypt_scalar(self, ciphertext) -> int:
        if self.backend == "seal-bfv-tenseal":
            return int(ciphertext.decrypt()[0])
        return ToyFHE.decrypt(ciphertext, self.sk)


@dataclass
class PQKeyPair:
    public_key: bytes
    private_key: bytes


class DilithiumSignature:
    """CRYSTALS-Dilithium signature wrapper via liboqs (python-oqs).

    If liboqs is unavailable, uses deterministic HMAC fallback to keep the
    research pipeline runnable in constrained environments.
    """

    algorithm = "Dilithium2"

    @classmethod
    def keygen(cls) -> PQKeyPair:
        try:
            import oqs  # type: ignore

            signer = oqs.Signature(cls.algorithm)
            public_key = signer.generate_keypair()
            secret_key = signer.export_secret_key()
            return PQKeyPair(public_key=public_key, private_key=secret_key)
        except Exception:
            sk = secrets.token_bytes(32)
            pk = hashlib.sha3_256(sk).digest()
            return PQKeyPair(public_key=pk, private_key=sk)

    @classmethod
    def sign(cls, message: bytes, private_key: bytes) -> bytes:
        try:
            import oqs  # type: ignore

            signer = oqs.Signature(cls.algorithm, secret_key=private_key)
            return signer.sign(message)
        except Exception:
            return hmac.new(private_key, message, hashlib.sha3_512).digest()

    @classmethod
    def verify(cls, message: bytes, signature: bytes, keypair: PQKeyPair) -> bool:
        try:
            import oqs  # type: ignore

            verifier = oqs.Signature(cls.algorithm)
            return bool(verifier.verify(message, signature, keypair.public_key))
        except Exception:
            expected = cls.sign(message, keypair.private_key)
            return hmac.compare_digest(expected, signature)


class KyberKEM:
    """Kyber KEM wrapper via liboqs (ML-KEM compatible family)."""

    algorithm = "Kyber512"
    _fallback_state: Dict[bytes, bytes] = {}

    @classmethod
    def keygen(cls) -> PQKeyPair:
        try:
            import oqs  # type: ignore

            kem = oqs.KeyEncapsulation(cls.algorithm)
            public_key = kem.generate_keypair()
            secret_key = kem.export_secret_key()
            return PQKeyPair(public_key=public_key, private_key=secret_key)
        except Exception:
            sk = secrets.token_bytes(32)
            pk = hashlib.sha3_256(sk + b"kyber").digest()
            return PQKeyPair(public_key=pk, private_key=sk)

    @classmethod
    def encapsulate(cls, public_key: bytes) -> Tuple[bytes, bytes]:
        try:
            import oqs  # type: ignore

            kem = oqs.KeyEncapsulation(cls.algorithm)
            ciphertext, shared_secret = kem.encap_secret(public_key)
            return ciphertext, shared_secret
        except Exception:
            seed = secrets.token_bytes(32)
            ciphertext = hashlib.sha3_512(public_key + seed).digest()
            shared = hashlib.sha3_256(seed + public_key).digest()
            cls._fallback_state[ciphertext] = shared
            return ciphertext, shared

    @classmethod
    def decapsulate(cls, ciphertext: bytes, keypair: PQKeyPair) -> bytes:
        try:
            import oqs  # type: ignore

            kem = oqs.KeyEncapsulation(cls.algorithm, secret_key=keypair.private_key)
            return kem.decap_secret(ciphertext)
        except Exception:
            if ciphertext in cls._fallback_state:
                return cls._fallback_state[ciphertext]
            return hashlib.sha3_256(ciphertext + keypair.public_key).digest()
