"""Tests for the SMB content recycler's parse function.

We don't hit the OpenAI API in tests — we test parse_posts() against
a fixed string of AI output. The test for the full recycle() flow
would require a network call and a paid API key; that's manual.
"""
import sys
from pathlib import Path

# Allow `import recycler` when running from the tests/ dir
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from recycler import parse_posts


SAMPLE_OUTPUT = """\
1. [LinkedIn] Stop wasting 3 hours every Saturday writing social posts.
Here's the 7-day workflow that turns 1 newsletter into 30 posts.
Save 3 hours a week, every week, forever.
What's the longest you've spent on a single social post?

2. [LinkedIn] 5 prompts. 1 hour per day. 7 days.
That's the whole workflow.
The wrong choice is the Saturday binge. The right choice is the daily
1-hour compounding.
Which workflow would you automate first?

3. [Facebook] If you write 1 newsletter a week and need 30 social posts
to promote it, this is for you.
The AI does the boring part. You do the editing.
Tag a friend who needs this.

4. [Instagram] [VISUAL: a 7-day calendar with 1 hour per day]
Caption: From 1 newsletter to 30 social posts in 7 days.
The 5 prompts. The 1-page SOP. The 1-hour-per-day ramp.
Save 3 hours a week, every week.
#ContentMarketing #SmallBusiness #SaveTime #MarketingTips
DM "WORKFLOW" for the free SOP.

5. [Twitter/X] 1/ I've been writing social posts the wrong way for
years.
---
2/ Then I tried a 7-day workflow: 5 prompts, 1 hour/day, 30 posts.
---
3/ The wrong choice is the Saturday binge.
---
4/ The right choice is the daily 1-hour compounding.
---
5/ If this was useful, RT the first tweet."""


def test_parse_posts_extracts_30_posts_when_present():
    """If the AI returns 30 posts, we extract all 30."""
    # Build a 30-post input by repeating the sample
    raw = SAMPLE_OUTPUT + "\n\n" + "\n\n".join(
        f"{i}. [{plat}] Post {i} body\nMore body"
        for i in range(6, 31)
        for plat in (["LinkedIn", "Facebook", "Instagram"][i % 3],)
    )
    posts = parse_posts(raw)
    assert len(posts) == 30, f"expected 30 posts, got {len(posts)}"
    # The first post should be LinkedIn
    platform, n, text = posts[0]
    assert platform == "LinkedIn", f"post 1 should be LinkedIn, got {platform}"
    assert n == 1
    assert "Stop wasting 3 hours" in text
    print(f"  ✓ parsed 30 posts; first platform={platform}, n={n}")


def test_parse_posts_extracts_platform_tag():
    """Each post's platform is the tag in [brackets] after the number."""
    posts = parse_posts(SAMPLE_OUTPUT)
    platforms = [p[0] for p in posts]
    assert "LinkedIn" in platforms, "LinkedIn should appear"
    assert "Facebook" in platforms, "Facebook should appear"
    assert "Instagram" in platforms, "Instagram should appear"
    print(f"  ✓ platforms extracted: {set(platforms)}")


def test_parse_posts_keeps_multiline_body():
    """The body + CTA on subsequent lines should be in the text."""
    posts = parse_posts(SAMPLE_OUTPUT)
    # Post 1 (LinkedIn) has a body with 2 lines after the hook
    _, _, text1 = posts[0]
    assert "Stop wasting 3 hours" in text1
    assert "Here's the 7-day workflow" in text1
    assert "Save 3 hours a week" in text1
    assert "What's the longest" in text1
    print("  ✓ multiline body preserved")


def test_parse_posts_handles_garbage_input():
    """If the AI returns garbage, parse_posts returns an empty list (no crash)."""
    posts = parse_posts("hello world\nthis is not a post")
    assert posts == [], f"expected empty list, got {posts}"
    posts = parse_posts("")
    assert posts == []
    print("  ✓ garbage input returns empty list, no crash")


def test_parse_posts_handles_partial_output():
    """If the AI returns only 5 posts, we get 5 (not 30)."""
    posts = parse_posts(SAMPLE_OUTPUT)
    # SAMPLE_OUTPUT has 5 posts in 3 formats
    assert len(posts) == 5, f"expected 5 posts in sample, got {len(posts)}"
    print(f"  ✓ partial output: got {len(posts)} posts")


if __name__ == "__main__":
    print("═══ recycler.parse_posts: meaningful workload ═══\n")
    test_parse_posts_extracts_30_posts_when_present()
    test_parse_posts_extracts_platform_tag()
    test_parse_posts_keeps_multiline_body()
    test_parse_posts_handles_garbage_input()
    test_parse_posts_handles_partial_output()
    print("\n═══ all 5 tests passed ═══")
