"""
Discord PNG Dispenser Bot.
This bot detects 7-digit numbers in messages and either creates private channels
or sends embeds directly in the channel to dispense random PNG images,
with the same input always yielding the same image.
"""
import re
import os
import asyncio
import traceback
import random
import nextcord
from nextcord.ext import commands
from typing import Optional, List
import config
from utils import (
    has_user_requested_image, 
    add_user_to_requested_list,
    get_image_for_number,
    get_multiple_cards_for_number,
    log_image_request,
    is_test_user,
    load_user_data,
    save_user_data
)

# Create log folder if it doesn't exist
os.makedirs(config.LOG_FOLDER, exist_ok=True)

# Initialize bot with intents
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Track active private channels
private_channels = {}

@bot.event
async def on_ready():
    """Event triggered when the bot is fully connected to Discord."""
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot is active in {len(bot.guilds)} guilds.')
    print(f'Mode: {"Private Channels" if config.PRIVATE_CHANNEL_MODE else "Direct Embeds"}')
    print(f'Testing mode: {"Enabled" if config.TESTING_MODE else "Disabled"}')
    
    # Set custom status
    await bot.change_presence(
        activity=nextcord.Activity(
            type=nextcord.ActivityType.playing, 
            name=f"{config.GAME_NAME} | 7-digit numbers"
        )
    )

