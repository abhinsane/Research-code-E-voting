from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .biometric import BiometricProcessor, CancellableTemplate
from .blockchain import VoteChain
from .crypto_primitives import PQKEM, PQSignature, ToyFHE, ToyZKP
from .dataset import VoterRecord, discover_socofing_records


@dataclass
class CastVoteReceipt:
    voter_id: str
    candidate: str
    block_hash: str
    zkp_valid: bool


class EVotingPipeline:
    def __init__(self, dataset_root: Path, max_voters: int = 30) -> None:
        self.dataset_root = dataset_root
        self.voters: List[VoterRecord] = discover_socofing_records(dataset_root, max_records=max_voters)
        self.chain = VoteChain()
        self.fhe_pk, self.fhe_sk = ToyFHE.keygen()
        self.pq_sig_keys = PQSignature.keygen()
        self.pq_kem_keys = PQKEM.keygen()
        self.templates: Dict[str, CancellableTemplate] = {}
        self.secret_registry: Dict[str, int] = {}
        self.encrypted_tally: Dict[str, int] = {}

    def enroll_voters(self) -> None:
        for voter in self.voters:
            feature_vec = BiometricProcessor.extract_feature_vector(voter.image_path)
            template = BiometricProcessor.create_cancellable_template(feature_vec, voter.voter_id)
            self.templates[voter.voter_id] = template
            self.secret_registry[voter.voter_id] = ToyZKP.make_secret()

    def cast_vote(self, voter_id: str, candidate: str) -> CastVoteReceipt:
        if voter_id not in self.templates:
            raise KeyError(f"Voter not enrolled: {voter_id}")

        secret = self.secret_registry[voter_id]
        public = ToyZKP.public_from_secret(secret)
        ctx = f"{voter_id}:{candidate}"
        proof = ToyZKP.prove_knowledge(secret, ctx)
        zkp_valid = ToyZKP.verify_knowledge(public, proof, ctx)
        if not zkp_valid:
            raise RuntimeError("ZKP verification failed; vote rejected")

        encrypted_vote = ToyFHE.encrypt(1, self.fhe_pk)
        prior = self.encrypted_tally.get(candidate, ToyFHE.encrypt(0, self.fhe_pk))
        self.encrypted_tally[candidate] = ToyFHE.add(prior, encrypted_vote, self.fhe_pk)

        payload = {
            "voter_id": voter_id,
            "candidate": candidate,
            "zkp": {"commitment": proof.commitment, "response": proof.response},
            "template_id": self.templates[voter_id].template_id,
        }
        serialized = json.dumps(payload, sort_keys=True).encode()
        signature = PQSignature.sign(serialized, self.pq_sig_keys.private_key).hex()
        kem_ct, _ = PQKEM.encapsulate(self.pq_kem_keys.public_key)
        payload["pqc_signature"] = signature
        payload["pqc_kem_ct"] = kem_ct.hex()

        block = self.chain.add_block(payload)
        return CastVoteReceipt(voter_id=voter_id, candidate=candidate, block_hash=block.hash, zkp_valid=zkp_valid)

    def decrypt_results(self) -> Dict[str, int]:
        return {candidate: ToyFHE.decrypt(enc, self.fhe_sk) for candidate, enc in self.encrypted_tally.items()}
