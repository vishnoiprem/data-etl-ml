"""Slack-like service: workspaces, channels, threads, mentions, search."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from common.ids import Snowflake
from common.storage import KeyValueStore

CHANNEL_HISTORY_CAP = 5000
THREAD_CAP = 1000
INDEX_TERM_CAP = 1000
MENTION_RE = re.compile(r"@([A-Za-z0-9_\-]+)")


@dataclass
class Workspace:
    workspace_id: int
    name: str
    created_at: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Channel:
    channel_id: int
    workspace_id: int
    name: str
    creator_id: int
    created_at: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Message:
    message_id: int
    channel_id: int
    user_id: int
    body: str
    thread_to: Optional[int]
    mentions: list
    ts: float

    def to_dict(self) -> dict:
        return asdict(self)


class SlackService:
    """Workspace + channel + threaded messaging with toy search.

    >>> svc = SlackService()
    >>> w = svc.create_workspace("acme")
    >>> ch = svc.create_channel(w.workspace_id, "general", creator_id=1)
    >>> m = svc.post_message(ch.channel_id, user_id=1, body="hello @2")
    >>> m.mentions
    [2]
    """

    def __init__(self):
        self.snow = Snowflake(machine_id=29)
        self.workspaces = KeyValueStore("slack_workspaces")
        self.channels = KeyValueStore("slack_channels")
        self.msgs = KeyValueStore("slack_messages")
        self.channel_msgs = KeyValueStore("slack_channel_msgs")
        self.threads = KeyValueStore("slack_threads")
        self.mentions = KeyValueStore("slack_mentions")
        self.index = KeyValueStore("slack_index")
        self.workspace_channels = KeyValueStore("slack_ws_channels")

    # ---- workspaces / channels ---------------------------------------

    def create_workspace(self, name: str) -> Workspace:
        if not name:
            raise ValueError("name required")
        wid = self.snow.next_id()
        w = Workspace(workspace_id=wid, name=name, created_at=time.time())
        self.workspaces.set(f"ws:{wid}", w.to_dict())
        return w

    def get_workspace(self, workspace_id: int) -> Optional[Workspace]:
        d = self.workspaces.get(f"ws:{workspace_id}")
        return Workspace(**d) if d else None

    def create_channel(
        self, workspace_id: int, name: str, creator_id: int
    ) -> Channel:
        if not name:
            raise ValueError("channel name required")
        if not self.get_workspace(workspace_id):
            raise ValueError("workspace not found")
        cid = self.snow.next_id()
        ch = Channel(
            channel_id=cid,
            workspace_id=int(workspace_id),
            name=name,
            creator_id=int(creator_id),
            created_at=time.time(),
        )
        self.channels.set(f"ch:{cid}", ch.to_dict())
        ws_chs = self.workspace_channels.get(f"ws_channels:{workspace_id}") or []
        if cid not in ws_chs:
            ws_chs.append(cid)
        self.workspace_channels.set(f"ws_channels:{workspace_id}", ws_chs)
        return ch

    def get_channel(self, channel_id: int) -> Optional[Channel]:
        d = self.channels.get(f"ch:{channel_id}")
        return Channel(**d) if d else None

    def channels_in(self, workspace_id: int) -> list[Channel]:
        cids = self.workspace_channels.get(f"ws_channels:{workspace_id}") or []
        out = []
        for cid in cids:
            ch = self.get_channel(cid)
            if ch:
                out.append(ch)
        return out

    # ---- messages -----------------------------------------------------

    def post_message(
        self,
        channel_id: int,
        user_id: int,
        body: str,
        thread_to: Optional[int] = None,
    ) -> Message:
        ch = self.get_channel(channel_id)
        if not ch:
            raise ValueError("channel not found")
        if not isinstance(body, str) or not body:
            raise ValueError("body required")
        # If threading, parent must exist in the same channel and be top-level.
        if thread_to is not None:
            parent = self._get_msg(thread_to)
            if not parent:
                raise ValueError("parent message not found")
            if parent.channel_id != channel_id:
                raise ValueError("parent message in different channel")
            if parent.thread_to is not None:
                raise ValueError("cannot reply to a thread reply (flatten)")

        mid = self.snow.next_id()
        ts = time.time()
        # Extract mentions like @user — accept any token as user id.
        mentioned: list[int] = []
        for m in MENTION_RE.finditer(body):
            tok = m.group(1)
            try:
                mentioned.append(int(tok))
            except ValueError:
                # Toy: only integer user ids trigger notification.
                continue

        msg = Message(
            message_id=mid,
            channel_id=int(channel_id),
            user_id=int(user_id),
            body=body,
            thread_to=int(thread_to) if thread_to is not None else None,
            mentions=mentioned,
            ts=ts,
        )
        self.msgs.set(f"msg:{mid}", msg.to_dict())

        if thread_to is not None:
            tids = self.threads.get(f"thread:{thread_to}") or []
            tids.append(mid)
            if len(tids) > THREAD_CAP:
                tids = tids[-THREAD_CAP:]
            self.threads.set(f"thread:{thread_to}", tids)
        else:
            ids = self.channel_msgs.get(f"channel_msgs:{channel_id}") or []
            ids.append(mid)
            if len(ids) > CHANNEL_HISTORY_CAP:
                ids = ids[-CHANNEL_HISTORY_CAP:]
            self.channel_msgs.set(f"channel_msgs:{channel_id}", ids)

        # Mentions: per-user inbox of message_ids.
        for uid in mentioned:
            um = self.mentions.get(f"user_mentions:{uid}") or []
            um.append(mid)
            if len(um) > CHANNEL_HISTORY_CAP:
                um = um[-CHANNEL_HISTORY_CAP:]
            self.mentions.set(f"user_mentions:{uid}", um)

        # Index terms.
        for term in self._tokenize(body):
            lst = self.index.get(f"idx:{term}") or []
            if mid not in lst:
                lst.append(mid)
                if len(lst) > INDEX_TERM_CAP:
                    lst = lst[-INDEX_TERM_CAP:]
            self.index.set(f"idx:{term}", lst)

        return msg

    def get_message(self, message_id: int) -> Optional[Message]:
        d = self.msgs.get(f"msg:{message_id}")
        return Message(**d) if d else None

    def _get_msg(self, message_id: int) -> Optional[Message]:
        return self.get_message(message_id)

    def fetch_messages(
        self, channel_id: int, since_ts: float = 0.0, limit: int = 100
    ) -> list[Message]:
        ids = self.channel_msgs.get(f"channel_msgs:{channel_id}") or []
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

    def fetch_thread(self, parent_id: int) -> list[Message]:
        ids = self.threads.get(f"thread:{parent_id}") or []
        out: list[Message] = []
        for mid in ids:
            d = self.msgs.get(f"msg:{mid}")
            if d:
                out.append(Message(**d))
        return out

    def fetch_mentions(self, user_id: int, limit: int = 100) -> list[Message]:
        ids = self.mentions.get(f"user_mentions:{user_id}") or []
        out: list[Message] = []
        for mid in reversed(ids):
            d = self.msgs.get(f"msg:{mid}")
            if d:
                out.append(Message(**d))
            if len(out) >= limit:
                break
        return out

    # ---- search -------------------------------------------------------

    def search(self, query: str, limit: int = 50) -> list[Message]:
        terms = self._tokenize(query)
        if not terms:
            return []
        # Intersect postings.
        posting_sets: list[set] = []
        for t in terms:
            ids = self.index.get(f"idx:{t}") or []
            posting_sets.append(set(ids))
        if not posting_sets:
            return []
        common = set.intersection(*posting_sets) if posting_sets else set()
        # Order by recency.
        scored: list[tuple[float, int]] = []
        for mid in common:
            d = self.msgs.get(f"msg:{mid}")
            if d:
                scored.append((d["ts"], mid))
        scored.sort(reverse=True)
        out: list[Message] = []
        for _ts, mid in scored:
            d = self.msgs.get(f"msg:{mid}")
            if d:
                out.append(Message(**d))
            if len(out) >= limit:
                break
        return out

    # ---- helpers ------------------------------------------------------

    def _tokenize(self, text: str) -> list[str]:
        text = text.lower()
        # split on non-alphanum, keep length>=2
        tokens = re.findall(r"[a-z0-9]{2,}", text)
        return tokens

    def stats(self) -> dict:
        return {
            "workspaces": self.workspaces.size(),
            "channels": self.channels.size(),
            "messages": self.msgs.size(),
            "index_entries": self.index.size(),
        }
