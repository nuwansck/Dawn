"""Telegram message templates for Dawn v1.1
AtomicFX-style: clean, state-change only, minimal noise.
"""
from __future__ import annotations

_DIV = "─" * 22


def _dir_icon(d: str) -> str:
    return "📈" if d == "BUY" else ("📉" if d == "SELL" else "")

def _session_icon(s: str) -> str:
    u = s.upper()
    if "LONDON" in u: return "🇬🇧"
    if "US" in u:     return "🗽"
    if "ASIAN" in u or "TOKYO" in u: return "🌏"
    if "EUROPEAN" in u: return "☀️"
    if "DEAD" in u:   return "✈️"
    return "📊"

def _pos_label(p: int) -> str:
    if p >= 30: return f"Full ${p}"
    if p >= 20: return f"Medium ${p}"
    if p >  0:  return f"Partial ${p}"
    return "No trade"

def _pnl_icon(v: float) -> str:
    return "🟢" if v > 0 else ("🔴" if v < 0 else "⬜")

def _mini_stats(s: dict) -> str:
    if s["count"] == 0: return "No closed trades"
    return f"{s['count']} trades  {s['wins']}W/{s['losses']}L  ${s['net_pnl']:+.2f}  WR {s['win_rate']:.0f}%"

def _split_banner(banner: str) -> tuple[str, str]:
    """Extract pair from banner.
    Handles both:
      '🇬🇧 LONDON [XAU/USD]'  → ('🇬🇧 LONDON [XAU/USD]', 'XAU/USD')
      'Dawn v1.1 | XAU/USD' → ('Dawn v1.1', 'XAU/USD')
    """
    if "[" in banner and "]" in banner:
        pair = banner[banner.index("[")+1 : banner.index("]")]
        return banner.strip(), pair.strip()
    if " | " in banner:
        bot, pair = banner.rsplit(" | ", 1)
        return bot.strip(), pair.strip("[]").strip()
    return banner.strip(), ""

def _ps(dp: int) -> float:
    return 10 ** -(dp - 1)

def _ascii_bar(v: float, mx: float, w: int = 10) -> str:
    if mx <= 0: return "░" * w
    f = int(round(v / mx * w))
    return "█" * f + "░" * (w - f)


# ── 1. Signal update ──────────────────────────────────────────────────────────

def msg_signal_update(
    banner, session, direction, score, position_usd, cpr_width_pct,
    detail_lines, news_penalty=0, raw_score=None, decision="WATCHING",
    reason="", mandatory_checks=None, quality_checks=None,
    execution_checks=None, cycle_minutes=5, signal_threshold=4,
    setup="", orb_age_min=None, orb_formed=False,
    h1_trend="UNKNOWN", h1_aligned=True, h1_filter_mode="soft",
    range_size=None,
) -> str:
    bot, pair = _split_banner(banner)
    s_str = f"{score}/6"
    if raw_score is not None and news_penalty:
        s_str += f" (raw {raw_score}, news {news_penalty:+d})"
    di    = _dir_icon(direction)
    nline = f"⚠️  News penalty: {news_penalty:+d}\n" if news_penalty else ""

    # Dawn v1.1: prefer range_size line if provided; fall back to CPR for Rogue compat.
    context_line = (
        f"Range size: {range_size:.2f} points"
        if range_size is not None
        else f"CPR: {cpr_width_pct:.2f}% width"
    )

    # H1 trend line — shows on all cards when filter is enabled
    def _h1_line():
        if h1_trend in ("UNKNOWN", "DISABLED"): return ""
        icon   = "🟢" if h1_trend == "BULLISH" else ("🔴" if h1_trend == "BEARISH" else "⬜")
        align  = "aligned" if h1_aligned else "counter-trend ⚠️"
        mode   = " [soft]" if h1_filter_mode == "soft" else ""
        return f"H1: {icon} {h1_trend}  ({align}){mode}\n"

    if decision == "WATCHING":
        return (
            f"{banner}\n{_DIV}\n"
            f"{pair}  {di} {direction}  Score {s_str}  👁 Watching\n"
            f"Reason: {reason or 'Watching for setup'}\n"
            f"{_h1_line()}"
            f"{nline}"
            f"{_DIV}\n"
            f"{context_line}\n"
            f"Next cycle in {cycle_minutes} min"
        )

    if decision == "BLOCKED":
        return (
            f"{banner}\n{_DIV}\n"
            f"{pair}  {di} {direction}  Score {s_str}  ❌ Blocked\n"
            f"Reason: {reason}\n"
            f"{_h1_line()}"
            f"{nline}"
            f"Next cycle in {cycle_minutes} min"
        )

    # READY
    spread = margin = ""
    if execution_checks:
        for lbl, ok, det in execution_checks:
            if "Spread" in lbl: spread = f"Spread: {det}  |  "
            elif "Margin" in lbl: margin = f"Margin: {det}\n"
    return (
        f"{banner}\n{_DIV}\n"
        f"{pair}  {di} {direction}  Score {s_str}  ✅ Ready\n"
        f"Window: {session}  |  {context_line}\n"
        f"{_h1_line()}"
        f"{nline}"
        f"{_DIV}\n"
        f"{spread}{margin}"
        f"Next cycle in {cycle_minutes} min"
    )


