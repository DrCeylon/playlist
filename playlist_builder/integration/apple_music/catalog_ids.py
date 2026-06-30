from __future__ import annotations

import re

from playlist_builder.canonical.models import CanonicalCandidate

_TRACK_ID_HINT_PREFIX = "itunes_track_id:"
_ITUNES_ID_IN_URL = re.compile(r"/(\d{6,})(?:\?|$)")
_ITUNES_TRACK_ID_IN_QUERY = re.compile(r"[?&]i=(\d+)")


def catalog_url_from_candidate(candidate: CanonicalCandidate) -> str:
    for hint in candidate.provider_hints:
        if hint.startswith(_TRACK_ID_HINT_PREFIX):
            continue
        if hint.startswith("http") or hint.startswith("music://"):
            return hint.strip()
    return ""


def catalog_track_id_from_candidate(candidate: CanonicalCandidate) -> str:
    for hint in candidate.provider_hints:
        if hint.startswith(_TRACK_ID_HINT_PREFIX):
            return hint.removeprefix(_TRACK_ID_HINT_PREFIX).strip()
    url = catalog_url_from_candidate(candidate)
    if not url:
        return ""
    query_match = _ITUNES_TRACK_ID_IN_QUERY.search(url)
    if query_match:
        return query_match.group(1)
    match = _ITUNES_ID_IN_URL.search(url)
    return match.group(1) if match else ""
