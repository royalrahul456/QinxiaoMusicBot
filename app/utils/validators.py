from urllib.parse import urlparse

ALLOWED_MUSIC_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "spotify.com",
    "open.spotify.com",
    "soundcloud.com",
    "www.soundcloud.com",
    "m.soundcloud.com",
    "on.soundcloud.com",
}


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url.strip())
        return all([result.scheme in ("http", "https"), result.hostname])
    except Exception:
        return False


def is_allowed_music_url(url: str) -> bool:
    if not is_valid_url(url):
        return False
    hostname = (urlparse(url.strip()).hostname or "").lower()
    return hostname in ALLOWED_MUSIC_DOMAINS


def get_url_provider_type(url: str) -> str:
    if not is_allowed_music_url(url):
        return "search"
    hostname = (urlparse(url.strip()).hostname or "").lower()
    if hostname in ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"):
        return "youtube"
    elif hostname in ("spotify.com", "open.spotify.com"):
        return "spotify"
    elif hostname in ("soundcloud.com", "www.soundcloud.com", "m.soundcloud.com", "on.soundcloud.com"):
        return "soundcloud"
    return "search"

