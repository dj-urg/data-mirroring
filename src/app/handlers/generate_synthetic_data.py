import json
import random
import time
import datetime
import calendar
import string
import os
import uuid
from zoneinfo import ZoneInfo
import logging
from werkzeug.utils import secure_filename
from app.utils.file_manager import get_user_temp_dir

# Expanded persona-specific content dictionaries
PERSONA_CONTENT = {
    'career': {
        'authors': ['bloomberg_business', 'wall_street_journal', 'financial_times', 'career_coach_pro', 
                   'exec_mentor', 'linkedin_news', 'harvard_biz_review', 'ted_talks', 'investopedia', 
                   'forbes_finance', 'the_economist', 'mckinsey_insights', 'hbr_ascend', 'fortune_magazine',
                   'business_insider', 'entrepreneur_daily', 'startup_grind', 'inc_magazine', 'fastcompany'],
        'titles': ['Market Analysis Q1 202X', 'Leadership Workshop Recap', 'Networking Strategies for Introverts', 
                  'Investment Banking Trends', 'Guide to Your Next Promotion', 'Economic Outlook Update', 
                  'FinTech Innovations', 'Remote Work Productivity Hacks', 'Negotiation Tactics That Work',
                  'Building Your Personal Brand', 'AI in the Workplace', 'The Future of Work', 
                  'Effective Team Management', 'Venture Capital Insights', 'Stock Market Analysis',
                  'How to Nail Your Next Interview', 'Resume Building Tips', 'Business Ethics Today',
                  'Sustainable Business Practices', 'Emerging Markets Forecast']
    },
    'fitness': {
        'authors': ['brussels_runners', 'crossfit_capital', 'zen_flow_yoga', 'olympic_swimming_archive', 
                   'nike_running', 'lululemon_eu', 'garmin_fitness', 'runners_world_mag', 'mens_health_mag', 
                   'womens_health_mag', 'triathlon_life', 'strava_stories', 'peloton_cycle',
                   'yoga_with_adriene', 'fitbit_official', 'myfitnesspal', 'calisthenics_movement', 
                   'velopark_cycling', 'gymshark', 'climbing_daily', 'marathon_runners', 'strong_lifts'],
        'titles': ['Marathon Training: Final Weeks', 'New CrossFit WOD Ideas', 'Advanced Vinyasa Flow', 
                  'Swim Technique Drills', 'Best Running Shoes 202X Review', 'High-Protein Meal Prep', 
                  'Race Day Checklist', 'Yoga for Recovery', 'HIIT Cardio Workout', 'Strength Training Basics',
                  '10K Training Plan', 'Mobility Exercises for Runners', 'Plant-based Protein Sources',
                  'Morning vs Evening Workouts', 'Injury Prevention Tips', 'Core Strength for Cyclists',
                  'Mountain Trail Running Guide', 'Boxing for Fitness', 'Recovery Nutrition Strategies',
                  'Home Workout Equipment Essentials']
    },
    'traveler': {
        'authors': ['visitbrussels', 'cntraveler', 'travel_photo_world', 'lonely_planet', 'nomadic_matt', 
                   'world_nomads', 'travel_channel', 'rick_steves', 'national_geographic_travel',
                   'backpacker_life', 'culture_trip', 'airbnb_experiences', 'travel_leisure', 'hostelworld',
                   'intrepid_travel', 'atlas_obscura', 'view_from_the_wing', 'suitcase_magazine', 
                   'wanderlust_magazine', 'tripadvisor', 'afar_media', 'roadtrippers'],
        'titles': ['Hidden Gems of Europe', 'Budget Travel Tips', 'Sustainable Tourism', 
                  'Off-the-Beaten-Path Destinations', 'Cultural Experiences Around the Globe', 
                  'Adventure Travel Guide', 'Photography Travel Tips', 'Solo Female Travel Safety',
                  'Digital Nomad Hubs 202X', 'Best Hiking Trails in Asia', 'Island Hopping in Greece',
                  'Authentic Food Experiences', 'UNESCO Heritage Sites', 'Traveling with Kids',
                  'Luxury on a Budget', 'Backpacking Essentials', 'Road Trip Routes', 'Travel Hacking 101',
                  'Best Time to Visit Popular Destinations', 'Local Festivals Worth Traveling For']
    },
    'foodie': {
        'authors': ['clean_eats_blog', 'good_food_guide', 'mindful_cooking', 'international_cuisine', 
                   'vegan_delights', 'street_food_lover', 'michelin_guide', 'culinary_adventures', 
                   'food_network', 'bon_appetit', 'saveur_mag', 'serious_eats', 'jamie_oliver',
                   'food52', 'epicurious', 'tasty', 'the_kitchn', 'minimalist_baker', 'delish',
                   'spruce_eats', 'thug_kitchen', 'binging_with_babish', 'chef_john', 'smitten_kitchen'],
        'titles': ['Healthy & Quick Weeknight Dinners', 'Culinary World Tour', 'Sustainable Cooking Practices', 
                  'Farm-to-Table Recipes', 'International Street Food Guide', 'Cooking Techniques Masterclass', 
                  'Food Photography Tips', 'Seasonal Ingredients Guide', 'Sourdough Bread Baking',
                  'Instant Pot Recipe Collection', 'Authentic Thai Cooking', 'Zero Waste Kitchen',
                  'Wine Pairing Fundamentals', 'Vegan Meal Prep', 'Perfecting the Art of French Pastry',
                  'Homemade Pasta Workshop', 'Spice Blending 101', 'Fermentation and Pickling',
                  'Cast Iron Cooking', 'Budget Gourmet Meals']
    },
    'techie': {
        'authors': ['wired', 'techcrunch', 'the_verge', 'mit_technology_review', 'digital_trends', 
                   'ars_technica', 'recode', 'cnet', 'engadget', 'hackernews', 'product_hunt',
                   'github_official', 'stack_overflow', 'dev_to', 'android_authority',
                   'macrumors', 'venture_beat', 'techradar', 'gizmodo', 'slashdot',
                   'smashing_magazine', 'wired_uk', 'techspot', 'the_register'],
        'titles': ['AI Breakthrough 202X', 'Emerging Tech Trends', 'Cybersecurity Insights', 
                  'Future of Robotics', 'Innovation in Tech', 'Startup Ecosystem Report', 
                  'Gadget Reviews', 'Blockchain Beyond Cryptocurrency', 'Quantum Computing Explained',
                  'The State of Web Development', 'Data Privacy Concerns', 'Cloud Architecture Patterns',
                  'Machine Learning for Beginners', 'Open Source Projects to Watch', 'Tech Ethics',
                  'AR/VR Development', 'Smart Home Technologies', 'Edge Computing Explained',
                  'Coding Best Practices', 'Future of Mobile Technology']
    }
}

