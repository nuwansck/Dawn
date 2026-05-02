# Dawn v1.4 FINAL

Automated OANDA DEMO bot for XAU/USD session breakouts.

## Strategy

- Instrument: XAU/USD (`XAU_USD`)
- Signal timeframe: M15
- Trend filter: H1 EMA21 hard filter
- Entry: first completed M15 candle close beyond the prior session range
- London window: 15:00-16:30 SGT, range 07:00-15:00 SGT
- NY window: 20:30-22:00 SGT, range 15:00-20:30 SGT

## SL/TP

- Range filter: $15-$80
- SL: 50% x range, clamped to $15-$35
- TP: 100% x range
- RR cap: 1:2.5

## Safety

- OANDA mode: DEMO
- Max open trades: 1
- Max trades/day: 2
- Max losing trades/day: 2
- Daily loss stop: $150
- News blackout: 30 minutes before/after high-impact USD/gold news
- Friday cutoff: 22:00 SGT

## Deploy

Use the included `Procfile`, `railway.json`, and `requirements.txt`. Configure secrets using environment variables:

- `OANDA_API_KEY`
- `OANDA_ACCOUNT_ID`
- `TELEGRAM_TOKEN`
- `TELEGRAM_CHAT_ID`

Do not commit `secrets.json`.
