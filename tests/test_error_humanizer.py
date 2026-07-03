from __future__ import annotations

from playlist_builder.ui.shared.error_humanizer import (
    humanize_engine_error,
    is_technical_error_message,
)


def test_is_technical_error_detects_python_unbound_local():
    message = "cannot access local variable 'ImportTrackStatus' where it is not associated with a value"
    assert is_technical_error_message(message)


def test_humanize_import_engine_error_masks_python_internals():
    raw = "cannot access local variable 'ImportTrackStatus' where it is not associated with a value"
    user_message, details = humanize_engine_error(raw, context="import_playlist")
    assert "ImportTrackStatus" not in user_message
    assert "importation a échoué" in user_message.lower()
    assert details == (("technical", raw),)


def test_humanize_preserves_user_facing_provider_message():
    raw = "Music.app n'est pas ouvert."
    user_message, details = humanize_engine_error(raw, context="import_playlist")
    assert user_message == raw
    assert details == ()
