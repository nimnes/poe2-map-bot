# Deployment

The bot supports two runtime modes:

- Polling: best for an always-on worker or VM.
- Webhook: best for Render Free Web Service.

Because Render says Background Workers are not available on your plan, use the webhook path below.

## 1. Create the Telegram Bot

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot`.
3. Choose a display name, for example `PoE 2 HC Map Bot`.
4. Choose a username ending in `bot`, for example `poe2_hc_map_bot`.
5. Copy the token BotFather gives you. Keep it secret.

Useful BotFather setup:

```text
/setdescription
PoE 2 map summaries, HC risk ratings, bosses, biomes, and quick survival tips.

/setabouttext
Hardcore-focused Path of Exile 2 map helper.

/setcommands
start - Start the bot
help - Show help
map - Look up a map by name
maps - List known maps
reload - Reload map data
```

## 2. Deploy Free On Render

Use a Render Web Service, not a Background Worker.

1. Push this repository to GitHub.
2. In Render, choose New > Blueprint or New > Web Service.
3. Select the GitHub repository.
4. Use Docker.
5. Set the service name to `poe2-map-bot`.
6. Choose the Free instance type.
7. Add environment variables:

```text
TELEGRAM_BOT_TOKEN=<token from BotFather>
TELEGRAM_WEBHOOK_URL=https://poe2-map-bot.onrender.com
MAP_DATA_PATH=/app/data/maps.json
LOG_LEVEL=INFO
```

If Render gives your service a different URL, use that exact URL for `TELEGRAM_WEBHOOK_URL`.

`TELEGRAM_WEBHOOK_PATH` is a secret path used by Telegram to reach the bot. The included `render.yaml` asks Render to generate it. If you create the Web Service manually, set it to any random string, for example:

```text
TELEGRAM_WEBHOOK_PATH=telegram-a-long-random-secret
```

8. Deploy the service.
9. Watch the logs. You want to see:

```text
Starting PoE 2 map bot with webhook
```

10. Open the bot in Telegram and send `/start`, then `/map Augury`.

## Important Free-Tier Caveat

Render Free Web Services spin down after idle periods. A Telegram message should wake the service, but the first message after sleep can be delayed while Render starts the container. If the first message times out, send it again after about a minute.

For a bot that must respond instantly 24/7, use an always-on host instead:

- Oracle Cloud Always Free VM
- Google Cloud free-tier VM, if eligible
- A small paid VPS
- A paid Render Background Worker

## Local Smoke Test

Polling mode:

```bash
docker build -t poe2-map-bot .
docker run --rm --env-file .env poe2-map-bot
```

Webhook mode locally needs a public tunnel URL, so polling is simpler for local testing.