# ── 2. Trade opened ───────────────────────────────────────────────────────────

def msg_trade_opened(
    banner, direction, setup, session, fill_price, signal_price,
    sl_price, tp_price, sl_usd, tp_usd, units, position_usd,
    rr_ratio, cpr_width_pct, spread_pips, score, balance, demo,
    news_penalty=0, raw_score=None, free_margin=None,
    required_margin=None, requested_units=None, margin_mode="NORMAL", margin_usage_pct=None,
    price_dp=2, tp2_rr=3.0,
    h1_trend="UNKNOWN", h1_aligned=True,
    range_high=None, range_low=None, range_size=None, sl_raw_usd=None,
) -> str:
    bot, pair = _split_banner(banner)
    mode = "DEMO" if demo else "LIVE"
    di   = _dir_icon(direction)
    si   = _session_icon(session)
    s_str = f"{score}/6"
    if raw_score is not None and news_penalty:
        s_str += f" (raw {raw_score})"

    pip = _ps(price_dp)
    sl_p  = round(sl_usd / pip)
    tp_p  = round(tp_usd / pip)
    tp2_p = round(sl_usd * tp2_rr / pip)
    tp2_price = round(
        fill_price + sl_usd * tp2_rr if direction == "BUY"
        else fill_price - sl_usd * tp2_rr, price_dp
    )
    units_fmt = f"{units:,.1f}" if float(units) % 1 else f"{int(units):,}"
    requested_units = units if requested_units is None else requested_units
    margin_lines = ""
    if free_margin is not None or required_margin is not None or margin_mode not in (None, "NORMAL"):
        margin_lines += f"Margin:  {margin_mode or 'NORMAL'}"
        if required_margin is not None:
            margin_lines += f" | Req: ${float(required_margin):.2f}"
        if free_margin is not None:
            margin_lines += f" | Free: ${float(free_margin):.2f}"
        if margin_usage_pct is not None:
            margin_lines += f" | Use: {float(margin_usage_pct):.1f}%"
        margin_lines += "\n"
    if requested_units is not None and float(requested_units) != float(units):
        margin_lines += f"Units adjusted: {requested_units:g} → {units:g}\n"

    expected_sl = round(fill_price - sl_usd if direction == "BUY" else fill_price + sl_usd, price_dp)
    expected_tp = round(fill_price + tp_usd if direction == "BUY" else fill_price - tp_usd, price_dp)
    sl_ok = "✅" if abs(float(sl_price) - expected_sl) <= 0.05 else "⚠️"
    tp_ok = "✅" if abs(float(tp_price) - expected_tp) <= 0.05 else "⚠️"
    range_line = ""
    if range_low is not None and range_high is not None and range_size is not None:
        range_line = (
            f"Range:   {float(range_low):.{price_dp}f}–{float(range_high):.{price_dp}f} "
            f"(size ${float(range_size):.2f})\n"
        )
    sl_calc_line = ""
    if sl_raw_usd is not None:
        sl_calc_line = f"Raw SL:  ${float(sl_raw_usd):.2f}  → Final SL: ${float(sl_usd):.2f}\n"

    return (
        f"{banner}\n{_DIV}\n"
        f"{di} {direction} {pair} — {si} {session}\n"
        f"{_DIV}\n"
        f"◆ Entry:  {fill_price:.{price_dp}f}\n"
        f"{range_line}"
        f"{sl_calc_line}"
        f"TP dist: ${float(tp_usd):.2f}  |  RR: 1:{rr_ratio:.2f}\n"
        f"{_DIV}\n"
        f"Broker SL/TP check\n"
        f"  SL: {sl_price:.{price_dp}f}  expected {expected_sl:.{price_dp}f} {sl_ok}\n"
        f"  TP: {tp_price:.{price_dp}f}  expected {expected_tp:.{price_dp}f} {tp_ok}\n"
        f"{_DIV}\n"
        f"Setup:   {setup}\n"
        f"Score:   {s_str}  |  Spread: {spread_pips}p\n"
        + (f"H1:      {'🟢' if h1_aligned else '🔴'} {h1_trend}  ({'aligned' if h1_aligned else 'counter-trend ⚠️'})\n"
           if h1_trend not in ('UNKNOWN', 'DISABLED') else "")
        + margin_lines
        + f"Units:   {units_fmt}  |  Risk: {_pos_label(position_usd)}  |  Mode: {mode}"
    )


