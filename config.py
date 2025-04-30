"""
Configuration settings for the Discord PNG Dispenser Bot.
"""
import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


#  #  #  #  #  #   #  #  #  #  #   #  #  #  #  #   #  #  #  #  #   #  #  #  #  # 
# Channel/Mode settings
# This is for the optional temp channels to dispense images privately.
PRIVATE_CHANNEL_MODE = False  # True = create private channel, False = send in same channel
CHANNEL_TIMEOUT_MINUTES = 10 # <--------------------------------
ADMIN_ROLE_ID = 1085017887728750634 # <--------------------------------

# Embed message variations (for the direct embed mode)
# These will be randomly selected when sending embeds
EMBED_MESSAGES = [
    "🍻 {user} has received their cards!",
    "🎉 {user} just got their cards!",
    "🥃 {user} pulled their cards!",
    "🎮 {user} received their What's Goodie cards!",
    "🔓 {user} got a fresh pack of cards!",
    "🎲 {user} received their TCG cards!",
    "💯 {user} is ready to play with their new cards!",
    "🎭 {user} just received a pack of What's Goodie cards!",
    "🌟 Party on! {user} received their cards!",
    "🍸 {user} just got served their cards!"
]
 

#  #  #  #  #  #   #  #  #  #  #   #  #  #  #  #   #  #  #  #  #   #  #  #  #  # 
# Bot token from environment variables
TOKEN = os.getenv('DISCORD_TOKEN')

# Folder paths
IMAGES_FOLDER = Path("images")
LOG_FOLDER = Path("logs")
USER_DATA_FILE = Path("user_data.json")
LOG_FILE = LOG_FOLDER / "bot_activity.log"
# Testing mode (True = bypass one-time-only restriction)
TESTING_MODE = True
is_test_user = os.getenv('TEST_USER', 'false').lower() == 'true' # SET to 'false' to disable test user bypass

# Image request pattern
SEVEN_DIGIT_PATTERN = r"^\d{7}$"

# Game information
GAME_NAME = "What's Goodie? TCG 2025"
CARDS_PER_PACK = 5  # Number of cards in each pack