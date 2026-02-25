from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Tuple


# -----------------------------
# Toy additive homomorphic crypto (Paillier-like)
# -----------------------------
# NOTE: This is for educational/research simulation only.


@dataclass
class ToyFHEPublicKey:
    n: int


@dataclass
class ToyFHEPrivateKey:
    n: int


class ToyFHE:
    """A tiny integer-based additive homomorphic scheme for vote tally simulation."""

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


# -----------------------------
# Schnorr-style proof (NIZK via Fiat-Shamir)
# -----------------------------


@dataclass
class ZKProof:
    commitment: int
    response: int


class ToyZKP:
    p = 2_147_483_647  # Mersenne prime
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


# -----------------------------
# Lightweight PQC wrapper
# -----------------------------


@dataclass
class PQKeyPair:
    public_key: bytes
    private_key: bytes


class PQSignature:
    """Fallback PQ-like signature interface.

    If real PQC libs are unavailable, uses HMAC-SHA3 for deterministic simulation.
    """

    @staticmethod
    def keygen() -> PQKeyPair:
        sk = secrets.token_bytes(32)
        pk = hashlib.sha3_256(sk).digest()
        return PQKeyPair(public_key=pk, private_key=sk)

    @staticmethod
    def sign(message: bytes, private_key: bytes) -> bytes:
        return hmac.new(private_key, message, hashlib.sha3_512).digest()

    @staticmethod
    def verify(message: bytes, signature: bytes, keypair: PQKeyPair) -> bool:
        expected = PQSignature.sign(message, keypair.private_key)
        return hmac.compare_digest(expected, signature)


class PQKEM:
    """Fallback PQ-like KEM interface using hash-derived shared secret."""

    @staticmethod
    def keygen() -> PQKeyPair:
        sk = secrets.token_bytes(32)
        pk = hashlib.sha3_256(sk + b"kem").digest()
        return PQKeyPair(public_key=pk, private_key=sk)

    @staticmethod
    def encapsulate(public_key: bytes) -> Tuple[bytes, bytes]:
        eph = secrets.token_bytes(32)
        shared = hashlib.sha3_256(public_key + eph).digest()
        ciphertext = hashlib.sha3_512(public_key + eph).digest()
        return ciphertext, shared

    @staticmethod
    def decapsulate(ciphertext: bytes, keypair: PQKeyPair) -> bytes:
        return hashlib.sha3_256(keypair.public_key + ciphertext[:32]).digest()