# ── 3. Breakeven ──────────────────────────────────────────────────────────────

def msg_breakeven(trade_id, direction, entry, trigger_price, trigger_dist,
                  current_price, unrealized_pnl, demo, price_dp=2) -> str:
    mode = "DEMO" if demo else "LIVE"
    return (
        f"🔒 Break-Even Activated\n{_DIV}\n"
        f"{direction}  Trade #{trade_id}\n"
        f"Entry:   {entry:.{price_dp}f}  →  SL moved to entry\n"
        f"Trigger: {trigger_price:.{price_dp}f}  (now: {current_price:.{price_dp}f})\n"
        f"PnL now: ${unrealized_pnl:+.2f}  |  Mode: {mode}"
    )


# ── 4. Trade closed ───────────────────────────────────────────────────────────

def msg_trade_closed(trade_id, direction, setup, entry, close_price,
                     pnl, session, demo, duration_str="", price_dp=5,
                     max_pips_reached=None) -> str:
    mode = "DEMO" if demo else "LIVE"
    di   = _dir_icon(direction)
    pip  = _ps(price_dp)
    pips = abs(close_price - entry) / pip

    if pnl > 0:
        outcome, pip_str = "TP ✅", f"+{pips:.0f} pips"
    elif pnl < 0:
        outcome, pip_str = "SL ✗",  f"-{pips:.0f} pips"
    else:
        outcome, pip_str = "BE ➡️", "0 pips"

    dur      = f"  |  {duration_str}" if duration_str else ""
    max_line = (f"Peak:    +{max_pips_reached:.1f} pips reached\n"
                if max_pips_reached is not None and max_pips_reached > 0 else "")
    return (
        f"{di} {direction} {outcome}\n{_DIV}\n"
        f"Entry:   {entry:.{price_dp}f}  →  Close: {close_price:.{price_dp}f}\n"
        f"Move:    {pip_str}\n"
        f"PnL:     ${pnl:+.2f}{dur}\n"
        f"{max_line}"
        f"Session: {session}  |  Mode: {mode}"
    )


# ── 5. News block ─────────────────────────────────────────────────────────────

def msg_news_block(event_name, event_time_sgt, before_min, after_min) -> str:
    return (
        f"📰 News Block\n{_DIV}\n"
        f"Event:  {event_name}\n"
        f"Time:   {event_time_sgt} SGT\n"
        f"Window: -{before_min}min → +{after_min}min\n"
        f"No new entries — resuming after event"
    )


# ── 6. News penalty ───────────────────────────────────────────────────────────

def msg_news_penalty(event_names, penalty, score_after, score_before,
                     position_after, position_before) -> str:
    names = ", ".join(event_names) if event_names else "Medium event"
    pos   = (f"${position_before} → ${position_after}"
             if position_before != position_after else f"${position_after} (unchanged)")
    status = "Trading with reduced size" if position_after > 0 else "Score below threshold — watching"
    return (
        f"📰 News Penalty\n{_DIV}\n"
        f"Event:    {names}\n"
        f"Score:    {score_before}/6 → {score_after}/6  (penalty {penalty:+d})\n"
        f"Position: {pos}\n"
        f"{status}"
    )


# ── 7. Cooldown ───────────────────────────────────────────────────────────────

def msg_cooldown_started(streak, cooldown_until_sgt, session_name="",
                         day_losses=0, day_limit=3) -> str:
    remaining = max(0, day_limit - day_losses)
    sline = f"Session: {session_name}\n" if session_name else ""
    return (
        f"🧊 Cooldown Started\n{_DIV}\n"
        f"Reason:  {streak} consecutive losses\n"
        f"{sline}"
        f"Resumes: {cooldown_until_sgt} SGT\n"
        f"Day:     {day_losses}/{day_limit} losses  ({remaining} remaining)"
    )


# ── 8. Daily cap ──────────────────────────────────────────────────────────────

