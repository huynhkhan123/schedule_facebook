from urllib.parse import unquote, urlparse, urlunparse

FACEBOOK_GROUP_HOSTS = frozenset({"facebook.com", "www.facebook.com", "m.facebook.com"})
FACEBOOK_GROUP_RESERVED_SLUGS = frozenset(
    {
        "categories",
        "category",
        "create",
        "discover",
        "feed",
        "joins",
        "notifications",
        "suggestions",
    }
)


def normalize_facebook_group_url(raw_url: str) -> str | None:
    parsed = urlparse(raw_url.strip())
    if parsed.scheme or parsed.netloc:
        if parsed.scheme not in {"http", "https"}:
            return None
        if parsed.netloc.lower() not in FACEBOOK_GROUP_HOSTS:
            return None

    path_parts = [part for part in parsed.path.split("/") if part]
    try:
        groups_index = path_parts.index("groups")
    except ValueError:
        return None

    if groups_index + 1 >= len(path_parts):
        return None

    slug = path_parts[groups_index + 1].strip()
    decoded_slug = unquote(slug).strip().lower()
    if not decoded_slug or decoded_slug in FACEBOOK_GROUP_RESERVED_SLUGS:
        return None

    return urlunparse(("https", "www.facebook.com", f"/groups/{slug}", "", "", ""))


def is_facebook_group_url(raw_url: str) -> bool:
    return normalize_facebook_group_url(raw_url) is not None
