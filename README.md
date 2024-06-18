# Telegram Strava Bot

## Setup and Usage Guide

### Prerequisites

Before you start, ensure you have the following:

- Python 3.6 or later installed
- A MongoDB instance
- A Telegram Bot Token
- A Strava API Client ID and Client Secret

### Step 1: Create the `secure.py` file

Create a file named `secure.py` in the root directory of your project. This file will store your sensitive information. Add the following variables to the `secure.py` file:

```python
# secure.py

# Telegram bot token
TELEGRAM_BOT_TOKEN = 'your-telegram-bot-token'

# MongoDB URI
MONGO_URI = 'your-mongodb-uri'

# Telegram group ID
TELEGRAM_GROUP_ID = 'your-telegram-group-id'

# Strava client ID
STRAVA_CLIENT_ID = 'your-strava-client-id'

# Strava client secret
STRAVA_CLIENT_SECRET = 'your-strava-client-secret'

# Telegram bot ID
TELEGRAM_BOT_ID = 'your-telegram-bot-id'

# Strava APP Redirect URI
STRAVA_REDIRECT_URI = 'your-strava-app-redirect-uri'
```

### Step 2: Install Dependencies

Install the necessary Python packages using `pip`. You can do this by running the following command:

```bash
pip install -r requirements.txt
```

### Step 3: Initialize the Bot

```
python bot.py
```

### Step 4: Set Up Telegram Group

1. Open the Telegram app on your device.
2. Create a new group by tapping the "New Group" option.
3. Add members to the group as desired.
4. Add the bot to the group.

Once the bot is added to the group, it will be able to listen and respond to messages in that group.

Your bot should now be running and responding to commands in your specified Telegram group.