def msg_daily_cap(cap_type, count, limit, window="", daily_pnl=None,
                  session_name="", last_loss_time_sgt="", reset_time_sgt="",
                  day_start_sgt="", day_end_sgt="", day_reset_sgt="") -> str:
    """Daily/window cap alert.

    v1.2.1 accepts legacy bot.py keyword names day_start_sgt/day_end_sgt/
    day_reset_sgt so cap alerts cannot crash the cycle when a safety stop fires.
    """
    if day_reset_sgt and not reset_time_sgt:
        reset_time_sgt = day_reset_sgt
    label  = ("Max losing trades" if cap_type == "losing_trades"
              else ("Max trades/day" if cap_type == "total_trades"
                    else ("Daily dollar loss stop" if cap_type == "daily_loss_usd" else f"{window} cap")))
    footer = "Resuming next trading day" if cap_type in ("losing_trades","total_trades","daily_loss_usd") else "Resuming next window"
    pline  = f"Day P&L: ${daily_pnl:+.2f}\n" if daily_pnl is not None else ""
    rline  = f"Resets:  {reset_time_sgt}\n"   if reset_time_sgt else ""
    wline  = f"Window:  {day_start_sgt} → {day_end_sgt} SGT\n" if day_start_sgt and day_end_sgt else ""
    return (
        f"🛑 Cap Reached\n{_DIV}\n"
        f"Type:  {label}\n"
        f"Count: {count}/{limit}\n"
        f"{pline}{wline}{rline}"
        f"{footer}"
    )


# ── 8b. New day ───────────────────────────────────────────────────────────────

def msg_new_day_resume(prev_day_pnl=None, prev_day_trades=0, london_open_sgt="16:00") -> str:
    prev = (f"Yesterday: {prev_day_trades} trade(s)  ${prev_day_pnl:+.2f}\n"
            if prev_day_trades > 0 and prev_day_pnl is not None else "")
    return (
        f"✅ New Trading Day\n{_DIV}\n"
        f"Daily limits reset\n"
        f"{prev}"
        f"Next session: London {london_open_sgt} SGT"
    )


# ── 8c. Session cap ───────────────────────────────────────────────────────────

def msg_session_cap(session_name=None, session_losses=None, session_limit=None,
                    day_losses=0, day_limit=0, next_session="", **kwargs) -> str:
    """Session cap alert with backward-compatible aliases.

    bot.py historically called this as msg_session_cap(session=..., count=..., limit=...).
    Accept both styles so safety-cap alerts never crash trading management.
    """
    session_name = session_name or kwargs.get("session") or "Session"
    session_losses = session_losses if session_losses is not None else kwargs.get("count", 0)
    session_limit = session_limit if session_limit is not None else kwargs.get("limit", 0)
    si  = _session_icon(session_name)
    ni  = _session_icon(next_session)
    rem = max(0, int(day_limit or 0) - int(day_losses or 0))
    return (
        f"🔶 Session Cap\n{_DIV}\n"
        f"{si} {session_name}: {session_losses}/{session_limit} losses  (paused)\n"
        f"Day: {day_losses}/{day_limit} losses  ({rem} remaining)\n"
        f"{_DIV}\n"
        f"Next: {ni} {next_session}"
    )


# ── 9. Session open ───────────────────────────────────────────────────────────

def msg_session_open(session_name, session_hours_sgt, trade_cap,
                     trades_today, daily_pnl) -> str:
    icon    = _session_icon(session_name)
    pnl_str = f"${daily_pnl:+.2f}" if trades_today > 0 else "—"
    return (
        f"{icon} {session_name} Open  {session_hours_sgt} SGT\n"
        f"{_DIV}\n"
        f"Today:  {trades_today} trade(s)  {pnl_str}  |  cap {trade_cap}\n"
        f"Scanning for CPR breakout setups..."
    )


# ── 10. Spread skip ───────────────────────────────────────────────────────────

def msg_spread_skip(banner, session_label, spread_pips, limit_pips) -> str:
    _, pair = _split_banner(banner)
    return (
        f"⚠️  Spread Too Wide\n{_DIV}\n"
        f"{pair}  |  {session_label}\n"
        f"Spread: {spread_pips}p  |  Limit: {limit_pips}p  (+{spread_pips - limit_pips} over)\n"
        f"Waiting for spread to normalise"
    )


# ── 11. Order failed ─────────────────────────────────────────────────────────

