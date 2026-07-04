# Deployment

This bot uses Telegram long polling, so it does not need a public web URL or webhook. It only needs an always-on process with outbound internet access.

## Recommended Host: Render Background Worker

Render is a straightforward fit because its background workers are continuous services that do not receive incoming traffic. The included `Dockerfile` and `render.yaml` are enough for a worker deployment.

The blueprint is set to request Render's `free` instance type. If Render's dashboard does not offer Free for a Background Worker in your workspace, use the cheapest paid worker or deploy the Docker container on an Always Free VM instead. Do not use a sleeping free web service for this bot unless you are comfortable with the bot going offline while it is idle.

### 1. Create the Telegram Bot

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

### 2. Push the Repository

Push this repository to GitHub first. The configured remote is:

```bash
git@github.com:nimnes/poe2-map-bot.git
```

If SSH is not loaded yet:

```bash
ssh-add ~/.ssh/id_ed25519
git push -u origin main
```

### 3. Deploy on Render

1. Go to Render and create a new Blueprint from the GitHub repository, or create a new Background Worker manually.
2. If creating manually, choose Docker and point it at this repository.
3. Add environment variables:

```text
TELEGRAM_BOT_TOKEN=<token from BotFather>
MAP_DATA_PATH=/app/data/maps.json
LOG_LEVEL=INFO
```

4. Deploy the worker.
5. Open the bot in Telegram and send `/start`, then try `/map Augury`.

## Other Good Hosting Choices

- Oracle Cloud Always Free VM: best truly-free always-on option, but more manual setup.
- Google Cloud free-tier VM: another always-free VM route if your region/account qualifies.
- Fly.io: good if you like Docker and CLI-driven deploys.
- Railway: simple app hosting with environment variables.
- A small VPS: cheapest long-term if you are comfortable running Docker yourself.

For this bot, avoid static hosts and serverless functions unless you convert it to Telegram webhooks. Long polling needs a process that stays running.

## Local Smoke Test

```bash
docker build -t poe2-map-bot .
docker run --rm --env-file .env poe2-map-bot
```