async def create_private_channel(guild: nextcord.Guild, user: nextcord.Member, input_number: str) -> None:
    """
    Create a private channel for the user and bot to interact.
    
    Args:
        guild: The Discord guild where the request was made.
        user: The user who requested the image.
        input_number: The 7-digit number input by the user.
    """
    # Get admin role ADMIN_ROLE_ID
    admin_role = nextcord.utils.get(guild.roles, id=config.ADMIN_ROLE_ID) if config.ADMIN_ROLE_ID else None
    
    # Channel permissions
    overwrites = {
        guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
        guild.me: nextcord.PermissionOverwrite(read_messages=True, send_messages=True),
        user: nextcord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    # Add admin role permissions if it exists
    if admin_role:
        overwrites[admin_role] = nextcord.PermissionOverwrite(read_messages=True)
    
    # Create the private channel
    channel_name = f"cards-{user.name.lower()}"
    channel = await guild.create_text_channel(
        channel_name,
        overwrites=overwrites,
        reason=f"Card dispensing for user {user.name}"
    )
    
    # Select a random message from the embed messages list
    message_template = random.choice(config.EMBED_MESSAGES)
    description = message_template.format(user=user.mention)
    
    # Send announcement to the original channel
    announcement_embed = nextcord.Embed(
        title=f"🎮 {config.GAME_NAME} - Cards Received!",
        description=description,
        color=0xF1C40F
    )
    
    # Try to send announcement to the channel where the request was made
    try:
        request_channel = user.guild.get_channel(guild.system_channel.id)
        if request_channel:
            await request_channel.send(embed=announcement_embed)
    except Exception as e:
        print(f"Error sending announcement: {e}")
        print(traceback.format_exc())
    
    # Add channel to tracking dict with expiry time
    private_channels[channel.id] = {
        "user_id": user.id,
        "input_number": input_number,
        "created_at": nextcord.utils.utcnow()
    }
    
    try:
        # Send the image to the private channel
        await send_image_to_channel(channel, user, input_number)
        
        # Start a task to delete the channel after timeout
        bot.loop.create_task(delete_channel_after_timeout(channel))
    except Exception as e:
        print(f"Error in create_private_channel: {e}")
        print(traceback.format_exc())
        await channel.send("An error occurred while processing your request. This channel will be deleted shortly.")
        await channel.delete(reason="Error occurred during card dispensing")

async def send_image_to_channel(channel: nextcord.TextChannel, user: nextcord.Member, input_number: str) -> None:
    """
    Send multiple card images to the private channel.
    
    Args:
        channel: The Discord channel to send the images to.
        user: The user who requested the cards.
        input_number: The 7-digit number input by the user.
    """
    # Get multiple cards for the input number
    card_details = get_multiple_cards_for_number(input_number, config.CARDS_PER_PACK)
    if not card_details:
        await channel.send("No images found in the images folder. Please contact an administrator.")
        return
    
    # Welcome message
    await channel.send(
        f"Hello {user.mention}! I've created this private channel for you.\n"
        f"Here are your {config.CARDS_PER_PACK} cards for input number `{input_number}`.\n"
        f"This channel will be automatically deleted in {config.CHANNEL_TIMEOUT_MINUTES} minutes.\n"
        f"Type `DELETE` to delete this channel immediately after viewing your cards."
    )
    
    # Create a nice header for the pack
    pack_embed = nextcord.Embed(
        title=f"📦 {config.GAME_NAME} - Pack Opening! 🎮",
        description=f"Opening a pack with number `{input_number}`. Revealing {config.CARDS_PER_PACK} cards...",
        color=0xF1C40F  # Gold color
    )
    await channel.send(embed=pack_embed)
    
    # Send each card with a small delay between them
    for index, (image_path, image_name, rarity) in enumerate(card_details, 1):
        # Extract card name from file name (remove extension)
        card_name = image_name.replace('.png', '').replace('_', ' ').title()
        
        # Create embed for card info
        card_embed = nextcord.Embed(
            title=f"Card {index}/{config.CARDS_PER_PACK}: {card_name}",
            description=f"Rarity: **{rarity.title()}**",
            color=0x1DB954 if rarity == "common" else (0x9370DB if rarity == "rare" else 0xFFD700)
        )
        await channel.send(embed=card_embed)
        
        # Send the image as a file
        with open(image_path, 'rb') as f:
            image_file = nextcord.File(f, filename=image_name)
            await channel.send(file=image_file)
        
        # Small delay between cards
        await asyncio.sleep(1)
    
    # Summary message
    await channel.send(
        f"All {config.CARDS_PER_PACK} cards have been revealed! The images will be automatically deleted in 30 seconds for privacy."
    )
    
    # Set auto-delete timer for all the messages
    await asyncio.sleep(30)
    try:
        # Delete the last 15 messages (should cover all cards + messages)
        async for message in channel.history(limit=15):
            try:
                await message.delete()
            except nextcord.NotFound:
                # Message already deleted
                pass
        await channel.send("The images have been automatically deleted for privacy.")
    except Exception as e:
        print(f"Error cleaning up cards: {e}")
        print(traceback.format_exc())
    
    # Log the request (just once for the whole pack)
    log_image_request(user.name, user.id, f"{config.CARDS_PER_PACK}-card-pack", input_number)
    
    # Add user to the list of those who have received cards
    add_user_to_requested_list(user.id)

async def send_multiple_cards_embed(channel: nextcord.TextChannel, user: nextcord.Member, input_number: str) -> None:
    """
    Send 5 cards (with possible duplicates) as embeds directly in the channel.
    First announces that the user received cards, then sends cards in a thread.
    
    Args:
        channel: The Discord channel to send the images to.
        user: The user who requested the cards.
        input_number: The 7-digit number input by the user.
    """
    try:
        # Get the 5 cards for the input number (allowing duplicates)
        card_details = get_multiple_cards_for_number(input_number, config.CARDS_PER_PACK)
        
        if not card_details:
            await channel.send("No images found in the images folder. Please contact an administrator.")
            return
        
        # Create main announcement embed - only announcing that the user received cards
        announcement_embed = nextcord.Embed(
            title=f"🎮 {config.GAME_NAME} - Cards Received!",
            description=f"{user.mention} has received their {config.CARDS_PER_PACK} cards!",
            color=0xF1C40F  # Gold color for announcement
        )
        announcement_embed.set_footer(text=f"🍻 {config.GAME_NAME}")
        
        # Send the announcement
        announcement = await channel.send(embed=announcement_embed)
        
        # Create a thread to show the actual cards
        thread_name = f"{user.name}'s Cards"
        thread = await announcement.create_thread(name=thread_name)
        
        # Send introductory message in thread
        await thread.send(f"Here are your cards from number `{input_number}`, {user.mention}! They will disappear in 60 seconds.")
        
        # Small delay for dramatic effect
        await asyncio.sleep(1)
        
        # Send each card with a small delay between them
        for index, (image_path, image_name, rarity) in enumerate(card_details, 1):
            # Extract card name from file name (remove extension)
            card_name = image_name.replace('.png', '').replace('_', ' ').title()
            
            # Get color based on rarity
            if rarity == "mythic":
                color = 0xFFD700  # Gold for mythic
            elif rarity == "rare":
                color = 0x9370DB  # Purple for rare
            else:
                color = 0x1DB954  # Green for common
            
            # Create embed for each card
            card_embed = nextcord.Embed(
                title=f"Card {index}/{config.CARDS_PER_PACK}: {card_name}",
                description=f"Rarity: **{rarity.title()}**",
                color=color
            )
            
            # Send the image as a file with embed
            with open(image_path, 'rb') as f:
                image_file = nextcord.File(f, filename=image_name)
                await thread.send(embed=card_embed, file=image_file)
            
            # Small delay between cards for dramatic effect
            await asyncio.sleep(1.5)
        
        # Completion message
        summary_embed = nextcord.Embed(
            title="Pack Opening Complete!",
            description=f"{user.mention} has received all {config.CARDS_PER_PACK} cards!",
            color=0xF1C40F
        )
        summary_embed.set_footer(text="Cards will vanish in 60 seconds! 🕒")
        await thread.send(embed=summary_embed)
        
        # Log the request (just once for the whole pack)
        log_image_request(user.name, user.id, "5-card-pack", input_number)
        
        # Add user to the list of those who have received cards
        add_user_to_requested_list(user.id)
        
        # Set auto-delete timer for the thread after 60 seconds
        await asyncio.sleep(60)
        try:
            await thread.delete()
            await channel.send(f"🕒 {user.mention}, your cards have vanished after 60 seconds!", delete_after=10)
        except Exception as e:
            print(f"Error cleaning up cards thread: {e}")
            print(traceback.format_exc())
            
    except Exception as e:
        print(f"Error in send_multiple_cards_embed: {e}")
        print(traceback.format_exc())
        await channel.send(
            f"An error occurred while processing your request. Please try again later.",
            delete_after=30
        )
        
        # Log the request
        log_image_request(user.name, user.id, image_name, input_number)
        
        # Add user to the list of those who have received an image
        add_user_to_requested_list(user.id)
        
    except Exception as e:
        print(f"Error in send_image_embed: {e}")
        print(traceback.format_exc())
        await channel.send(
            f"An error occurred while processing your request. Please try again later.",
            delete_after=30
        )

async def delete_channel_after_timeout(channel: nextcord.TextChannel) -> None:
    """
    Delete a channel after the configured timeout period.
    
    Args:
        channel: The Discord channel to delete.
    """
    try:
        # Wait for the timeout duration
        await asyncio.sleep(config.CHANNEL_TIMEOUT_MINUTES * 60)
        
        # Check if channel still exists and delete it
        try:
            await channel.send("This channel will be deleted in 10 seconds due to inactivity.")
            await asyncio.sleep(10)
            await channel.delete(reason="Timeout: PNG dispensing channel auto-deleted")
        except nextcord.NotFound:
            # Channel already deleted
            pass
        
        # Remove from tracking dict if still there
        if channel.id in private_channels:
            del private_channels[channel.id]
    except Exception as e:
        print(f"Error in delete_channel_after_timeout: {e}")
        print(traceback.format_exc())

@bot.event
async def on_message_delete(message):
    """Event triggered when a message is deleted."""
    # We don't need to do anything here, just defining it for completeness
    pass

@bot.event
async def on_message_edit(before, after):
    """Event triggered when a message is edited."""
    # We don't need to do anything here, just defining it for completeness
    pass

@bot.event
async def on_message(message):
    """
    Event triggered when a message is sent.
    Handles both commands and the 7-digit number detection.
    
    Args:
        message: The Discord message object.
    """
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check for DELETE command in private channels
    if message.channel.id in private_channels and message.content.upper() == "DELETE":
        try:
            await message.channel.send("Channel will be deleted in 3 seconds...")
            await asyncio.sleep(3)
            await message.channel.delete(reason="User requested channel deletion")
            # Remove from tracking dict
            if message.channel.id in private_channels:
                del private_channels[message.channel.id]
            return
        except Exception as e:
            print(f"Error while deleting channel: {e}")
            print(traceback.format_exc())
    
    if config.GAME_CHANNEL_ID and message.channel.id != config.GAME_CHANNEL_ID:
        return

    # Process normal commands
    await bot.process_commands(message)
    
    # Admin commands
    if message.content.startswith("!wg"):
        # Check if user has admin permissions
        if not message.author.guild_permissions.administrator:
            return
            
        args = message.content.split()
        if len(args) < 2:
            await message.channel.send("Usage: !wg [mode|test|reset] [value]", delete_after=30)
            return
            
        command = args[1].lower()
        
        # Command to toggle modes
        if command == "mode" and len(args) == 3:
            value = args[2].lower()
            if value in ["private", "channel", "p", "c"]:
                # Set to private channel mode
                global PRIVATE_CHANNEL_MODE
                config.PRIVATE_CHANNEL_MODE = True
                await message.channel.send("✅ Bot set to private channel mode.", delete_after=30)
            elif value in ["direct", "embed", "d", "e"]:
                # Set to direct embed mode
                config.PRIVATE_CHANNEL_MODE = False
                await message.channel.send("✅ Bot set to direct embed mode.", delete_after=30)
            else:
                await message.channel.send("Invalid mode. Use 'private' or 'direct'.", delete_after=30)
                
        # Command to toggle testing mode
        elif command == "test" and len(args) == 3:
            value = args[2].lower()
            if value in ["on", "true", "1", "yes", "y"]:
                config.TESTING_MODE = True
                await message.channel.send("✅ Testing mode enabled.", delete_after=30)
            elif value in ["off", "false", "0", "no", "n"]:
                config.TESTING_MODE = False
                await message.channel.send("✅ Testing mode disabled.", delete_after=30)
            else:
                await message.channel.send("Invalid value. Use 'on' or 'off'.", delete_after=30)
                
        # Command to reset a user's request status
        elif command == "reset" and len(args) == 3:
            try:
                # Try to get user by ID
                user_id = int(args[2])
                user_data = load_user_data()
                if user_id in user_data["users"]:
                    user_data["users"].remove(user_id)
                    save_user_data(user_data)
                    await message.channel.send(f"✅ Reset request status for user ID {user_id}.", delete_after=30)
                else:
                    await message.channel.send(f"User ID {user_id} has not requested an image.", delete_after=30)
            except ValueError:
                # If not a numeric ID, try to find by mention
                if message.mentions:
                    user = message.mentions[0]
                    user_data = load_user_data()
                    if user.id in user_data["users"]:
                        user_data["users"].remove(user.id)
                        save_user_data(user_data)
                        await message.channel.send(f"✅ Reset request status for {user.name}.", delete_after=30)
                    else:
                        await message.channel.send(f"{user.name} has not requested an image.", delete_after=30)
                else:
                    await message.channel.send("Invalid user ID or mention.", delete_after=30)
    
    # Check for 7-digit number pattern
    match = re.match(config.SEVEN_DIGIT_PATTERN, message.content.strip())
    if match and not message.channel.id in private_channels:
        # Get the user and the input number
        user = message.author
        input_number = message.content.strip()
        
        try:
            # Check if user has already requested an image (unless in testing mode or is a test user)
            if has_user_requested_image(user.id) and not config.TESTING_MODE and not is_test_user(user.id):
                await message.channel.send(
                    f"{user.mention}, you have already received a card and cannot request another one.",
                    delete_after=30
                )
                return
            
            # Choose the appropriate method based on config
            if config.PRIVATE_CHANNEL_MODE:
                # Create a private channel for the user
                await create_private_channel(message.guild, user, input_number)
            else:
                # Send multiple cards directly in the channel
                await send_multiple_cards_embed(message.channel, user, input_number)
                
        except Exception as e:
            print(f"Error in on_message: {e}")
            print(traceback.format_exc())
            await message.channel.send(
                f"An error occurred while processing your request. Please try again later.",
                delete_after=30
            )

if __name__ == "__main__":
    try:
        # Check if token is properly set
        if not config.TOKEN:
            raise ValueError("Discord token not found. Please check your .env file.")
        
        # Start the bot
        bot.run(config.TOKEN)
    except Exception as e:
        print(f"Error starting the bot: {e}")
        print(traceback.format_exc())