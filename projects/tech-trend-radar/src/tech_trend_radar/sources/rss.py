"""RSS and Atom feeds, parsed with the standard library.

`xml.etree.ElementTree` handles both formats. Adding a feedparser dependency
would mean touching the network for something the stdlib already does, and
the project has a rule: no dependency unless it buys something.

Two feed shapes are handled here:

* **RSS 2.0** — `<rss><channel><item>` with `<title>`, `<link>`, `<pubDate>`.
  This is what TechCrunch, The Verge and arXiv serve.
* **Atom** — `<feed><entry>` with `<title>`, `<link href>`, `<published>`.
  This is what YouTube serves.

RSS carries no engagement counter. Weight comes from *recency* instead: a
feed is a broadcast, so how recently it published is the only signal it has.
That is honest rather than a fudge — the cross-platform corroboration bonus
is where RSS topics earn their strength.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from ..config import DEFAULT_RSS_FEEDS, DEFAULT_YOUTUBE_CHANNELS, Settings
from ..http import HttpClient
from ..models import Post
from .base import BaseAdapter

ATOM_NS = "http://www.w3.org/2005/Atom"
YT_NS = "http://www.youtube.com/xml/schemas/2015"
YOUTUBE_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def _parse_date(value: str | None) -> datetime:
    """Parse the date formats the feeds in play actually use."""
    if not value:
        return datetime.now(timezone.utc)

    # RFC 822, as RSS 2.0 uses.
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        pass

    # ISO-8601, as Atom uses.
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def _strip_html(text: str) -> str:
    """Feed descriptions carry markup; the topic extractor wants plain text."""
    import re

    without_tags = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", without_tags).strip()


class RSSAdapter(BaseAdapter):
    """Generic RSS/Atom feeds, one Post per item."""

    name = "rss"

    def __init__(self, feeds: dict[str, str] | None = None) -> None:
        self.feeds = dict(feeds) if feeds is not None else dict(DEFAULT_RSS_FEEDS)
        #: Every feed this adapter knows about. The feed name is the source
        #: identity, so it is excluded from the topic vocabulary.
        self.source_markers = frozenset(self.feeds) | {"rss"}

    def fetch(self, client: HttpClient, settings: Settings) -> list[Post]:
        feeds = {**self.feeds, **settings.extra_feeds}
        posts: list[Post] = []

        for feed_name, url in feeds.items():
            try:
                xml = client.get_text(url)
            except Exception:  # noqa: BLE001 - one bad feed must not stop the others
                continue
            posts.extend(self._parse_feed(feed_name, xml, settings))
        return posts

    def _parse_feed(self, feed_name: str, xml: str, settings: Settings) -> list[Post]:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return []

        tag = root.tag.split("}")[-1]
        if tag == "rss":
            items = root.findall("./channel/item")
        elif tag == "feed":
            items = root.findall(f"{{{ATOM_NS}}}entry")
        else:
            return []

        weight = settings.platform_weight(self.name)
        posts: list[Post] = []

        for item in items[: settings.limit]:
            title = _child_text(item, "title")
            if not title:
                continue

            link = _child_text(item, "link")
            if not link:
                link_node = item.find(f"{{{ATOM_NS}}}link")
                if link_node is not None:
                    link = link_node.get("href", "")

            published = _parse_date(
                _child_text(item, "pubDate") or _child_text(item, "published")
            )
            description = _strip_html(
                _child_text(item, "description") or _child_text(item, "summary") or ""
            )
            categories = tuple(
                (node.text or "").strip()
                for node in item.findall("category")
                if (node.text or "").strip()
            )
            # RSS `<category>` values are the publisher's editorial
            # sections — "In Brief", "Transportation", "Gear" — not
            # technologies. They are kept on the post as metadata but are
            # not offered as topic tags, because a publisher's section
            # structure is not a statement about what technology is being
            # discussed.
            topic_tags = (feed_name,)

            # No engagement counter exists on a feed, so recency carries the
            # weight: a post published inside the recent window counts fully,
            # and the weight decays as the item ages into the baseline window.
            age_hours = (datetime.now(timezone.utc) - published).total_seconds() / 3600
            recency = 1.0 if age_hours <= settings.recent_window_hours else 0.35

            posts.append(
                Post(
                    platform=self.name,
                    native_id=f"{feed_name}:{_child_text(item, 'guid') or link or title}",
                    title=title.strip(),
                    published=published,
                    weight=weight * recency,
                    raw_engagement=recency,
                    url=link,
                    tags=topic_tags,
                    description=description,
                    extra={
                        "feed": feed_name,
                        "age_hours": round(age_hours, 2),
                        "categories": list(categories),
                    },
                )
            )
        return posts


class YouTubeAdapter(BaseAdapter):
    """YouTube channel feeds, parsed as Atom."""

    name = "youtube"

    def __init__(self, channels: dict[str, str] | None = None) -> None:
        self.channels = (
            dict(channels) if channels is not None else dict(DEFAULT_YOUTUBE_CHANNELS)
        )
        self.source_markers = frozenset(self.channels) | {"youtube"}

    def fetch(self, client: HttpClient, settings: Settings) -> list[Post]:
        weight = settings.platform_weight(self.name)
        posts: list[Post] = []

        for channel_name, channel_id in self.channels.items():
            try:
                xml = client.get_text(YOUTUBE_FEED.format(channel_id=channel_id))
            except Exception:  # noqa: BLE001
                continue

            try:
                root = ET.fromstring(xml)
            except ET.ParseError:
                continue

            for entry in root.findall(f"{{{ATOM_NS}}}entry")[: settings.limit]:
                title_node = entry.find(f"{{{ATOM_NS}}}title")
                title = (title_node.text or "").strip() if title_node is not None else ""
                if not title:
                    continue

                video_id = ""
                for node in entry.findall(f"{{{YT_NS}}}videoId"):
                    video_id = node.text or ""
                    break

                published = _parse_date(_child_text(entry, "published"))
                views_node = entry.find(f"{{{YT_NS}}}statistics")
                views = int(views_node.get("views", 0)) if views_node is not None else 0

                age_hours = (datetime.now(timezone.utc) - published).total_seconds() / 3600
                recency = 1.0 if age_hours <= settings.recent_window_hours else 0.35
                raw = float(views) if views else recency * 100

                posts.append(
                    Post(
                        platform=self.name,
                        native_id=video_id or f"{channel_name}:{title}",
                        title=title,
                        published=published,
                        weight=weight * recency,
                        raw_engagement=raw,
                        url=_child_text(entry, "link"),
                        author=_child_text(entry, "author"),
                        tags=("youtube", channel_name),
                        description=_strip_html(_child_text(entry, "summary")),
                        extra={"channel": channel_name, "views": views},
                    )
                )
        return posts


def _child_text(node: ET.Element, name: str) -> str:
    """Find a child by local name, ignoring the namespace.

    Feeds in the wild mix default and prefixed namespaces in ways that make
    a fully-qualified lookup brittle; matching on the local name is what
    every feed parser effectively does.
    """
    for child in node:
        if child.tag.split("}")[-1] == name:
            return (child.text or "").strip()
    return ""
