"""Tests for the source adapters.

These tests do not touch the network. They check the parsing and the
filtering logic against recorded payloads, and they check the registry's
behaviour — which sources run, and what happens when one fails.
"""

from __future__ import annotations

from datetime import datetime, timezone

from tech_trend_radar.config import Settings
from tech_trend_radar.models import FetchResult, Post
from tech_trend_radar.sources import build_adapters
from tech_trend_radar.sources.base import BaseAdapter
from tech_trend_radar.sources.devto import DevToAdapter
from tech_trend_radar.sources.github import GitHubAdapter, build_query, repo_stem
from tech_trend_radar.sources.hackernews import HackerNewsAdapter
from tech_trend_radar.sources.reddit import RedditAdapter
from tech_trend_radar.sources.rss import RSSAdapter, YouTubeAdapter, _parse_date, _strip_html
from tech_trend_radar.sources.stackoverflow import StackOverflowAdapter


class FakeClient:
    """A client that returns canned responses instead of making requests."""

    def __init__(self, responses: dict | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[tuple[str, dict | None]] = []

    def get_json(self, url, params=None, headers=None):
        self.calls.append((url, params))
        for pattern, payload in self.responses.items():
            if pattern in url:
                return payload
        raise AssertionError(f"Unexpected URL: {url}")

    def get_text(self, url, headers=None):
        self.calls.append((url, None))
        for pattern, payload in self.responses.items():
            if pattern in url:
                return payload
        raise AssertionError(f"Unexpected URL: {url}")


class TestRegistry:
    def test_the_default_adapters_are_present(self):
        names = {a.name for a in build_adapters(Settings())}
        assert {"hackernews", "github", "stackoverflow", "devto", "youtube", "rss"} <= names

    def test_reddit_is_absent_without_credentials(self):
        names = {a.name for a in build_adapters(Settings())}
        assert "reddit" not in names

    def test_reddit_is_present_with_credentials(self):
        settings = Settings(reddit_client_id="id", reddit_client_secret="secret")
        names = {a.name for a in build_adapters(settings)}
        assert "reddit" in names

    def test_a_disabled_source_is_not_returned(self):
        settings = Settings(disabled_sources=("github",))
        names = {a.name for a in build_adapters(settings)}
        assert "github" not in names

    def test_reddit_reports_itself_as_unavailable_without_credentials(self):
        assert not RedditAdapter().available(Settings())
        assert RedditAdapter().available(Settings(reddit_client_id="a", reddit_client_secret="b"))


class TestErrorHandling:
    def test_a_failing_adapter_produces_a_failed_result_not_an_exception(self):
        class Failing(BaseAdapter):
            name = "failing"

            def fetch(self, client, settings):
                raise RuntimeError("boom")

        result = Failing().run(FakeClient(), Settings())
        assert not result.ok
        assert "boom" in result.error

    def test_a_successful_adapter_produces_an_ok_result(self):
        class Working(BaseAdapter):
            name = "working"

            def fetch(self, client, settings):
                return []

        result = Working().run(FakeClient(), Settings())
        assert result.ok
        assert result.error == ""

    def test_the_error_names_the_exception_type(self):
        class Failing(BaseAdapter):
            name = "failing"

            def fetch(self, client, settings):
                raise ValueError("nope")

        assert "ValueError" in Failing().run(FakeClient(), Settings()).error


class TestHackerNews:
    def test_a_front_page_story_becomes_a_post(self):
        client = FakeClient(
            {
                "topstories": [1, 2],
                "item/1": {
                    "id": 1,
                    "type": "story",
                    "title": "Rust 1.90 released",
                    "score": 100,
                    "descendants": 20,
                    "time": 1794700000,
                    "url": "https://example.invalid/1",
                    "by": "someone",
                },
                "item/2": {
                    "id": 2,
                    "type": "job",
                    "title": "We are hiring",
                    "score": 1,
                    "time": 1794700000,
                },
                "algolia": {"hits": []},
            }
        )
        posts = HackerNewsAdapter().fetch(client, Settings())
        titles = [p.title for p in posts]
        assert "Rust 1.90 released" in titles
        assert "We are hiring" not in titles

    def test_the_points_and_comments_become_the_engagement(self):
        client = FakeClient(
            {
                "topstories": [1],
                "item/1": {
                    "id": 1,
                    "type": "story",
                    "title": "A story",
                    "score": 100,
                    "descendants": 20,
                    "time": 1794700000,
                },
                "algolia": {"hits": []},
            }
        )
        posts = HackerNewsAdapter().fetch(client, Settings())
        front = next(p for p in posts if p.native_id == "1")
        assert front.extra["points"] == 100
        assert front.extra["comments"] == 20

    def test_a_story_without_a_title_is_skipped(self):
        client = FakeClient(
            {
                "topstories": [1],
                "item/1": {"id": 1, "type": "story", "title": "", "time": 1794700000},
                "algolia": {"hits": []},
            }
        )
        posts = HackerNewsAdapter().fetch(client, Settings())
        assert posts == []


class TestGitHub:
    def test_the_query_uses_an_absolute_date(self):
        query = build_query(datetime(2026, 11, 15, tzinfo=timezone.utc))
        assert "created:>2026-11-01" in query

    def test_the_query_has_no_relative_date(self):
        query = build_query()
        assert "days-ago" not in query

    def test_the_query_has_a_star_and_a_fork_floor(self):
        query = build_query()
        assert "stars:>" in query
        assert "forks:>" in query

    def test_a_star_farmed_repository_is_filtered_out(self):
        repos = [
            {
                "name": "StarFarm",
                "full_name": "a/StarFarm",
                "description": "spammy",
                "stargazers_count": 900,
                "forks_count": 3,
                "created_at": "2026-11-10T00:00:00Z",
                "topics": ["rust"],
                "owner": {"login": "a"},
            }
        ]
        kept = GitHubAdapter._prefilter(repos)
        assert kept == []

    def test_a_genuine_repository_survives_the_filter(self):
        repos = [
            {
                "name": "RealProject",
                "full_name": "a/RealProject",
                "description": "real",
                "stargazers_count": 900,
                "forks_count": 120,
                "created_at": "2026-11-10T00:00:00Z",
                "topics": ["rust"],
                "owner": {"login": "a"},
            }
        ]
        assert GitHubAdapter._prefilter(repos) == repos

    def test_the_same_name_under_many_owners_is_a_farm(self):
        repos = [
            {
                "name": "GitHub-Copilot-app",
                "full_name": f"owner{i}/GitHub-Copilot-app",
                "stargazers_count": 660,
                "forks_count": 200,
                "created_at": "2026-11-10T00:00:00Z",
                "owner": {"login": f"owner{i}"},
            }
            for i in range(5)
        ]
        assert GitHubAdapter._prefilter(repos) == []

    def test_one_repository_under_two_owners_survives(self):
        repos = [
            {
                "name": "Shared",
                "full_name": f"owner{i}/Shared",
                "stargazers_count": 60,
                "forks_count": 10,
                "created_at": "2026-11-10T00:00:00Z",
                "owner": {"login": f"owner{i}"},
            }
            for i in range(2)
        ]
        assert len(GitHubAdapter._prefilter(repos)) == 2

    def test_a_small_repository_skips_the_ratio_test(self):
        repos = [
            {
                "name": "Tiny",
                "full_name": "a/Tiny",
                "stargazers_count": 40,
                "forks_count": 0,
                "created_at": "2026-11-10T00:00:00Z",
                "owner": {"login": "a"},
            }
        ]
        assert GitHubAdapter._prefilter(repos) == repos

    def test_the_same_project_under_many_suffixes_is_filtered_out(self):
        # One project reposted under a different trailing word each time.
        # The exact names all differ, so the duplicate-name check misses it.
        repos = [
            {
                "name": f"blender-ai-copilot-{suffix}",
                "full_name": f"a{index}/blender-ai-copilot-{suffix}",
                "stargazers_count": 490 + index,
                "forks_count": 40,
                "created_at": "2026-11-10T00:00:00Z",
                "topics": ["blender"],
                "owner": {"login": f"a{index}"},
            }
            for index, suffix in enumerate(["studio", "forge", "flow", "assets"])
        ]
        assert GitHubAdapter._prefilter(repos) == []

    def test_one_repository_under_two_suffixes_survives(self):
        repos = [
            {
                "name": f"blender-ai-copilot-{suffix}",
                "full_name": f"a{index}/blender-ai-copilot-{suffix}",
                "stargazers_count": 490 + index,
                "forks_count": 40,
                "created_at": "2026-11-10T00:00:00Z",
                "topics": ["blender"],
                "owner": {"login": f"a{index}"},
            }
            for index, suffix in enumerate(["studio", "forge"])
        ]
        assert len(GitHubAdapter._prefilter(repos)) == 2

    def test_a_topic_stuffed_repository_is_filtered_out(self):
        # Twenty keyword-stuffed topics turn one repository into twenty
        # different "trends" for a topic-based aggregator.
        repos = [
            {
                "name": "Stuffed",
                "full_name": "a/Stuffed",
                "stargazers_count": 400,
                "forks_count": 90,
                "created_at": "2026-11-10T00:00:00Z",
                "topics": [f"topic-{index}" for index in range(20)],
                "owner": {"login": "a"},
            }
        ]
        assert GitHubAdapter._prefilter(repos) == []

    def test_a_repository_with_a_few_topics_survives(self):
        repos = [
            {
                "name": "Reasonable",
                "full_name": "a/Reasonable",
                "stargazers_count": 400,
                "forks_count": 90,
                "created_at": "2026-11-10T00:00:00Z",
                "topics": ["rust", "cli", "parser"],
                "owner": {"login": "a"},
            }
        ]
        assert GitHubAdapter._prefilter(repos) == repos

    def test_the_stem_drops_only_a_known_trailing_word(self):
        assert repo_stem("blender-ai-copilot-studio") == "blender-ai-copilot"
        assert repo_stem("Blender-AI-MCP-Studio") == "blender-ai-mcp"
        # A name with no filler suffix is left alone.
        assert repo_stem("real-project") == "real-project"
        # Only the trailing word is dropped, never a leading one.
        assert repo_stem("studio-real") == "studio-real"


class TestStackOverflow:
    def test_a_question_becomes_a_post(self):
        client = FakeClient(
            {
                "questions": {
                    "items": [
                        {
                            "question_id": 42,
                            "title": "How do I use Rust with Tokio?",
                            "score": 5,
                            "answer_count": 2,
                            "view_count": 100,
                            "creation_date": 1794700000,
                            "tags": ["rust", "tokio"],
                            "link": "https://example.invalid/q/42",
                        }
                    ]
                }
            }
        )
        posts = StackOverflowAdapter().fetch(client, Settings())
        assert len(posts) == 1
        assert posts[0].native_id == "42"
        assert "rust" in posts[0].tags

    def test_each_tag_is_queried_separately(self):
        client = FakeClient({"questions": {"items": []}})
        StackOverflowAdapter().fetch(client, Settings())
        # The same endpoint is called once per tag, with a different tag in
        # the parameters each time. A single request with all the tags
        # returns zero results — the API ANDs them.
        tags = [params["tagged"] for _, params in client.calls]
        assert len(tags) > 1
        assert len(set(tags)) == len(tags)


class TestDevTo:
    def test_an_article_becomes_a_post(self):
        client = FakeClient(
            {
                "articles": [
                    {
                        "id": 7,
                        "title": "Understanding Rust lifetimes",
                        "description": "A deep dive",
                        "public_reactions_count": 40,
                        "comments_count": 5,
                        "published_at": "2026-11-14T10:00:00Z",
                        "tag_list": ["rust", "programming"],
                        "url": "https://dev.to/a/b",
                        "user": {"name": "Author"},
                    }
                ]
            }
        )
        posts = DevToAdapter().fetch(client, Settings())
        assert len(posts) == 1
        assert posts[0].extra["reactions"] == 40
        assert posts[0].author == "Author"

    def test_the_tags_parameter_is_used_not_tag(self):
        client = FakeClient({"articles": []})
        DevToAdapter().fetch(client, Settings())
        _, params = client.calls[0]
        assert "tags" in params
        assert "tag" not in params


class TestRSS:
    RSS = """<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <title>Feed</title>
      <item>
        <title>Rust 1.90 is out</title>
        <link>https://example.invalid/1</link>
        <pubDate>Sat, 14 Nov 2026 10:00:00 GMT</pubDate>
        <description><![CDATA[<p>Some <b>markup</b> here</p>]]></description>
        <category>News</category>
      </item>
    </channel></rss>
    """

    ATOM = """<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:yt="http://www.youtube.com/xml/schemas/2015">
      <entry>
        <title>A video title</title>
        <link href="https://youtube.com/watch?v=abc"/>
        <published>2026-11-14T10:00:00+00:00</published>
        <yt:videoId>abc</yt:videoId>
        <yt:statistics views="1234"/>
      </entry>
    </feed>
    """

    def test_an_rss_item_becomes_a_post(self):
        client = FakeClient({"example.invalid/feed": self.RSS})
        posts = RSSAdapter(feeds={"example": "https://example.invalid/feed"}).fetch(
            client, Settings()
        )
        assert len(posts) == 1
        assert posts[0].title == "Rust 1.90 is out"
        assert posts[0].url == "https://example.invalid/1"

    def test_the_html_is_stripped_from_the_description(self):
        client = FakeClient({"example.invalid/feed": self.RSS})
        posts = RSSAdapter(feeds={"example": "https://example.invalid/feed"}).fetch(
            client, Settings()
        )
        assert "<" not in posts[0].description
        assert "markup" in posts[0].description

    def test_the_publisher_categories_are_kept_as_metadata_not_tags(self):
        client = FakeClient({"example.invalid/feed": self.RSS})
        posts = RSSAdapter(feeds={"example": "https://example.invalid/feed"}).fetch(
            client, Settings()
        )
        assert posts[0].extra["categories"] == ["News"]
        assert "news" not in posts[0].tags

    def test_an_atom_entry_becomes_a_post(self):
        client = FakeClient({"youtube.com/feeds": self.ATOM})
        posts = YouTubeAdapter(channels={"ch": "abc"}).fetch(client, Settings())
        assert len(posts) == 1
        assert posts[0].title == "A video title"
        assert posts[0].extra["views"] == 1234

    def test_one_bad_feed_does_not_stop_the_others(self):
        client = FakeClient({"good.invalid/feed": self.RSS})
        adapter = RSSAdapter(feeds={"good": "https://good.invalid/feed", "bad": "https://bad.invalid/feed"})
        # The fake raises AssertionError for the bad URL, which the adapter
        # catches per feed.
        posts = adapter.fetch(client, Settings())
        assert len(posts) == 1

    def test_malformed_xml_yields_no_posts(self):
        client = FakeClient({"bad.invalid/feed": "<not xml"})
        posts = RSSAdapter(feeds={"bad": "https://bad.invalid/feed"}).fetch(client, Settings())
        assert posts == []

    def test_the_date_parser_handles_rfc_822(self):
        parsed = _parse_date("Sat, 14 Nov 2026 10:00:00 GMT")
        assert parsed.year == 2026
        assert parsed.tzinfo is not None

    def test_the_date_parser_handles_iso(self):
        parsed = _parse_date("2026-11-14T10:00:00Z")
        assert parsed.year == 2026

    def test_a_missing_date_falls_back_to_now(self):
        assert _parse_date(None) is not None

    def test_the_html_stripper_removes_tags(self):
        assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"


class TestModelSerialisation:
    def test_a_post_round_trips(self):
        post = Post(
            platform="hackernews",
            native_id="1",
            title="A title",
            published=datetime(2026, 11, 15, tzinfo=timezone.utc),
            weight=1.5,
            raw_engagement=100.0,
            url="https://example.invalid",
            author="someone",
            tags=("rust",),
            description="desc",
        )
        restored = Post.from_dict(post.to_dict())
        assert restored.platform == post.platform
        assert restored.title == post.title
        assert restored.published == post.published
        assert restored.tags == post.tags

    def test_the_post_id_is_stable(self):
        post = Post(
            platform="hackernews",
            native_id="1",
            title="A",
            published=datetime.now(timezone.utc),
            weight=1.0,
        )
        assert post.id == post.id
        assert post.id != Post(
            platform="github",
            native_id="1",
            title="A",
            published=datetime.now(timezone.utc),
            weight=1.0,
        ).id

    def test_a_fetch_result_round_trips(self):
        result = FetchResult(
            platform="hackernews",
            posts=[],
            ok=True,
            fetched_at=datetime(2026, 11, 15, tzinfo=timezone.utc),
        )
        restored = FetchResult.from_dict(result.to_dict())
        assert restored.platform == result.platform
        assert restored.ok == result.ok
