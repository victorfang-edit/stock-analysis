import pandas as pd

from analyze import drawdown, metrics, rsi


def test_max_drawdown():
    s = pd.Series([100, 120, 60, 90])
    assert abs(drawdown(s).min() - (-0.5)) < 1e-9  # 120 -> 60 is -50%


def test_rsi_rising_series_is_100():
    s = pd.Series(range(1, 60), dtype=float)
    assert rsi(s).iloc[-1] > 99.9


def test_beta_of_benchmark_is_one():
    s = pd.Series([100, 101, 99, 103, 104, 102, 106], index=pd.date_range("2024-01-01", periods=7))
    m = metrics(s, s.pct_change().dropna())
    assert abs(m["Beta vs bench"] - 1) < 1e-9
    assert abs(m["Total return"] - 0.06) < 1e-9


if __name__ == "__main__":
    test_max_drawdown(); test_rsi_rising_series_is_100(); test_beta_of_benchmark_is_one()
    print("all tests passed")
