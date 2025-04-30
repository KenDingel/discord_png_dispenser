"""
Utility functions for the Discord PNG Dispenser Bot.
"""
import json
import os
import logging
import hashlib
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from config import USER_DATA_FILE, IMAGES_FOLDER, LOG_FILE

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# List of test user IDs who can bypass the one-time-only restriction
TEST_USER_IDS = [
    # Add your Discord user ID here for testing
]

def is_test_user(user_id: int) -> bool:
    """
    Check if a user is designated as a test user (can bypass one-time-only restriction).
    
    Args:
        user_id (int): Discord user ID.
        
    Returns:
        bool: True if user is a test user, False otherwise.
    """
    return user_id in TEST_USER_IDS

def load_user_data() -> Dict:
    """
    Load user data from JSON file.
    
    Returns:
        Dict: Dictionary containing user data.
    """
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding {USER_DATA_FILE}. Creating new user data.")
            return {"users": []}
    else:
        logger.info(f"User data file not found. Creating new file at {USER_DATA_FILE}")
        return {"users": []}

def save_user_data(data: Dict) -> None:
    """
    Save user data to JSON file.
    
    Args:
        data (Dict): User data to save.
    """
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    logger.info(f"User data saved to {USER_DATA_FILE}")

def has_user_requested_image(user_id: int) -> bool:
    """
    Check if a user has already requested an image.
    
    Args:
        user_id (int): Discord user ID.
        
    Returns:
        bool: True if user has already requested an image, False otherwise.
    """
    user_data = load_user_data()
    return user_id in user_data["users"]

def add_user_to_requested_list(user_id: int) -> None:
    """
    Add a user to the list of users who have requested images.
    
    Args:
        user_id (int): Discord user ID.
    """
    user_data = load_user_data()
    if user_id not in user_data["users"]:
        user_data["users"].append(user_id)
        save_user_data(user_data)
        logger.info(f"User {user_id} added to requested list")

def get_image_for_number(input_number: str) -> Tuple[Optional[Path], Optional[str]]:
    """
    Get a consistent image based on a 7-digit input number.
    
    Args:
        input_number (str): 7-digit number input by the user.
        
    Returns:
        Tuple[Optional[Path], Optional[str]]: Path to image file and filename,
                                             or (None, None) if no images found.
    """
    # List all PNG files in the images folder
    image_files = list(IMAGES_FOLDER.glob("*.png"))
    
    # If no images found, return None
    if not image_files:
        logger.warning(f"No PNG images found in {IMAGES_FOLDER}")
        return None, None
    
    # Create a deterministic seed from the input number
    hash_value = hashlib.sha256(input_number.encode()).hexdigest()
    seed = int(hash_value, 16) % 10000000
    
    # Use the seed to select an image
    random.seed(seed)
    selected_image = random.choice(image_files)
    logger.info(f"Selected image {selected_image.name} for input {input_number}")
    
    return selected_image, selected_image.name

def get_multiple_cards_for_number(input_number: str, num_cards: int = 5) -> List[Tuple[Path, str, str]]:
    """
    Get multiple cards (with possible duplicates) based on a 7-digit input number.
    
    Args:
        input_number (str): 7-digit number input by the user.
        num_cards (int): Number of cards to generate (default: 5).
        
    Returns:
        List[Tuple[Path, str, str]]: List of tuples containing (image_path, image_name, rarity)
                                    for each card, or empty list if no images found.
    """
    # List all PNG files in the images folder
    image_files = list(IMAGES_FOLDER.glob("*.png"))
    
    # If no images found, return empty list
    if not image_files:
        logger.warning(f"No PNG images found in {IMAGES_FOLDER}")
        return []
    
    # Create a deterministic seed from the input number
    hash_value = hashlib.sha256(input_number.encode()).hexdigest()
    seed = int(hash_value, 16) % 10000000
    random.seed(seed)
    
    # Separate images by rarity (based on filename)
    common_cards = []
    rare_cards = []
    mythic_cards = []
    
    for img in image_files:
        name_lower = img.name.lower()
        if "mythic" in name_lower:
            mythic_cards.append(img)
        elif "rare" in name_lower:
            rare_cards.append(img)
        else:
            common_cards.append(img)
    
    # Make sure we have at least some cards in each category
    if not common_cards:
        common_cards = image_files  # Default to all cards if no commons found
    
    # Calculate rarity drop rates
    # These values are from the announcement: rare rate x1.5, mythic rate 0.02%
    rare_rate = 0.15  # 15% chance for a rare card (assuming baseline was 10%)
    mythic_rate = 0.0002  # 0.02% chance for a mythic card
    
    # Select cards with possible duplicates
    selected_cards = []
    for _ in range(num_cards):
        # Determine rarity for this card position
        roll = random.random()
        
        if roll < mythic_rate and mythic_cards:
            # Mythic card (very rare)
            card = random.choice(mythic_cards)
            rarity = "mythic"
        elif roll < rare_rate and rare_cards:
            # Rare card
            card = random.choice(rare_cards)
            rarity = "rare"
        else:
            # Common card
            card = random.choice(common_cards)
            rarity = "common"
        
        selected_cards.append((card, card.name, rarity))
        logger.info(f"Selected {rarity} card {card.name} for input {input_number}")
    
    return selected_cards

def log_image_request(user_name: str, user_id: int, image_name: str, input_number: str) -> None:
    """
    Log an image request to the log file.
    
    Args:
        user_name (str): Discord username.
        user_id (int): Discord user ID.
        image_name (str): Name of the dispensed image.
        input_number (str): 7-digit number input by the user.
    """
    logger.info(
        f"Image Request: User={user_name}({user_id}) | "
        f"Input={input_number} | Image={image_name} | "
        f"Time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )