# What's Goodie? TCG 2025 Discord Bot

A Discord bot for distributing "What's Goodie? TCG 2025" game cards to users based on 7-digit number inputs. Each unique number consistently maps to the same set of cards, and users are limited to one request.

## Features

- Detects 7-digit numbers in messages without requiring a command prefix
- Dispenses 5 cards per request with possibility of duplicates
- Supports two different operational modes:
  - **Private Channel Mode**: Creates private channels where only the requesting user, bot, and admins can see the cards
  - **Direct Embed Mode**: Announces card receipt in the main channel, shows cards in a private thread
- Implements card rarity system (Common, Rare, Mythic) with proper drop rates:
  - Rare Card Drop Chance: 15% (increased by 1.5x as per announcement)
  - Mythical Card Drop Chance: 0.02%
- Auto-deletes cards after 60 seconds for privacy
- Auto-deletes channels after 10 minutes of inactivity
- Users can type `DELETE` to immediately delete private channels
- Each user can only request cards once (tracked in a JSON file)
- Testing mode allows bypassing the one-time-only restriction
- Admin commands for managing the bot
- Logging of all requests with user details, timestamp, and which cards were dispensed
- Consistent card selection based on input number (same number always gets same cards)

## Setup

### Prerequisites

- Python 3.9 or newer
- Nextcord library
- A Discord bot token

### Installation

1. Clone this repository
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create an `images` folder in the project directory
4. Place your PNG card images in the `images` folder
   - Name cards with rarity in the filename (e.g., `rare_cardname.png`, `mythic_cardname.png`)
   - Cards without "rare" or "mythic" in the name will be treated as common
5. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ```

### Discord Bot Setup

1. Create a Discord application at https://discord.com/developers/applications
2. Create a bot user for your application
3. Enable the following Privileged Gateway Intents:
   - Message Content Intent
   - Server Members Intent
4. Generate an invitation URL with the following permission:
   - Bot
5. Invite the bot to your server using the generated URL
6. Add the bot to the game channel with the following permissions:
   - Read Message History
   - Send Messages
   - Manage Channels
   - Manage Threads
   - Read Message History
   - Attach Files

## Running the Bot

Simply run the `bot.py` file:

```
python bot.py
```

## Usage

1. Users type a 7-digit number in any channel the bot can see
2. The bot announces the user received cards in the channel (without revealing specific cards)
3. Depending on the mode:
   - In Direct Embed Mode: A private thread is created where the user can see their cards
   - In Private Channel Mode: A private channel is created where the user can see their cards
4. Cards are automatically deleted after 60 seconds
5. Channels/threads are automatically deleted after the timeout period

## Admin Commands

Administrators can use the following commands to manage the bot:

- `!wg mode private`: Switch to private channel mode
- `!wg mode direct`: Switch to direct embed mode
- `!wg test on`: Enable testing mode (bypasses one-time-only restriction)
- `!wg test off`: Disable testing mode
- `!wg reset @user`: Reset a user's request status to allow them to request again

## Admin Setup

1. Create an admin role in your Discord server, the role's ID needs to be added to the config. !!! IMPORTANT
2. Assign this role to any users who should have access to all private channels

## Configuration

Edit settings in `config.py`:

- `PRIVATE_CHANNEL_MODE`: Set to `True` for private channels or `False` for direct embeds
- `TESTING_MODE`: Set to `True` during development to bypass the one-time-only restriction
- `CARDS_PER_PACK`: Number of cards to dispense per request (default: 5)
- `CHANNEL_TIMEOUT_MINUTES`: Number of minutes before auto-deleting private channels

## File Structure

- `bot.py`: Main bot code
- `config.py`: Configuration loading and constants
- `utils.py`: Utility functions for user tracking, card selection, and logging
- `requirements.txt`: Required Python dependencies
- `.env`: Environment variables for configuration
- `user_data.json`: Auto-generated file tracking users who have requested cards
- `logs/bot_activity.log`: Log file with detailed activity records
- `images/`: Folder containing PNG card images to dispense

## Development Notes

- To add a test user (who can bypass the one-request limit), add their Discord user ID to the `TEST_USER_IDS` list in `utils.py`
- The bot determines card rarity based on filenames containing "rare" or "mythic"
- Duplicate cards are possible within the same pack