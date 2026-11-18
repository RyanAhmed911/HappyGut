from datetime import date, timedelta

from happygut_engine import WeightEntry, valid_weight, weight_trend

TODAY = date(2026, 6, 30)


def series(*points: tuple[int, float]) -> list[WeightEntry]:
    """(days before today, kg) pairs."""
    return [WeightEntry(TODAY - timedelta(days=d), kg) for d, kg in points]


def test_no_entries_means_a_weigh_in_is_due():
    t = weight_trend([], TODAY)
    assert t.latest is None and t.due and t.loss is None and t.entries == 0


def test_stable_weight_has_no_warning_and_reports_changes():
    t = weight_trend(series((90, 60.0), (30, 59.6), (2, 59.8)), TODAY)
    assert t.loss is None and not t.due
    by_window = {c.days: c for c in t.changes}
    assert by_window[30].kg == 0.2 and by_window[90].kg == -0.2 and 180 not in by_window


def test_just_over_five_percent_in_six_months_is_notable():
    t = weight_trend(series((150, 60.0), (60, 58.5), (1, 56.9)), TODAY)  # 5.2% below the peak
    assert t.loss is not None and t.loss.level == "notable" and t.loss.window == "recent"
    assert t.loss.peak.kg == 60.0 and t.loss.kg == 3.1 and t.loss.percent == 5.2


def test_exactly_five_percent_is_not_flagged():
    # GLIM: "more than 5%"
    assert weight_trend(series((100, 60.0), (0, 57.0)), TODAY).loss is None


def test_more_than_ten_percent_in_six_months_is_larger():
    t = weight_trend(series((120, 70.0), (0, 62.0)), TODAY)
    assert t.loss.level == "larger" and t.loss.percent == 11.4


def test_loss_is_measured_from_the_peak_and_recovered_dips_do_not_count():
    rising_then_falling = series((170, 58.0), (90, 62.0), (0, 58.5))  # 5.6% below the 62 kg peak
    assert weight_trend(rising_then_falling, TODAY).loss.peak.kg == 62.0
    recovered = series((120, 60.0), (60, 56.0), (0, 59.8))  # the dip came back
    assert weight_trend(recovered, TODAY).loss is None


def test_slow_loss_over_a_year_needs_more_than_ten_percent():
    nine = series((300, 70.0), (0, 63.7))  # 9% over ~10 months: below the "beyond 6 months" threshold
    assert weight_trend(nine, TODAY).loss is None
    eleven = series((300, 70.0), (0, 62.2))
    loss = weight_trend(eleven, TODAY).loss
    assert loss.window == "long" and loss.level == "notable"


def test_a_weigh_in_is_due_after_a_week_and_future_entries_are_ignored():
    assert weight_trend(series((7, 60.0)), TODAY).due
    assert not weight_trend(series((6, 60.0)), TODAY).due
    future = [WeightEntry(TODAY + timedelta(days=3), 40.0), *series((2, 60.0))]
    t = weight_trend(future, TODAY)
    assert t.latest.kg == 60.0 and t.entries == 1


def test_plausible_range():
    assert valid_weight(55.5) and not valid_weight(5) and not valid_weight(400)