def msg_order_failed(direction, instrument, units, error,
                     free_margin=None, required_margin=None, retry_attempted=False) -> str:
    mline = (f"Margin: free=${free_margin:.2f}  req=${required_margin:.2f}\n"
             if free_margin is not None and required_margin is not None else "")
    return (
        f"❌ Order Failed\n{_DIV}\n"
        f"{direction}  {instrument}  {int(units):,} units\n"
        f"Error:  {error}\n"
        f"{mline}"
        f"Retry:  {'attempted' if retry_attempted else 'not attempted'}\n"
        f"Check OANDA account and logs"
    )


# ── 11b. Margin adjustment ────────────────────────────────────────────────────

def msg_margin_adjustment(instrument, requested_units, adjusted_units,
                          free_margin, required_margin, reason) -> str:
    action = "Skipping trade" if adjusted_units <= 0 else "Using smaller size"
    return (
        f"⚠️  Margin Protection\n{_DIV}\n"
        f"Pair:      {instrument}\n"
        f"Requested: {int(requested_units):,}\n"
        f"Adjusted:  {int(adjusted_units):,}\n"
        f"Free Mgn:  ${free_margin:.2f}\n"
        f"Req Mgn:   ${required_margin:.2f}\n"
        f"{_DIV}\n"
        f"{action}"
    )


# ── 12. Error ─────────────────────────────────────────────────────────────────

def msg_error(error_type, detail="") -> str:
    dline = f"Detail: {detail}\n" if detail else ""
    return f"❌ Error\n{_DIV}\n{error_type}\n{dline}Check logs"


# ── 13. Friday cutoff ─────────────────────────────────────────────────────────

def msg_friday_cutoff(cutoff_hour_sgt) -> str:
    return (
        f"📅 Friday Cutoff\n{_DIV}\n"
        f"After {cutoff_hour_sgt:02d}:00 SGT — no new entries\n"
        f"Resuming Monday 16:00 SGT"
    )


# ── 14. Startup ───────────────────────────────────────────────────────────────

def msg_startup(
    version, mode, balance, min_score, cycle_minutes=5,
    max_trades_london=1, max_trades_us=1, max_trades_tokyo=0,
    max_losing_day=2, trading_day_start_hour=8,
    us_early_end=3, dead_zone_start=4, dead_zone_end=7,
    tokyo_start=8, tokyo_end=15, london_start=15, london_end=16,
    us_start=20, us_end=22, max_total_open=1,
    position_full_usd=100, position_partial_usd=100, session_thresholds=None,
    tg_min_score=1, h1_filter_enabled=True, h1_filter_mode="hard",
    dry_run=False, daily_loss_limit_usd=150.0,
    dawn_range_min_usd=15.0, dawn_range_max_usd=80.0,
    dawn_sl_range_pct=0.50, dawn_tp_range_pct=1.00,
    sl_min_usd=15.0, sl_max_usd=35.0, max_rr_ratio=2.5,
) -> str:
    """Dawn startup message — session breakout flavour.

    Signature preserved from Rogue so scheduler.py can call it unchanged.
    Some parameters (dead_zone_*, tokyo_*, us_early_end, score tiers) are
    effectively unused for Dawn's two-window strategy but kept for compat.
    """
    h1_line = (
        f"H1 filter: {'✅' if h1_filter_enabled else '⬜'} "
        f"{h1_filter_mode.upper() if h1_filter_enabled else 'OFF'}\n"
    )
    dry = "ON 🧪" if dry_run else "OFF"
    daily_loss_line = "Disabled" if not daily_loss_limit_usd else f"${float(daily_loss_limit_usd):.0f}"
    return (
        f"🌅 {version} started\n{_DIV}\n"
        f"Mode:      {mode}  |  Dry run: {dry}  |  Balance: ${balance:,.2f}\n"
        f"Pair:      XAU/USD  |  Signal TF: M15  |  Trend TF: H1  |  Cycle: {cycle_minutes} min\n"
        f"Strategy:  Session Breakout + H1 Trend Filter\n"
        f"Entry:     First completed M15 close beyond prior range\n"
        f"Size:      ${position_full_usd} risk budget per trade\n"
        f"{h1_line}"
        f"{_DIV}\n"
        f"Entry windows (SGT)\n"
        f"  🇬🇧 15:00–16:30  London open  (range 07:00–15:00)\n"
        f"  🗽 20:30–22:00  NY open      (range 15:00–20:30)\n"
        f"{_DIV}\n"
        f"SL/TP logic\n"
        f"  Range: ${float(dawn_range_min_usd):.0f}–${float(dawn_range_max_usd):.0f}\n"
        f"  Raw SL: {float(dawn_sl_range_pct)*100:.0f}% × range\n"
        f"  Final SL clamp: ${float(sl_min_usd):.0f}–${float(sl_max_usd):.0f}\n"
        f"  TP: {float(dawn_tp_range_pct)*100:.0f}% × range  |  RR cap: 1:{float(max_rr_ratio):.1f}\n"
        f"{_DIV}\n"
        f"Safety: {max_losing_day} losses/day, {max_trades_london + max_trades_us} trades/day, "
        f"daily loss stop {daily_loss_line}\n"
        f"Global: {max_total_open} open  |  Reset: {trading_day_start_hour:02d}:00 SGT"
    )


