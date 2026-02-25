from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Block:
    index: int
    previous_hash: str
    timestamp: float
    payload: Dict[str, Any]
    nonce: int = 0
    hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        block_data = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "nonce": self.nonce,
        }
        encoded = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()


class VoteChain:
    def __init__(self, difficulty_prefix: str = "000") -> None:
        self.difficulty_prefix = difficulty_prefix
        genesis = Block(index=0, previous_hash="0" * 64, timestamp=time.time(), payload={"genesis": True})
        self.chain: List[Block] = [genesis]

    def add_block(self, payload: Dict[str, Any]) -> Block:
        prev = self.chain[-1]
        block = Block(index=len(self.chain), previous_hash=prev.hash, timestamp=time.time(), payload=payload)
        while not block.hash.startswith(self.difficulty_prefix):
            block.nonce += 1
            block.hash = block.compute_hash()
        self.chain.append(block)
        return block

    def validate_chain(self) -> bool:
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr.previous_hash != prev.hash:
                return False
            if curr.compute_hash() != curr.hash:
                return False
            if not curr.hash.startswith(self.difficulty_prefix):
                return False
        return True
