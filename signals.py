"""Signal engine for Dawn v1.1 — XAU/USD session open breakout.

Strategy: trade breakouts of the prior-session range during the first 90 minutes
after London open (15:00–16:30 SGT) and NY open (20:30–22:00 SGT). Binary
entry: first M15 candle that closes beyond the range high/low fires.

Windows (Asia/Singapore timezone, configurable via settings.json):
  London breakout:
    range:    07:00–15:00 SGT  (prior 8 hours — Asian session)
    entry:    15:00–16:30 SGT  (90-minute window after London open)
  NY breakout:
    range:    15:00–20:30 SGT  (prior 5.5 hours — London + pre-NY)
    entry:    20:30–22:00 SGT  (90-minute window after NY open)

Entry:
  BUY  when last completed M15 candle close > range high
  SELL when last completed M15 candle close < range low
  One trade per entry window (same-window guard enforced upstream)

Filters:
  1. Range size: must be in [dawn_range_min_usd, dawn_range_max_usd] (15–80)
     Small = noise; wide = already-volatile trap day.
  2. H1 EMA21 trend filter (reused from Rogue): BUY above, SELL below.
  3. Spread limit (upstream in bot.py, reused from settings.max_spread_pips).
  4. News blackout ±30 min (upstream, reused from Rogue's news_filter).
  5. Friday cutoff (upstream in bot.py).

SL / TP:
  SL = range_size × dawn_sl_range_pct (default 0.50) — clamped [sl_min_usd, sl_max_usd]
  TP = range_size × dawn_tp_range_pct (default 1.00) — realistic M15 target

Position size: fixed dawn_position_usd (default $100) per trade.
  units = position_usd / SL_usd

Return value matches Rogue interface so upstream bot.py works unchanged:
  (score, direction, details, levels, position_usd)
  score is binary: 0 (no signal/blocked) or 1 (fire trade).
"""

import time
import logging
from datetime import datetime

import pytz

from config_loader import load_secrets, load_settings
from oanda_trader import make_oanda_session

log = logging.getLogger(__name__)

SGT = pytz.timezone("Asia/Singapore")
UTC = pytz.UTC


# ── Default windows ──────────────────────────────────────────────────────────
# Each tuple: (name, range_start_h, range_end_h,
#              entry_start_h, entry_start_m, entry_end_h, entry_end_m)
# Overridable via settings["dawn_windows"] (list of dicts).
WINDOWS = [
    ("London",  7, 15,  15,  0, 16, 30),
    ("NY",     15, 20,  20, 30, 22,  0),
]


def position_usd_from_settings(settings=None) -> int:
    """Dawn uses flat fixed-$ sizing (no score-to-size mapping)."""
    return int((settings or {}).get("dawn_position_usd", 100))


# Back-compat shim for bot.py which may still import score_to_position_usd.
def score_to_position_usd(score: int, settings=None) -> int:
    return position_usd_from_settings(settings) if score >= 1 else 0