# ── 15. Daily report ─────────────────────────────────────────────────────────

def msg_daily_report(
    day_label, day_stats, wtd_stats, mtd_stats, open_count, report_time,
    blocked_spread=0, blocked_news=0, blocked_signal=0,
    session_stats=None,
) -> str:
    # No trades today
    if day_stats["count"] == 0:
        oline = f"Open now: {open_count} position(s)\n" if open_count > 0 else ""
        return (
            f"📊 Daily Summary — {day_label}\n{_DIV}\n"
            f"No trades closed today\n"
            f"{_DIV}\n"
            f"Month-to-date\n  {_mini_stats(mtd_stats)}\n"
            f"{_DIV}\n"
            f"{oline}"
            f"Report: {report_time}"
        )

    icon  = _pnl_icon(day_stats["net_pnl"])
    oline = f"Open now: {open_count} position(s)\n" if open_count > 0 else ""
    parts = []
    if blocked_spread:  parts.append(f"{blocked_spread} spread")
    if blocked_news:    parts.append(f"{blocked_news} news")
    if blocked_signal:  parts.append(f"{blocked_signal} signal")
    bline = f"Blocked:  {', '.join(parts)}\n" if parts else ""

    best  = day_stats.get("best_trade")
    worst = day_stats.get("worst_trade")
    bst   = f"  Best:     ${best['pnl']:+.2f}  ({best['time']} SGT)\n"   if best  else ""
    wst   = f"  Worst:    ${worst['pnl']:+.2f}  ({worst['time']} SGT)\n" if worst else ""
    isl   = day_stats.get("instant_sl_count", 0)
    islline = f"  ⚡ Instant SL: {isl} trade(s) ≤5min\n" if isl > 0 else ""
    fire  = " 🔥" if day_stats.get("wins", 0) >= 3 else ""

    # Session breakdown (Tokyo / London / US)
    sess_block = ""
    if session_stats:
        sess_block = f"{_DIV}\nSession breakdown\n"
        for name, s in session_stats.items():
            pnl_str = f"${s['net_pnl']:+.2f}"
            result  = "✅" if s["net_pnl"] > 0 else ("❌" if s["net_pnl"] < 0 else "—")
            sess_block += f"  {name:<14} {s['count']}t  {pnl_str}  {result}\n"

    return (
        f"📊 Daily Summary — {day_label}\n"
        f"{sess_block}"
        f"{_DIV}\n"
        f"Day total\n"
        f"  Trades:   {day_stats['count']}  ({day_stats['wins']}W{fire} / {day_stats['losses']}L)\n"
        f"  Win rate: {day_stats['win_rate']:.0f}%\n"
        f"  Net P&L:  ${day_stats['net_pnl']:+.2f}  {icon}\n"
        f"{bst}{wst}{islline}{bline}"
        f"{_DIV}\n"
        f"Month-to-date\n  {_mini_stats(mtd_stats)}\n"
        f"{_DIV}\n"
        f"{oline}"
        f"Report: {report_time}"
    )


# ── 16. Weekly report ─────────────────────────────────────────────────────────

