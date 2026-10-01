def test_video_id_and_required_fields():
    import research.phase30_3_bear_put_source_resolution as mod

    assert mod.VIDEO_ID == "IpCuGEDxF1k"
    required = {
        "structure",
        "entry",
        "entry_timing",
        "strike_selection",
        "premium_debit_credit",
        "adjustment",
        "adjustment_timing",
        "stop_loss",
        "profit_target",
        "exit",
        "days_to_expiry",
        "lot_ratio",
        "no_trade",
        "holding_period",
        "capital_margin",
    }
    assert required.issubset(set(mod.PATTERNS))
