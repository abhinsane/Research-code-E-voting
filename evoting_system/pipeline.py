from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from .biometric import BiometricProcessor, CancellableTemplate
from .blockchain import VoteChain
from .crypto_primitives import DilithiumSignature, HomomorphicTally, KyberKEM, ToyZKP
from .dataset import VoterRecord, discover_socofing_records


@dataclass
class CastVoteReceipt:
    voter_id: str
    candidate: str
    block_hash: str
    zkp_valid: bool
    nullifier: str


class EVotingPipeline:
    def __init__(self, dataset_root: Path, max_voters: int = 30, election_id: str = "default_election") -> None:
        self.dataset_root = dataset_root
        self.voters: List[VoterRecord] = discover_socofing_records(dataset_root, max_records=max_voters)
        self.chain = VoteChain()
        self.election_id = election_id
        self.tally_crypto = HomomorphicTally()
        self.pq_sig_keys = DilithiumSignature.keygen()
        self.pq_kem_keys = KyberKEM.keygen()
        self.templates: Dict[str, CancellableTemplate] = {}
        self.secret_registry: Dict[str, int] = {}
        self.encrypted_tally: Dict[str, object] = {}
        self.used_nullifiers: Set[str] = set()

    def enroll_voters(self) -> None:
        for voter in self.voters:
            feature_vec = BiometricProcessor.extract_feature_vector(voter.image_path)
            template = BiometricProcessor.create_cancellable_template(feature_vec, voter.voter_id)
            self.templates[voter.voter_id] = template
            self.secret_registry[voter.voter_id] = ToyZKP.make_secret()

    def _build_nullifier(self, voter_id: str) -> str:
        material = f"{self.election_id}|{voter_id}|{self.templates[voter_id].template_id}".encode()
        return hashlib.sha256(material).hexdigest()

    def cast_vote(self, voter_id: str, candidate: str) -> CastVoteReceipt:
        if voter_id not in self.templates:
            raise KeyError(f"Voter not enrolled: {voter_id}")

        nullifier = self._build_nullifier(voter_id)
        if nullifier in self.used_nullifiers:
            raise RuntimeError(f"Replay/double-vote blocked for nullifier: {nullifier}")

        secret = self.secret_registry[voter_id]
        public = ToyZKP.public_from_secret(secret)
        cast_nonce = secrets.token_hex(8)
        ctx = f"{self.election_id}:{voter_id}:{candidate}:{nullifier}:{cast_nonce}"
        proof = ToyZKP.prove_knowledge(secret, ctx)
        zkp_valid = ToyZKP.verify_knowledge(public, proof, ctx)
        if not zkp_valid:
            raise RuntimeError("ZKP verification failed; vote rejected")

        encrypted_vote = self.tally_crypto.encrypt_scalar(1)
        prior = self.encrypted_tally.get(candidate)
        if prior is None:
            self.encrypted_tally[candidate] = encrypted_vote
        else:
            self.encrypted_tally[candidate] = self.tally_crypto.add(prior, encrypted_vote)

        payload = {
            "election_id": self.election_id,
            "voter_id": voter_id,
            "candidate": candidate,
            "nullifier": nullifier,
            "nonce": cast_nonce,
            "zkp": {"commitment": proof.commitment, "response": proof.response},
            "template_id": self.templates[voter_id].template_id,
            "he_backend": self.tally_crypto.backend,
        }
        serialized = json.dumps(payload, sort_keys=True).encode()
        signature = DilithiumSignature.sign(serialized, self.pq_sig_keys.private_key).hex()
        kem_ct, _ = KyberKEM.encapsulate(self.pq_kem_keys.public_key)
        payload["dilithium_signature"] = signature
        payload["kyber_kem_ct"] = kem_ct.hex()

        block = self.chain.add_block(payload)
        self.used_nullifiers.add(nullifier)
        return CastVoteReceipt(
            voter_id=voter_id,
            candidate=candidate,
            block_hash=block.hash,
            zkp_valid=zkp_valid,
            nullifier=nullifier,
        )

    def decrypt_results(self) -> Dict[str, int]:
        return {candidate: self.tally_crypto.decrypt_scalar(enc) for candidate, enc in self.encrypted_tally.items()}
