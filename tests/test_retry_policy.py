from playlist_builder.catalog.retry_policy import RetryPolicy


def test_minimum_delay_is_incremental_and_capped():
    policy = RetryPolicy(base_min_delay=2, increment=3, max_min_delay=10)
    assert policy.minimum_delay_for_attempt(1) == 2
    assert policy.minimum_delay_for_attempt(2) == 5
    assert policy.minimum_delay_for_attempt(3) == 8
    assert policy.minimum_delay_for_attempt(4) == 10
    assert policy.minimum_delay_for_attempt(99) == 10