# Activity level mapping
ACTIVITY_MULTIPLIERS = {
    'low': 0.5,     # Occasional User
    'medium': 1.0,  # Regular User
    'high': 1.8     # Power User
}

# Time patterns - people tend to be more active at certain times
TIME_PATTERNS = {
    "early_morning": {"hours": range(5, 8), "weight": 0.5},     # 5-8 AM
    "morning": {"hours": range(8, 12), "weight": 1.0},          # 8-12 PM
    "lunch": {"hours": range(12, 14), "weight": 1.5},           # 12-2 PM
    "afternoon": {"hours": range(14, 17), "weight": 0.8},       # 2-5 PM
    "evening": {"hours": range(17, 22), "weight": 2.0},         # 5-10 PM
    "night": {"hours": range(22, 24), "weight": 1.0},           # 10-12 AM
    "late_night": {"hours": range(0, 5), "weight": 0.3}         # 12-5 AM
}

# Day of week patterns - people tend to be more active on certain days
DAY_WEIGHTS = {
    0: 0.8,  # Monday
    1: 0.9,  # Tuesday
    2: 1.0,  # Wednesday
    3: 1.0,  # Thursday
    4: 1.2,  # Friday
    5: 1.5,  # Saturday
    6: 1.3   # Sunday
}

def random_string(length=11):
    """Generate a random string for URLs."""
    chars = string.ascii_lowercase + string.digits + '-' + '_'
    return ''.join(random.choice(chars) for _ in range(length))

