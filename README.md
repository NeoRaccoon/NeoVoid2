# NeoVoid

A multi-purpose Discord bot for VRChat community management — handles member linking, age verification, staff applications, moderation logging, and more.

## Features

- **VRChat Account Linking** — Members link their VRChat profile to Discord for verification
- **Age Verification** — In-DM review workflow with approve/deny buttons for staff
- **Staff Applications** — Custom application forms for Security/Bartender roles, submitted and reviewed in-DM
- **Moderation Logging** — Tracks deleted/edited messages, member joins/leaves, nickname changes
- **Auto-moderation** — Spam detection, scam link filtering, mass mention protection
- **VRChat API Integration** — World/avatar lookups via VRChat API
- **OSINT Toolkit** — Email, username, and phone number reconnaissance commands
- **Custom Commands** — Configurable prefix commands for community engagement

## Setup

```bash
# Clone and install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Discord bot token and API keys
```

### Environment Variables (`.env`)

```
TOKEN=your_discord_bot_token
OPENROUTER_API_KEY=sk-or-...
CEREBRAS_API_KEY=csk-...
OPENROUTER_MODEL=openai/gpt-4o-mini
CEREBRAS_MODEL=gpt-oss-120b
```

## Running

```bash
python neovoid.py
```

### Docker

```bash
docker compose up --build
```
