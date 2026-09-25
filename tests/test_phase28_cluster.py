from research.phase28_cluster import norm, similarity, cluster

def test_norm():
    assert norm("Iron Fly!!!") == "iron fly"

def test_similarity_identical():
    a = {"title": "Iron Fly Strategy", "candidate_payoff_family": "iron_fly", "video_id": "a"}
    b = {"title": "Iron Fly Strategy", "candidate_payoff_family": "iron_fly", "video_id": "b"}
    assert similarity(a, b) == 1.0

def test_cluster_never_allows_backtest():
    rows = [
        {"video_id": "a", "title": "Weekly IronFly", "candidate_payoff_family": "iron_fly", "webpage_url": ""},
        {"video_id": "b", "title": "Weekly IronFly", "candidate_payoff_family": "iron_fly", "webpage_url": ""},
    ]
    result = cluster(rows)
    assert len({r["family_id"] for r in result}) == 1
    assert all(r["backtest_allowed"] == "NO" for r in result)