class SignalEngine:
    def __init__(self, demo: bool = True):
        secrets = load_secrets()
        self.api_key = secrets.get("OANDA_API_KEY", "")
        self.account_id = secrets.get("OANDA_ACCOUNT_ID", "")
        self.base_url = (
            "https://api-fxpractice.oanda.com" if demo else "https://api-fxtrade.oanda.com"
        )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.session = make_oanda_session(allowed_methods=["GET"])

    # ── Core analyze ──────────────────────────────────────────────────────────
    def analyze(self, asset: str = "XAUUSD", settings=None):
        """Run the Dawn breakout engine.

        Returns (score, direction, details, levels, position_usd).
          score:     0 (no trade) or 1 (fire)
          direction: "BUY" | "SELL" | "NONE"
          details:   reason string for Telegram/logs
          levels:    dict with range_high, range_low, range_size,
                     current_close, sl_usd_rec, tp_usd_rec, h1_ema, setup
          position_usd: $ risk for the trade, 0 if no trade
        """
        if settings is None:
            settings = load_settings()
        display = settings.get("instrument_display", "XAU/USD").replace("/", "")
        if asset not in ("XAUUSD", display):
            return 0, "NONE", f"Only {display} supported", {}, 0

        instrument = settings.get("instrument", "XAU_USD")
        now_sgt = datetime.now(SGT)

        # 1. Are we in an entry window?
        active = self._active_entry_window(now_sgt, settings)
        if active is None:
            return 0, "NONE", "Outside entry window — idle", {}, 0
        window_name, range_start_sgt, range_end_sgt, entry_end_sgt = active

        # 2. Fetch M15 candles (120 = ~30h coverage; plenty of margin)
        closes, highs, lows, times = self._fetch_candles_with_time(instrument, "M15", 120)
        if len(closes) < 20:
            return 0, "NONE", "Not enough M15 data", {}, 0

        # 3. Session range
        rh, rl, rc = self._session_range(highs, lows, times, range_start_sgt, range_end_sgt)
        if rh is None or rl is None or rc < 4:
            return 0, "NONE", (
                f"Insufficient {window_name} range data ({rc} candles)"
            ), {}, 0

        range_size = round(rh - rl, 2)
        current_close = closes[-1]

        levels = {
            "window_name":   window_name,
            "range_high":    round(rh, 2),
            "range_low":     round(rl, 2),
            "range_size":    range_size,
            "range_candles": rc,
            "current_close": round(current_close, 2),
            "range_start":   range_start_sgt.strftime("%H:%M SGT"),
            "range_end":     range_end_sgt.strftime("%H:%M SGT"),
        }
        log.info(
            "%s range | high=%.2f low=%.2f size=%.2f candles=%d",
            window_name, rh, rl, range_size, rc,
        )

        # 4. Range size sanity filters
        rmin = float(settings.get("dawn_range_min_usd", 15.0))
        rmax = float(settings.get("dawn_range_max_usd", 80.0))
        if range_size < rmin:
            return 0, "NONE", (
                f"{window_name} range too small ({range_size:.2f} < {rmin:.0f})"
            ), levels, 0
        if range_size > rmax:
            return 0, "NONE", (
                f"{window_name} range too large ({range_size:.2f} > {rmax:.0f}) — skip volatile day"
            ), levels, 0

        # 5. Breakout trigger — last completed M15 close beyond range
        direction = "NONE"
        setup = ""
        if current_close > rh:
            direction = "BUY"
            setup = f"{window_name} Range High Break"
        elif current_close < rl:
            direction = "SELL"
            setup = f"{window_name} Range Low Break"
        else:
            return 0, "NONE", (
                f"{window_name} waiting | close={current_close:.2f} "
                f"high={rh:.2f} low={rl:.2f}"
            ), levels, 0

        levels["setup"] = setup
        levels["direction"] = direction

        # 6. H1 EMA21 trend filter
        if settings.get("h1_trend_filter_enabled", True):
            h1_period = int(settings.get("h1_ema_period", 21))
            h1c, _, _, _ = self._fetch_candles_with_time(instrument, "H1", h1_period + 5)
            if len(h1c) >= h1_period:
                h1_ema = sum(h1c[-h1_period:]) / h1_period
                h1_price = h1c[-1]
                levels["h1_ema"] = round(h1_ema, 2)
                levels["h1_price"] = round(h1_price, 2)
                if direction == "BUY" and h1_price < h1_ema:
                    return 0, "NONE", (
                        f"{setup} — H1 trend BLOCKED BUY "
                        f"(H1 {h1_price:.2f} < EMA{h1_period} {h1_ema:.2f})"
                    ), levels, 0
                if direction == "SELL" and h1_price > h1_ema:
                    return 0, "NONE", (
                        f"{setup} — H1 trend BLOCKED SELL "
                        f"(H1 {h1_price:.2f} > EMA{h1_period} {h1_ema:.2f})"
                    ), levels, 0

        # 7. SL / TP from range
        sl_pct = float(settings.get("dawn_sl_range_pct", 0.50))
        tp_pct = float(settings.get("dawn_tp_range_pct", 1.00))
        sl_min = float(settings.get("sl_min_usd", 15.0))
        sl_max = float(settings.get("sl_max_usd", 35.0))

        sl_raw = range_size * sl_pct
        sl_usd = max(sl_min, min(sl_max, sl_raw))
        tp_usd = range_size * tp_pct

        levels["sl_raw_usd"] = round(sl_raw, 2)
        levels["sl_usd_rec"] = round(sl_usd, 2)
        levels["tp_usd_rec"] = round(tp_usd, 2)
        levels["rr_ratio"]   = round(tp_usd / sl_usd, 2) if sl_usd > 0 else 0

        # 8. Position
        position_usd = position_usd_from_settings(settings)
        levels["position_usd"] = position_usd
        levels["entry"] = round(current_close, 2)
        levels["score"] = 1

        parts = [
            f"🌅 {window_name} breakout",
            f"{setup} @ {current_close:.2f}",
            f"Range {rl:.2f}–{rh:.2f} (size {range_size:.2f})",
            f"SL ${sl_usd:.2f}  TP ${tp_usd:.2f}  RR 1:{levels['rr_ratio']:.1f}",
        ]
        if "h1_ema" in levels:
            parts.append(f"H1 EMA={levels['h1_ema']:.2f} ✓")
        details = " | ".join(parts)

        log.info(
            "Dawn FIRE | window=%s dir=%s | range=%.2f sl=%.2f tp=%.2f",
            window_name, direction, range_size, sl_usd, tp_usd,
        )
        return 1, direction, details, levels, position_usd

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _active_entry_window(self, now_sgt: datetime, settings: dict):
        cfg = settings.get("dawn_windows")
        if cfg and isinstance(cfg, list):
            windows = [(w["name"], w["range_start_h"], w["range_end_h"],
                        w["entry_start_h"], w["entry_start_m"],
                        w["entry_end_h"], w["entry_end_m"]) for w in cfg]
        else:
            windows = WINDOWS

        today = now_sgt.date()
        midnight = datetime.combine(today, datetime.min.time())
        for name, rs_h, _re_h, es_h, es_m, ee_h, ee_m in windows:
            entry_start = SGT.localize(midnight.replace(hour=es_h, minute=es_m))
            entry_end   = SGT.localize(midnight.replace(hour=ee_h, minute=ee_m))
            if entry_start <= now_sgt < entry_end:
                range_start = SGT.localize(midnight.replace(hour=rs_h, minute=0))
                # Range ends at entry_start (session open)
                return name, range_start, entry_start, entry_end
        return None

    def _session_range(self, highs, lows, times_utc, range_start_sgt, range_end_sgt):
        """High/low of candles whose OPEN time is in [start, end) SGT."""
        rh = -1e18
        rl = 1e18
        count = 0
        for i, t_str in enumerate(times_utc):
            if not t_str:
                continue
            try:
                t_clean = t_str.replace("Z", "+00:00")
                # Trim nanosecond-precision fractions to microsecond for fromisoformat
                if "." in t_clean:
                    head, _, tail = t_clean.partition(".")
                    frac, _, tzp = tail.partition("+")
                    frac = frac[:6]
                    t_clean = f"{head}.{frac}+{tzp}" if tzp else f"{head}.{frac}"
                t_utc = datetime.fromisoformat(t_clean)
                if t_utc.tzinfo is None:
                    t_utc = UTC.localize(t_utc)
            except Exception:
                continue
            t_sgt = t_utc.astimezone(SGT)
            if range_start_sgt <= t_sgt < range_end_sgt:
                if highs[i] > rh:
                    rh = highs[i]
                if lows[i] < rl:
                    rl = lows[i]
                count += 1
        if count == 0:
            return None, None, 0
        return rh, rl, count

    def _fetch_candles(self, instrument: str, granularity: str, count: int = 60):
        closes, highs, lows, _ = self._fetch_candles_with_time(instrument, granularity, count)
        return closes, highs, lows

    def _fetch_candles_with_time(self, instrument: str, granularity: str, count: int = 60):
        url = f"{self.base_url}/v3/instruments/{instrument}/candles"
        params = {"count": str(count), "granularity": granularity, "price": "M"}
        for attempt in range(3):
            try:
                r = self.session.get(url, headers=self.headers, params=params, timeout=15)
                if r.status_code == 200:
                    candles = r.json().get("candles", [])
                    complete = [c for c in candles if c.get("complete")]
                    closes = [float(c["mid"]["c"]) for c in complete]
                    highs  = [float(c["mid"]["h"]) for c in complete]
                    lows   = [float(c["mid"]["l"]) for c in complete]
                    times  = [c.get("time", "") for c in complete]
                    return closes, highs, lows, times
                log.warning("Fetch candles %s %s: HTTP %s", instrument, granularity, r.status_code)
            except Exception as e:
                log.warning(
                    "Fetch candles error (%s %s) attempt %s: %s",
                    instrument, granularity, attempt + 1, e,
                )
            time.sleep(1)
        return [], [], [], []

    def _atr(self, highs, lows, closes, period=14):
        n = len(closes)
        if n < period + 2 or len(highs) < n or len(lows) < n:
            return None
        trs = [
            max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
            for i in range(1, n)
        ]
        atr = sum(trs[:period]) / period
        for tr in trs[period:]:
            atr = (atr * (period - 1) + tr) / period
        return atr