def msg_weekly_report(week_label, stats, sessions, setups, report_time, pairs=None) -> str:
    if stats["count"] == 0:
        return f"📅 Weekly Report — {week_label}\n{_DIV}\nNo closed trades.\nReport: {report_time}"

    icon   = _pnl_icon(stats["net_pnl"])
    pf_str = f"{stats['profit_factor']}" if stats["profit_factor"] is not None else "n/a"
    rline  = f"Avg R:       {stats['avg_r']}R\n" if stats.get("avg_r") is not None else ""
    bline  = (f"Best:        ${stats['best_trade']['pnl']:+.2f}  ({stats['best_trade']['time']} SGT)\n"
              if stats.get("best_trade") else "")
    wline  = (f"Worst:       ${stats['worst_trade']['pnl']:+.2f}  ({stats['worst_trade']['time']} SGT)\n"
              if stats.get("worst_trade") else "")

    def _sec(data):
        if not data: return ""
        mx = max(s["win_rate"] for s in data.values()) or 1
        return "".join(
            f"  {n:<10} {_ascii_bar(s['win_rate'],mx)} {s['win_rate']:>5.1f}%  ${s['net_pnl']:+.2f}  ({s['count']}t)\n"
            for n, s in data.items()
        )

    def _setup_sec(data):
        if not data: return ""
        mx = max(s["win_rate"] for s in data.values()) or 1
        return "".join(
            f"  {n[:18]:<18} {_ascii_bar(s['win_rate'],mx)} {s['win_rate']:>5.1f}%\n"
            for n, s in data.items()
        )

    pf, wr, n = stats["profit_factor"] or 0, stats["win_rate"], stats["count"]
    if n < 10:     verdict = f"⚠️ Small sample ({n} trades)"
    elif pf >= 1.3 and wr >= 48: verdict = f"✅ Healthy — PF {pf}  WR {wr}%"
    elif pf >= 1.0: verdict = f"🟡 Marginal — PF {pf}  WR {wr}%  Monitor"
    else:           verdict = f"🔴 Negative — PF {pf}  WR {wr}%  Review"

    return (
        f"📅 Weekly Report — {week_label}\n{_DIV}\n"
        f"{icon} Trades: {stats['count']}  ({stats['wins']}W / {stats['losses']}L)\n"
        f"Net P&L:     ${stats['net_pnl']:+.2f}\n"
        f"Win rate:    {wr}%\n"
        f"P.Factor:    {pf_str}\n"
        f"{rline}Streaks:     {stats['max_win_streak']}W / {stats['max_loss_streak']}L max\n"
        f"{bline}{wline}"
        f"{_DIV}\nBy Session\n{_sec(sessions)}"
        f"{_DIV}\nBy Pair\n{_sec(pairs) if pairs else ''}"
        f"{_DIV}\nBy Setup\n{_setup_sec(setups)}"
        f"{_DIV}\n{verdict}\nReport: {report_time}"
    )


# ── 17. Monthly report ────────────────────────────────────────────────────────

def msg_monthly_report(month_label, stats, sessions, setups, scores,
                       mom_delta, prior_month_pnl, report_time) -> str:
    if stats["count"] == 0:
        return f"📆 Monthly Report — {month_label}\n{_DIV}\nNo closed trades.\nReport: {report_time}"

    icon   = _pnl_icon(stats["net_pnl"])
    pf_str = f"{stats['profit_factor']}" if stats["profit_factor"] is not None else "n/a"
    rline  = f"Avg R:         {stats['avg_r']}R\n" if stats.get("avg_r") is not None else ""
    mline  = ""
    if mom_delta is not None and prior_month_pnl is not None:
        di    = "🟢" if mom_delta >= 0 else "🔴"
        mline = f"vs prior:      ${prior_month_pnl:+.2f}  →  {di} {mom_delta:+.2f}\n"
    bline  = (f"Best trade:    ${stats['best_trade']['pnl']:+.2f}  ({stats['best_trade']['time']} SGT)\n"
              if stats.get("best_trade") else "")
    wline  = (f"Worst trade:   ${stats['worst_trade']['pnl']:+.2f}  ({stats['worst_trade']['time']} SGT)\n"
              if stats.get("worst_trade") else "")

    def _sec(data, w=18):
        if not data: return ""
        mx = max(s["win_rate"] for s in data.values()) or 1
        return "".join(
            f"  {n[:w]:<{w}} {_ascii_bar(s['win_rate'],mx)} {s['win_rate']:>5.1f}%  ({s['count']}t)\n"
            for n, s in data.items()
        )

    pf, wr, n = stats["profit_factor"] or 0, stats["win_rate"], stats["count"]
    if n < 20:
        verdict, rec = f"⚠️ Small sample ({n} trades)", "Collect more data before any changes."
    elif pf >= 1.3 and wr >= 48:
        verdict, rec = f"✅ Healthy — PF {pf}  WR {wr}%", "System performing well. No changes needed."
    elif pf >= 1.0:
        verdict, rec = f"🟡 Marginal — PF {pf}  WR {wr}%", "Consider raising signal_threshold by +1."
    else:
        verdict, rec = f"🔴 Negative — PF {pf}  WR {wr}%", "Review session breakdown. Pause worst session."

    return (
        f"📆 Monthly Report — {month_label}\n{_DIV}\n"
        f"{icon} Trades: {stats['count']}  ({stats['wins']}W / {stats['losses']}L)\n"
        f"Net P&L:       ${stats['net_pnl']:+.2f}\n"
        f"{mline}"
        f"Win rate:      {wr}%\n"
        f"P.Factor:      {pf_str}\n"
        f"{rline}"
        f"Gross P:       ${stats['gross_profit']:.2f}\n"
        f"Gross L:       ${stats['gross_loss']:.2f}\n"
        f"Streaks:       {stats['max_win_streak']}W / {stats['max_loss_streak']}L max\n"
        f"{bline}{wline}"
        f"{_DIV}\nBy Session\n{_sec(sessions)}"
        f"{_DIV}\nBy Setup\n{_sec(setups)}"
        f"{_DIV}\nBy Score\n{_sec(scores, w=8)}"
        f"{_DIV}\n{verdict}\n💡 {rec}\nReport: {report_time}"
    )


