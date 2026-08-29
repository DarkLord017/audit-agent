"""What travels through the queue.

Deliberately small: an id and the few things the instancer needs to
start a container. Everything else it can read from Postgres. Fat
messages go stale the moment the row changes.
"""

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class JobMessage:
    job_id: str
    model: str
    profile: str
    upload_path: str
    proxy_token: str

    def to_bytes(self) -> bytes:
        return json.dumps(asdict(self)).encode()

    @classmethod
    def from_bytes(cls, raw: bytes) -> "JobMessage":
        data = json.loads(raw)
        return cls(**{k: data[k] for k in cls.__dataclass_fields__})