def random_url():
    """Generate a realistic random Instagram URL."""
    base = random.choice([
        "https://www.instagram.com/p/", 
        "https://www.instagram.com/reel/"
    ])
    return base + random_string() + "/"

def weighted_timestamp(base_timestamp, day_of_week):
    """Generate timestamps that follow realistic user patterns."""
    # Start with the base timestamp
    dt = datetime.datetime.fromtimestamp(base_timestamp, tz=datetime.timezone.utc)
    
    # Apply day of week weighting
    day_weight = DAY_WEIGHTS[dt.weekday()]
    if random.random() > day_weight:
        # Skip this timestamp based on day weighting
        return None
    
    # Apply time of day patterns
    hour = dt.hour
    time_weight = 0.5  # Default weight
    
    for pattern, info in TIME_PATTERNS.items():
        if hour in info["hours"]:
            time_weight = info["weight"]
            break
            
    if random.random() > time_weight:
        # Skip this timestamp based on time weighting
        return None
        
    # Randomize minutes and seconds
    dt = dt.replace(
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
    )
    
    return int(dt.timestamp())

def generate_synthetic_data(persona_type, activity_level, output_filename):
    """
    Generate synthetic Instagram data based on user inputs.
    
    :param persona_type: Type of persona (career, fitness, traveler, foodie, techie)
    :param activity_level: User's activity level (low, medium, high)
    :param output_filename: Filename to save the JSON data
    :return: Dictionary with generated data
    """
    logger = logging.getLogger()
    logger.info(f"Generating synthetic data: persona={persona_type}, activity={activity_level}, output={output_filename}")
        
    # 1. Sanitize the filename
    safe_filename = secure_filename(os.path.basename(output_filename))
    
    # 2. Get the proper user temp directory
    temp_dir = get_user_temp_dir()
    
    # 3. Join safely with the intended directory
    output_path = os.path.join(temp_dir, safe_filename)
    
    # 4. Additional protection: verify the resulting path is still within the temp directory
    real_output_path = os.path.realpath(output_path)
    real_temp_dir = os.path.realpath(temp_dir)
    
    if not real_output_path.startswith(real_temp_dir):
        logger.error(f"Path traversal attempt detected with filename: {output_filename}")
        raise ValueError("Security error: Invalid filename")
    
    # Now we can safely create the directory if needed
    output_dir = os.path.dirname(real_output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # Reassign output_filename to the secure path
    output_filename = real_output_path
    
    # Check file permissions
    try:
        # Test write permission using the secure, sanitized path
        with open(real_output_path, 'a') as test_file:
            pass
        logger.info(f"Write permission OK for {real_output_path}")
    except Exception as e:
        logger.error(f"Cannot write to output file: {e}")
        return None
    
    try:
        # Configuration
        START_YEAR = 2015
        START_MONTH = 4
        END_DATETIME_UTC = datetime.datetime.now(datetime.timezone.utc)

        # Ensure valid inputs
        if persona_type not in PERSONA_CONTENT:
            return None
        
        # Adjust ranges based on activity level
        multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.0)
        
        # Base ranges for activities per month
        NUM_SAVES_RANGE = (int(2 * multiplier), int(8 * multiplier))
        NUM_LIKES_RANGE = (int(8 * multiplier), int(25 * multiplier))
        NUM_WATCHES_RANGE = (int(20 * multiplier), int(50 * multiplier))

        # Secondary interests - add variety by including content from other personas
        secondary_interests = []
        for other_type in PERSONA_CONTENT.keys():
            if other_type != persona_type and random.random() < 0.3:  # 30% chance to have secondary interest
                secondary_interests.append(other_type)
        
        # Create a mixed content pool with primary and secondary interests
        mixed_authors = PERSONA_CONTENT[persona_type]['authors'].copy()
        mixed_titles = PERSONA_CONTENT[persona_type]['titles'].copy()
        
        # Add some content from secondary interests
        for interest in secondary_interests:
            # Add a subset of authors from secondary interest
            secondary_authors = random.sample(
                PERSONA_CONTENT[interest]['authors'],
                k=min(5, len(PERSONA_CONTENT[interest]['authors']))
            )
            mixed_authors.extend(secondary_authors)
            
            # Add a subset of titles from secondary interest
            secondary_titles = random.sample(
                PERSONA_CONTENT[interest]['titles'],
                k=min(3, len(PERSONA_CONTENT[interest]['titles']))
            )
            mixed_titles.extend(secondary_titles)

        # Create favorite authors that will appear more frequently
        favorite_authors = random.sample(
            PERSONA_CONTENT[persona_type]['authors'],
            k=min(3, len(PERSONA_CONTENT[persona_type]['authors']))
        )

        # --- Data Generation ---
        saved_media = []
        media_likes = []
        videos_watched = []

        start_date = datetime.datetime(START_YEAR, START_MONTH, 1, tzinfo=datetime.timezone.utc)
        current_date = start_date
        
        # Create usage bursts - periods of higher activity
        burst_months = []
        for year in range(START_YEAR, END_DATETIME_UTC.year + 1):
            # Add 2-3 burst months per year
            num_bursts = random.randint(2, 3)
            for _ in range(num_bursts):
                burst_months.append((year, random.randint(1, 12)))

        while current_date <= END_DATETIME_UTC:
            year = current_date.year
            month = current_date.month
            month_start_dt = datetime.datetime(year, month, 1, tzinfo=datetime.timezone.utc)
            month_start_ts = int(month_start_dt.timestamp())

            # Calculate the end of the current period
            next_month_start_year = year + 1 if month == 12 else year
            next_month_start_month = 1 if month == 12 else month + 1
            next_month_start_dt = datetime.datetime(next_month_start_year, next_month_start_month, 1, tzinfo=datetime.timezone.utc)

            month_end_dt = min(next_month_start_dt, END_DATETIME_UTC)
            month_end_ts = max(month_start_ts, int(month_end_dt.timestamp()))

            # Only generate if the time window is valid
            if month_start_ts < month_end_ts:
                # Check if this is a burst month for higher activity
                is_burst_month = (year, month) in burst_months
                month_multiplier = 1.5 if is_burst_month else 1.0
                
                # Simulate increasing platform usage over time
                year_factor = min(1.5, 1 + (year - START_YEAR) * 0.1)  # Up to 50% increase over years
                
                # Calculate adjusted counts with all multipliers
                num_saves = random.randint(
                    int(NUM_SAVES_RANGE[0] * month_multiplier * year_factor),
                    int(NUM_SAVES_RANGE[1] * month_multiplier * year_factor)
                )
                num_likes = random.randint(
                    int(NUM_LIKES_RANGE[0] * month_multiplier * year_factor),
                    int(NUM_LIKES_RANGE[1] * month_multiplier * year_factor)
                )
                num_watches = random.randint(
                    int(NUM_WATCHES_RANGE[0] * month_multiplier * year_factor),
                    int(NUM_WATCHES_RANGE[1] * month_multiplier * year_factor)
                )

                # Generate timestamps within the month (accounting for weighted times)
                month_days = calendar.monthrange(year, month)[1]
                timestamps = []
                
                # Generate more timestamps than needed to account for weighted filtering
                for day in range(1, month_days + 1):
                    for _ in range(5):  # Generate multiple times per day
                        day_dt = datetime.datetime(year, month, day, 
                                                  random.randint(0, 23),  # Random hour
                                                  tzinfo=datetime.timezone.utc)
                        base_ts = int(day_dt.timestamp())
                        weighted_ts = weighted_timestamp(base_ts, day_dt.weekday())
                        if weighted_ts:
                            timestamps.append(weighted_ts)
                
                # Shuffle and take what we need
                random.shuffle(timestamps)
                
                # Determine which content to generate based on output filename
                # SECURITY FIX: Use safe_filename for pattern checking
                if 'saved_posts.json' in safe_filename:
                    # Generate Saves
                    for _ in range(min(num_saves, len(timestamps))):
                        ts = timestamps.pop() if timestamps else month_start_ts
                        title = random.choice(mixed_titles)
                        href = random_url()
                        saved_media.append({
                            "title": title,
                            "string_map_data": {
                                "Saved on": {
                                    "href": href,
                                    "timestamp": ts
                                }
                            }
                        })
                    
                elif 'liked_posts.json' in safe_filename:
                    # Generate Likes with higher probability for favorite authors
                    for _ in range(min(num_likes, len(timestamps))):
                        ts = timestamps.pop() if timestamps else random.randint(month_start_ts, month_end_ts - 1)
                        
                        # 40% chance to like content from a favorite author
                        if random.random() < 0.4 and favorite_authors:
                            title = random.choice(favorite_authors)
                        else:
                            title = random.choice(mixed_authors)
                            
                        href = random_url()
                        media_likes.append({
                            "title": title,
                            "string_list_data": [
                                {
                                    "href": href,
                                    "value": "Like", # Changed from emoji to text
                                    "timestamp": ts
                                }
                            ]
                        })
                
                elif 'videos_watched.json' in safe_filename:
                    # Generate Watches
                    for _ in range(min(num_watches, len(timestamps))):
                        ts = timestamps.pop() if timestamps else random.randint(month_start_ts, month_end_ts - 1)
                        
                        # 40% chance to watch content from a favorite author
                        if random.random() < 0.4 and favorite_authors:
                            author = random.choice(favorite_authors)
                        else:
                            author = random.choice(mixed_authors)
                            
                        videos_watched.append({
                            "string_map_data": {
                                "Time": {
                                    "timestamp": ts
                                },
                                "Author": {
                                    "value": author
                                }
                            }
                        })

            # Move to the next month for the loop
            current_date = next_month_start_dt

        # Shuffle lists to distribute entries non-chronologically (as in real data)
        random.shuffle(saved_media)
        random.shuffle(media_likes)
        random.shuffle(videos_watched)

        # Combine into the final structure
        # Only include relevant data based on the output filename
        final_data = {}
        
        # SECURITY FIX: Use safe_filename for pattern checking
        if 'saved_posts.json' in safe_filename:
            final_data["saved_saved_media"] = saved_media
        elif 'liked_posts.json' in safe_filename:
            final_data["likes_media_likes"] = media_likes
        elif 'videos_watched.json' in safe_filename:
            final_data["impressions_history_videos_watched"] = videos_watched

        # Save to file - use ensure_ascii=True to handle encoding issues
        output_json = json.dumps(final_data, indent=None, ensure_ascii=True)
        
        logger.info(f"Saving to file: {real_output_path}")
        try:
            with open(real_output_path, "w", encoding="utf-8") as f:
                f.write(output_json)
            logger.info(f"File saved successfully: {real_output_path}")
        except Exception as write_error:
            logger.error(f"Error writing file: {write_error}")
            raise
        
        # Return statistics with the data
        return {
            "data": final_data,
            "stats": {
                "total_saves": len(saved_media),
                "total_likes": len(media_likes),
                "total_watches": len(videos_watched),
                "persona_type": persona_type,
                "activity_level": activity_level,
                "secondary_interests": secondary_interests,
                "favorite_authors": favorite_authors,
                "date_range": f"{start_date.strftime('%Y-%m-%d')} to {END_DATETIME_UTC.strftime('%Y-%m-%d')}"
            }
        }
    
    except Exception as e:
        # SECURITY FIX: Don't expose detailed error information in the return value
        logger.error(f"An error occurred during JSON generation or saving: {e}")
        # Import secure logging functions
        from app.utils.logging_config import log_error_safely, log_stack_trace_safely
        
        log_error_safely(e, "Synthetic data generation", logger)
        log_stack_trace_safely(e, logger)
        return None