# ── 18. Session performance report ──────────────────────────────────────────

def msg_session_report(
    session_name: str,       # "Asian", "London", "US"
    banner: str,             # e.g. "🌏 ASIAN"
    session_stats: dict,     # _stats() output for this session window
    report_time: str,        # e.g. "16:05 SGT"
    next_session: str = "",  # e.g. "London (16:00 SGT)"
) -> str:
    icon = _pnl_icon(session_stats["net_pnl"]) if session_stats["count"] > 0 else "📋"
    r_line    = f"  Avg R:    {session_stats['avg_r']}R\n" if session_stats.get("avg_r") is not None else ""
    pf_val    = session_stats.get("profit_factor")
    pf_line   = f"  P.Factor: {pf_val}\n" if pf_val is not None else ""
    best      = session_stats.get("best_trade")
    worst     = session_stats.get("worst_trade")
    best_line  = f"  Best:     ${best['pnl']:+.2f}  ({best['time']} SGT)\n"  if best  else ""
    worst_line = f"  Worst:    ${worst['pnl']:+.2f}  ({worst['time']} SGT)\n" if worst else ""
    next_line  = f"Next: {next_session}\n" if next_session else ""

    if session_stats["count"] == 0:
        body = f"  No trades this session\n"
    else:
        body = (
            f"  Trades:   {session_stats['count']}  ({session_stats['wins']}W / {session_stats['losses']}L)\n"
            f"  Net PnL:  ${session_stats['net_pnl']:+.2f}\n"
            f"{pf_line}"
            f"{r_line}"
            f"{best_line}"
            f"{worst_line}"
        )

    return (
        f"{icon} {session_name} Session\n{_DIV}\n"
        f"{banner}\n"
        f"{_DIV}\n"
        f"{body}"
        f"{_DIV}\n"
        f"{next_line}"
        f"Report: {report_time}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# 15. Weekly performance report  (Monday 08:15 SGT)
# ══════════════════════════════════════════════════════════════════════════════


# ── 19. Pyramid add opened ───────────────────────────────────────────────────

def msg_pyramid_opened(
    banner: str,
    direction: str,
    session: str,
    fill_price: float,
    signal_price: float,
    sl_price: float,
    tp_price: float,
    sl_usd: float,
    tp_usd: float,
    units: float,
    rr_ratio: float,
    spread_pips: int,
    score: int,
    t1_trade_id: str,
    t1_unrealized_pnl: float,
    pyramid_max_risk: int,
    demo: bool,
) -> str:
    slip     = fill_price - signal_price
    slip_str = f"  (slip ${slip:+.2f})" if abs(slip) > 0.005 else ""
    mode     = "DEMO" if demo else "LIVE"
    pnl_str  = f"+${t1_unrealized_pnl:.2f}" if t1_unrealized_pnl >= 0 else f"-${abs(t1_unrealized_pnl):.2f}"
    return (
        f"{banner} 🔺 Pyramid Add — {direction}\n{_DIV}\n"
        f"Trade 1:   #{t1_trade_id}  (open, {pnl_str})\n"
        f"Window:    {session}\n"
        f"Fill:      ${fill_price:.2f}{slip_str}\n"
        f"SL:        ${sl_price:.2f}  (-${sl_usd:.2f} tight)\n"
        f"TP:        ${tp_price:.2f}  (+${tp_usd:.2f})\n"
        f"Units:     {units}\n"
        f"Risk cap:  ${pyramid_max_risk}  (1:{rr_ratio:.0f})\n"
        f"Spread:    {spread_pips} pips\n"
        f"Score:     {score}/6\n"
        f"Mode:      {mode}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# 10b. Margin auto-scale / skip
# ══════════════════════════════════════════════════════════════════════════════
