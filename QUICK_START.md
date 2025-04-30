So to setup you need to install the discord dependencies with
```
pip install -r requirements.txt
```
Then card images go into the images folder, and the .env file needs to be configured with your Discord bot token:
```
DISCORD_TOKEN=your_discord_bot_token_here
```

The config also needs to be modified if you want to change the default settings:
- Set `PRIVATE_CHANNEL_MODE = False` if you want to use direct embed mode
- Set `TESTING_MODE = True` during development to bypass the one-request limit
- Adjust `CARDS_PER_PACK` if you want to change how many cards are given out (default: 5)

Your card image files should be named to indicate rarity:
- Regular cards: `cardname.png`
- Rare cards: `rare_cardname.png`
- Mythic cards: `mythic_cardname.png`

To run the bot, just use:
```
python bot.py
```

Users get cards by typing any 7-digit number in a Discord channel. The bot will announce they received cards but only show the actual cards in private threads or channels. Each user can only request cards once unless an admin resets them with the `!wg reset @username` command.

Admins can switch modes with `!wg mode direct` or `!wg mode private` and toggle testing mode with `!wg test on` or `!wg test off`.