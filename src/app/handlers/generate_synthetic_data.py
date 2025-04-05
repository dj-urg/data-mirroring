import json
import random
import time
import datetime
import calendar
import string
import os
from zoneinfo import ZoneInfo

# Persona-specific content dictionaries
PERSONA_CONTENT = {
    'career': {
        'authors': ['bloomberg_business', 'wall_street_journal', 'financial_times', 'career_coach_pro', 'exec_mentor', 'linkedin_news', 'harvard_biz_review', 'ted_talks', 'investopedia', 'forbes_finance', 'the_economist'],
        'titles': ['Market Analysis Q1 202X', 'Leadership Workshop Recap', 'Networking Strategies for Introverts', 'Investment Banking Trends', 'Guide to Your Next Promotion', 'Economic Outlook Update', 'FinTech Innovations']
    },
    'fitness': {
        'authors': ['brussels_runners', 'crossfit_capital', 'zen_flow_yoga', 'olympic_swimming_archive', 'nike_running', 'lululemon_eu', 'garmin_fitness', 'runners_world_mag', 'mens_health_mag', 'womens_health_mag', 'triathlon_life', 'strava_stories', 'peloton_cycle'],
        'titles': ['Marathon Training: Final Weeks', 'New CrossFit WOD Ideas', 'Advanced Vinyasa Flow', 'Swim Technique Drills', 'Best Running Shoes 202X Review', 'High-Protein Meal Prep', 'Race Day Checklist', 'Yoga for Recovery']
    },
    'traveler': {
        'authors': ['visitbrussels', 'cntraveler', 'travel_photo_world', 'lonely_planet', 'nomadic_matt', 'world_nomads', 'travel_channel', 'rick_steves', 'national_geographic_travel'],
        'titles': ['Hidden Gems of Europe', 'Budget Travel Tips', 'Sustainable Tourism', 'Off-the-Beaten-Path Destinations', 'Cultural Experiences Around the Globe', 'Adventure Travel Guide', 'Photography Travel Tips']
    },
    'foodie': {
        'authors': ['clean_eats_blog', 'good_food_guide', 'mindful_cooking', 'international_cuisine', 'vegan_delights', 'street_food_lover', 'michelin_guide', 'culinary_adventures', 'food_network'],
        'titles': ['Healthy & Quick Weeknight Dinners', 'Culinary World Tour', 'Sustainable Cooking Practices', 'Farm-to-Table Recipes', 'International Street Food Guide', 'Cooking Techniques Masterclass', 'Food Photography Tips']
    },
    'techie': {
        'authors': ['wired', 'techcrunch', 'the_verge', 'mit_technology_review', 'digital_trends', 'ars_technica', 'recode', 'cnet', 'engadget'],
        'titles': ['AI Breakthrough 202X', 'Emerging Tech Trends', 'Cybersecurity Insights', 'Future of Robotics', 'Innovation in Tech', 'Startup Ecosystem Report', 'Gadget Reviews']
    }
}

# Activity level mapping
ACTIVITY_MULTIPLIERS = {
    'low': 0.5,     # Occasional User
    'medium': 1.0,  # Regular User
    'high': 1.5     # Power User
}

def generate_synthetic_data(persona_type, activity_level, output_filename):
    """
    Generate synthetic Instagram data based on user inputs.
    
    :param persona_type: Type of persona (career, fitness, traveler, foodie, techie)
    :param activity_level: User's activity level (low, medium, high)
    :param output_filename: Filename to save the JSON data
    :return: Dictionary with generated data
    """
    # Configuration
    START_YEAR = 2015
    START_MONTH = 4
    END_DATETIME_UTC = datetime.datetime(2025, 4, 4, 14, 33, 6, tzinfo=datetime.timezone.utc)

    # Adjust ranges based on activity level
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.0)
    NUM_SAVES_RANGE = (int(2 * multiplier), int(6 * multiplier))
    NUM_LIKES_RANGE = (int(8 * multiplier), int(20 * multiplier))
    NUM_WATCHES_RANGE = (int(20 * multiplier), int(40 * multiplier))

    # Get persona-specific content
    persona_authors = PERSONA_CONTENT[persona_type]['authors']
    persona_titles = PERSONA_CONTENT[persona_type]['titles']

    def random_string(length=11):
        """Generate a random string often seen in URLs."""
        chars = string.ascii_lowercase + string.digits + '-' + '_'
        return ''.join(random.choice(chars) for _ in range(length))

    def generate_url():
        """Generate a fake Instagram URL."""
        base = random.choice(["https://www.instagram.com/p/", "https://www.instagram.com/reel/"])
        return base + random_string() + "/"

    # --- Data Generation ---
    saved_media = []
    media_likes = []
    videos_watched = []

    start_date = datetime.datetime(START_YEAR, START_MONTH, 1, tzinfo=datetime.timezone.utc)
    current_date = start_date

    print(f"Generating {persona_type} persona data from {start_date.strftime('%Y-%m-%d')} to {END_DATETIME_UTC.strftime('%Y-%m-%d %H:%M:%S %Z')}...")

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
            num_saves = random.randint(*NUM_SAVES_RANGE)
            num_likes = random.randint(*NUM_LIKES_RANGE)
            num_watches = random.randint(*NUM_WATCHES_RANGE)

            # Generate Saves
            for _ in range(num_saves):
                ts = random.randint(month_start_ts, max(month_start_ts, month_end_ts - 1))
                title = random.choice(persona_titles)
                href = generate_url()
                saved_media.append({
                    "title": title,
                    "string_map_data": {
                        "Saved on": {
                            "href": href,
                            "timestamp": ts
                        }
                    }
                })

            # Generate Likes
            for _ in range(num_likes):
                ts = random.randint(month_start_ts, max(month_start_ts, month_end_ts - 1))
                title = random.choice(persona_authors)
                href = generate_url()
                media_likes.append({
                    "title": title,
                    "string_list_data": [
                        {
                            "href": href,
                            "value": "\ud83d\udc4d", # Unicode for 👍
                            "timestamp": ts
                        }
                    ]
                })

            # Generate Watches
            for _ in range(num_watches):
                ts = random.randint(month_start_ts, max(month_start_ts, month_end_ts - 1))
                author = random.choice(persona_authors)
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

    # Shuffle lists to distribute entries non-chronologically
    random.shuffle(saved_media)
    random.shuffle(media_likes)
    random.shuffle(videos_watched)

    # Combine into the final structure
    final_data = {
        "saved_saved_media": saved_media,
        "likes_media_likes": media_likes,
        "impressions_history_videos_watched": videos_watched
    }

    # Save to file
    try:
        output_json = json.dumps(final_data, indent=None, ensure_ascii=False)
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(output_json)
        
        print(f"Data saved to {output_filename}")
        print(f"\nGenerated {len(saved_media)} saves, {len(media_likes)} likes, {len(videos_watched)} watches.")
        
        output_size_bytes = os.path.getsize(output_filename)
        output_size_mb = output_size_bytes / (1024 * 1024)
        print(f"Final file size: {output_size_mb:.2f} MB")
        
        return final_data
    
    except Exception as e:
        print(f"An error occurred during JSON generation or saving: {e}")
        return None

# This allows the script to be imported without automatically running
if __name__ == "__main__":
    # Example usage when run directly
    generate_synthetic_data('career', 'medium', 'liked_posts.json')