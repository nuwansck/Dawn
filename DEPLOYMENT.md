# Dawn v1.4 Deployment

## Railway variables

Set these variables in Railway:

| Variable | Purpose |
|---|---|
| `OANDA_API_KEY` | OANDA API token |
| `OANDA_ACCOUNT_ID` | OANDA demo account ID |
| `TELEGRAM_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat/group ID |
| `DATA_DIR` | Usually `/data` |

## Expected startup log

```text
Dawn v1.4 — Scheduler starting
Health-check server listening on port 8080 — GET /health
OANDA | Mode: DEMO
API Key: configured
Login success!
```

## Expected Telegram startup

```text
🤖 Dawn v1.4
──────────────────────
🌅 Dawn v1.4 started
```

## Health check

Railway should use:

```text
/health
```
