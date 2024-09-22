import nielsen.fetcher


def test_strip_tags() -> None:
    """Should strip HTML tags from the given input."""

    summary: str = """\u003cp\u003eJason Sudeikis plays Ted Lasso, a small-time
        college football coach from Kansas hired to coach a professional soccer team
        in England, despite having no experience coaching soccer.\u003c/p\u003e"""

    stripped: str = """Jason Sudeikis plays Ted Lasso, a small-time
        college football coach from Kansas hired to coach a professional soccer team
        in England, despite having no experience coaching soccer."""

    assert nielsen.fetcher.strip_tags(summary) == stripped
