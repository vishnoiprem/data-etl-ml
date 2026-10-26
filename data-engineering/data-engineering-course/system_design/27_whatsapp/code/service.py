"""WhatsApp-style group messaging service with toy E2E key model."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore

MAX_GROUP_SIZE = 1024
GROUP_HISTORY_CAP = 5000
INBOX_CAP = 1000


@dataclass
class Group:
    group_id: int
    name: str
    creator_id: int
    members: list
    key_id: str
    key_version: int
    created_at: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GroupMessage:
    message_id: int
    group_id: int
    sender_id: int
    body: str
    media_url: Optional[str]
    media_b64: Optional[str]
    key_id: str
    ts: float

    def to_dict(self) -> dict:
        return asdict(self)


class WhatsAppService:
    """Group chat with toy E2E 'encryption' (we just store a per-group key).

    >>> svc = WhatsAppService()
    >>> g = svc.create_group("family", creator_id=1, members=[1, 2, 3])
    >>> m = svc.send_message(g.group_id, sender_id=1, body="hi all")
    >>> msgs = svc.fetch_messages(g.group_id)
    >>> len(msgs) >= 1
    True
    """

    def __init__(self):
        self.snow = Snowflake(machine_id=27)
        self.groups = KeyValueStore("wa_groups")
        self.msgs = KeyValueStore("wa_messages")
        self.gmsgs = KeyValueStore("wa_group_msgs")  # group_id -> [msg_id]
        self.user_groups = KeyValueStore("wa_user_groups")  # user_id -> [group_id]
        self.inbox = KeyValueStore("wa_inbox")  # user_id -> [msg_id]

    # ---- groups -------------------------------------------------------

    def create_group(self, name: str, creator_id: int, members: list) -> Group:
        if not name or not isinstance(name, str):
            raise ValueError("group name required")
        if creator_id in (None,):
            raise ValueError("creator_id required")
        members = sorted(set(int(m) for m in (members or []) + [int(creator_id)]))
        if len(members) > MAX_GROUP_SIZE:
            raise ValueError(f"group too large (>{MAX_GROUP_SIZE})")
        gid = self.snow.next_id()
        g = Group(
            group_id=gid,
            name=name,
            creator_id=int(creator_id),
            members=members,
            key_id=self._mint_key_id(gid, 1),
            key_version=1,
            created_at=time.time(),
        )
        self.groups.set(f"group:{gid}", g.to_dict())
        for uid in members:
            ug = self.user_groups.get(f"user_groups:{uid}") or []
            if gid not in ug:
                ug.append(gid)
            self.user_groups.set(f"user_groups:{uid}", ug)
        return g

    def get_group(self, group_id: int) -> Optional[Group]:
        d = self.groups.get(f"group:{group_id}")
        return Group(**d) if d else None

    def add_member(self, group_id: int, user_id: int) -> Group:
        g = self.get_group(group_id)
        if not g:
            raise ValueError("group not found")
        uid = int(user_id)
        if uid in g.members:
            return g
        if len(g.members) + 1 > MAX_GROUP_SIZE:
            raise ValueError("group full")
        g.members = sorted(set(g.members + [uid]))
        g.key_version += 1
        g.key_id = self._mint_key_id(group_id, g.key_version)
        self.groups.set(f"group:{group_id}", g.to_dict())
        ug = self.user_groups.get(f"user_groups:{uid}") or []
        if group_id not in ug:
            ug.append(group_id)
        self.user_groups.set(f"user_groups:{uid}", ug)
        return g

    def remove_member(self, group_id: int, user_id: int) -> Group:
        g = self.get_group(group_id)
        if not g:
            raise ValueError("group not found")
        uid = int(user_id)
        if uid not in g.members:
            return g
        g.members = [m for m in g.members if m != uid]
        g.key_version += 1
        g.key_id = self._mint_key_id(group_id, g.key_version)
        self.groups.set(f"group:{group_id}", g.to_dict())
        ug = self.user_groups.get(f"user_groups:{uid}") or []
        if group_id in ug:
            ug.remove(group_id)
        self.user_groups.set(f"user_groups:{uid}", ug)
        return g

    def groups_for(self, user_id: int) -> list[Group]:
        gids = self.user_groups.get(f"user_groups:{user_id}") or []
        out: list[Group] = []
        for gid in gids:
            g = self.get_group(gid)
            if g:
                out.append(g)
        return out

    # ---- messages -----------------------------------------------------

    def send_message(
        self,
        group_id: int,
        sender_id: int,
        body: str,
        media_url: Optional[str] = None,
        media_b64: Optional[str] = None,
    ) -> GroupMessage:
        g = self.get_group(group_id)
        if not g:
            raise ValueError("group not found")
        if int(sender_id) not in g.members:
            raise ValueError("sender not in group")
        if not body and not media_url and not media_b64:
            raise ValueError("empty message")
        mid = self.snow.next_id()
        ts = time.time()
        m = GroupMessage(
            message_id=mid,
            group_id=group_id,
            sender_id=int(sender_id),
            body=body or "",
            media_url=media_url,
            media_b64=media_b64,
            key_id=g.key_id,
            ts=ts,
        )
        self.msgs.set(f"gmsg:{mid}", m.to_dict())

        # Append to group history.
        ids = self.gmsgs.get(f"gmsgs:{group_id}") or []
        ids.append(mid)
        if len(ids) > GROUP_HISTORY_CAP:
            ids = ids[-GROUP_HISTORY_CAP:]
        self.gmsgs.set(f"gmsgs:{group_id}", ids)

        # Fan out to per-user inbox for every current member.
        for uid in g.members:
            inb = self.inbox.get(f"inbox:{uid}") or []
            inb.append(mid)
            if len(inb) > INBOX_CAP:
                inb = inb[-INBOX_CAP:]
            self.inbox.set(f"inbox:{uid}", inb)

        return m

    def fetch_messages(
        self, group_id: int, since_ts: float = 0.0, limit: int = 200
    ) -> list[GroupMessage]:
        ids = self.gmsgs.get(f"gmsgs:{group_id}") or []
        out: list[GroupMessage] = []
        for mid in ids:
            d = self.msgs.get(f"gmsg:{mid}")
            if not d:
                continue
            if d["ts"] > since_ts:
                out.append(GroupMessage(**d))
            if len(out) >= limit:
                break
        return out

    def fetch_inbox(self, user_id: int, since_ts: float = 0.0, limit: int = 200) -> list[GroupMessage]:
        ids = self.inbox.get(f"inbox:{user_id}") or []
        out: list[GroupMessage] = []
        for mid in ids:
            d = self.msgs.get(f"gmsg:{mid}")
            if not d:
                continue
            if d["ts"] > since_ts:
                out.append(GroupMessage(**d))
            if len(out) >= limit:
                break
        return out

    # ---- helpers ------------------------------------------------------

    def _mint_key_id(self, group_id: int, version: int) -> str:
        # Toy model: deterministic, NOT a real crypto key.
        return f"key-{group_id}-v{version}-{os.urandom(4).hex()}"

    def stats(self) -> dict:
        return {
            "groups": self.groups.size(),
            "messages": self.msgs.size(),
            "inbox_entries": self.inbox.size(),
        }
