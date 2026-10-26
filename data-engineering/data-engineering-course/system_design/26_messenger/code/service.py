"""Facebook Messenger-style service: 1:1 conversations, messages, presence.

This service is intentionally in-memory + JSON-persisted (via
``common.storage.KeyValueStore``). In a real system the message store
would be a partitioned write-ahead log (Kafka + Cassandra) and the
per-user inbox would live in a read-optimized KV store (HBase/RocksDB).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore

PRESENCE_TTL = 30.0
INBOX_CAP = 1000


@dataclass
class Conversation:
    conversation_id: int
    user_a: int
    user_b: int
    created_at: float

    def participants(self) -> tuple[int, int]:
        # Always normalized so equality checks work.
        return tuple(sorted([self.user_a, self.user_b]))  # type: ignore[return-value]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Message:
    message_id: int
    conversation_id: int
    sender_id: int
    body: str
    ts: float

    def to_dict(self) -> dict:
        return asdict(self)


class MessengerService:
    """1:1 messenger with conversations, inboxes, and presence.

    >>> svc = MessengerService()
    >>> cid = svc.create_conversation(1, 2)
    >>> m = svc.send_message(cid, sender_id=1, body="hi")
    >>> msgs = svc.fetch_messages(cid)
    >>> len(msgs) >= 1
    True
    """

    def __init__(self):
        self.snow = Snowflake(machine_id=26)
        self.convs = KeyValueStore("msgr_conversations")
        self.msgs = KeyValueStore("msgr_messages")
        self.conv_msgs = KeyValueStore("msgr_conv_msgs")  # conv_id -> [msg_id]
        self.inbox = KeyValueStore("msgr_inbox")  # user_id -> [msg_id]
        self.pair_index = KeyValueStore("msgr_pair")  # "u1:u2" -> conv_id
        self.presence = TTLCache(ttl_seconds=PRESENCE_TTL, max_entries=200_000)
        # In-process listener registry: user_id -> [queue.Queue]
        self._listeners: dict[int, list["__import__('queue').Queue"]] = {}

    # ---- conversations ------------------------------------------------

    def _pair_key(self, a: int, b: int) -> str:
        x, y = sorted([int(a), int(b)])
        return f"{x}:{y}"

    def create_conversation(self, user_a: int, user_b: int) -> Conversation:
        if user_a == user_b:
            raise ValueError("cannot start a conversation with yourself")
        key = self._pair_key(user_a, user_b)
        existing = self.pair_index.get(key)
        if existing is not None:
            d = self.convs.get(f"conv:{existing}")
            return Conversation(**d) if d else self._new_conv(user_a, user_b, key)
        return self._new_conv(user_a, user_b, key)

    def _new_conv(self, user_a: int, user_b: int, pair_key: str) -> Conversation:
        cid = self.snow.next_id()
        c = Conversation(
            conversation_id=cid,
            user_a=int(user_a),
            user_b=int(user_b),
            created_at=time.time(),
        )
        self.convs.set(f"conv:{cid}", c.to_dict())
        self.pair_index.set(pair_key, cid)
        return c

    def get_conversation(self, conv_id: int) -> Optional[Conversation]:
        d = self.convs.get(f"conv:{conv_id}")
        return Conversation(**d) if d else None

    # ---- messages -----------------------------------------------------

    def send_message(
        self, conv_id: int, sender_id: int, body: str
    ) -> Message:
        c = self.get_conversation(conv_id)
        if not c:
            raise ValueError("conversation not found")
        if sender_id not in (c.user_a, c.user_b):
            raise ValueError("sender is not a participant")
        if not isinstance(body, str) or not body:
            raise ValueError("body must be a non-empty string")

        mid = self.snow.next_id()
        ts = time.time()
        m = Message(
            message_id=mid,
            conversation_id=conv_id,
            sender_id=int(sender_id),
            body=body,
            ts=ts,
        )
        self.msgs.set(f"msg:{mid}", m.to_dict())

        # Append to conversation list.
        ids = self.conv_msgs.get(f"conv_msgs:{conv_id}") or []
        ids.append(mid)
        self.conv_msgs.set(f"conv_msgs:{conv_id}", ids)

        # Fan out to per-user inboxes for both participants.
        for uid in (c.user_a, c.user_b):
            inb = self.inbox.get(f"inbox:{uid}") or []
            inb.append(mid)
            if len(inb) > INBOX_CAP:
                inb = inb[-INBOX_CAP:]
            self.inbox.set(f"inbox:{uid}", inb)
            self._notify_listeners(int(uid), m)

        return m

    def fetch_messages(
        self, conv_id: int, since_ts: float = 0.0, limit: int = 200
    ) -> list[Message]:
        ids = self.conv_msgs.get(f"conv_msgs:{conv_id}") or []
        out: list[Message] = []
        for mid in ids:
            d = self.msgs.get(f"msg:{mid}")
            if not d:
                continue
            if d["ts"] > since_ts:
                out.append(Message(**d))
            if len(out) >= limit:
                break
        return out

    def fetch_inbox(self, user_id: int, since_ts: float = 0.0, limit: int = 200) -> list[Message]:
        ids = self.inbox.get(f"inbox:{user_id}") or []
        out: list[Message] = []
        for mid in ids:
            d = self.msgs.get(f"msg:{mid}")
            if not d:
                continue
            if d["ts"] > since_ts:
                out.append(Message(**d))
            if len(out) >= limit:
                break
        return out

    def get_message(self, message_id: int) -> Optional[Message]:
        d = self.msgs.get(f"msg:{message_id}")
        return Message(**d) if d else None

    # ---- presence -----------------------------------------------------

    def heartbeat(self, user_id: int) -> None:
        self.presence.set(f"presence:{user_id}", time.time(), ttl_seconds=PRESENCE_TTL)

    def is_online(self, user_id: int) -> bool:
        return self.presence.get(f"presence:{user_id}") is not None

    def last_seen(self, user_id: int) -> Optional[float]:
        return self.presence.get(f"presence:{user_id}")

    # ---- listeners / SSE plumbing ------------------------------------

    def _notify_listeners(self, user_id: int, message: Message) -> None:
        for q in list(self._listeners.get(user_id, [])):
            try:
                q.put_nowait(message.to_dict())
            except Exception:
                # Queue is full or closed — drop silently. The client will
                # reconnect with since_ts.
                pass

    def register_listener(self, user_id: int) -> "queue.Queue":  # type: ignore[name-defined]
        import queue
        q: "queue.Queue" = queue.Queue(maxsize=100)
        self._listeners.setdefault(int(user_id), []).append(q)
        return q

    def unregister_listener(self, user_id: int, q) -> None:  # type: ignore[no-untyped-def]
        lst = self._listeners.get(int(user_id), [])
        if q in lst:
            lst.remove(q)

    # ---- ops ----------------------------------------------------------

    def stats(self) -> dict:
        return {
            "conversations": self.convs.size(),
            "messages": self.msgs.size(),
            "inbox_entries": self.inbox.size(),
            "online_users": self._count_online(),
            "presence_cache": self.presence.stats(),
        }

    def _count_online(self) -> int:
        # Walk the in-memory presence cache.
        return len([k for k in self.presence._data.keys() if k.startswith("presence:")])  # type: ignore[attr-defined]
