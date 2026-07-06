from __future__ import annotations

import re

from playlist_builder.infrastructure import manual_continue_trace as trace


def test_manual_continue_trace_emits_timestamped_lines(capsys) -> None:
    trace.begin_session("session-trace-test")
    trace.log("ENTER test_step")
    trace.log("RETURN test_step")

    captured = capsys.readouterr().err
    lines = [line for line in captured.splitlines() if line.startswith("manual-continue-trace:")]
    assert len(lines) == 3
    assert all("[session=session-trace-test]" in line for line in lines)
    assert re.search(r"\[\d{2}:\d{2}:\d{2}\.\d{3}\]", lines[0])
    assert "(+" in lines[1] or "(+" in lines[2]
