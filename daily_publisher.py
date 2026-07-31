import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Beach Vibes and Sunshine — Life in Paradise",
        "Tropical Style for Your Next Getaway",
        "Chasing Sunshine: Travel Moments to Live For",
        "Brazilian Fashion Inspiration for Summer",
        "Island Living — Simpler, Brighter, Better",
        "Pack Light, Live Bright: Travel Tips",
        "The Beauty of Living With Passion",
        "Your Daily Dose of Sunshine and Adventure",
        "Beach Looks That Turn Heads",
        "Find Your Happy Place — Travel and Dream",
        "Tropical Life Lessons From the Coast",
        "Summer Style With a Brazilian Soul",
        "Wander Often, Wonder Always",
        "Confidence, Beauty and Island Adventure",
        "Escape to Paradise — Even for a Moment",
    ]

    fallback_descriptions = [
        "There's something magical about the ocean — the sound of waves, the warmth of the sun, the feeling of sand between your toes. Life slows down by the beach, and suddenly everything feels brighter. Whether you're planning a getaway or dreaming from home, bring a little paradise into your day. Drop a 🌊 if you're a beach soul! #beachvibes #travel #sunshine #islandliving #tropicalstyle #amorasolis",
        "Brazilian style is all about color, confidence, and joy. Flowing fabrics, bold prints, and effortless silhouettes made for warm days and golden sunsets. Dress like every day is a summer day and watch your energy transform. Save these looks for your next trip! 🌺 #brazilianfashion #summerstyle #tropicalstyle #beachoutfit #fashioninspo #amorasolis",
        "Chasing sunshine is a mindset, not just a destination. Find beauty in the ordinary, take the scenic route, and make time for the moments that make you feel alive. Adventure is out there — you just have to go. Comment your dream destination below! ✈️ #chasingsunshine #travel #adventure #wanderlust #lifestyle #amorasolis",
        "Island living teaches you the art of slowing down. Mornings by the water, afternoons in the shade, evenings painted in gold. It's not about escaping life — it's about living it fully. Take a breath, and remember what matters. Like if you crave island life! 🏝️ #islandliving #slowliving #beachlife #travel #mindfulness #amorasolis",
        "The best travel memories aren't the photos — they're the feelings. The laughter, the sunsets, the people you meet along the way. Collect experiences, not things. This is your reminder to book that trip. Share this with your travel buddy! 🌅 #travelmemories #travelinspo #adventure #wanderlust #experiencenotthings #amorasolis",
        "Confidence looks good in any language. Own your style, walk tall, and let your inner light shine — whether you're on a beach in Brazil or in your hometown. Beauty is an attitude, and adventure begins the moment you believe in yourself. Drop a 💛 if you're ready to live boldly! #confidence #selflove #beauty #adventure #empowerment #amorasolis",
        "Tropical fashion is a celebration of color and life. Vibrant prints, breezy linen, and accessories that catch the sun — it's joyful, expressive, and made to be worn with a smile. Let your wardrobe bring you joy every single day. Double tap if you love tropical prints! 🌴 #tropicalstyle #colorfulfashion #brazilianfashion #summerstyle #fashionjoy #amorasolis",
        "You don't need a passport to embrace island energy. Bring the beach home — lighter meals, brighter colors, more time outside, and a slower pace. Small shifts create a whole new vibe. Save this for when you need a little sunshine! ☀️ #beachvibes #lifestyle #selfcare #summer #positiveenergy #amorasolis",
        "Every sunset is a reminder that endings can be beautiful — and that tomorrow brings a new day full of possibility. Watch the sky, breathe deep, and trust the journey. You're exactly where you're meant to be. Like if you needed this today. 🌇 #sunset #gratitude #mindset #hopeful #travel #amorasolis",
        "Adventure doesn't have to be extreme — it can be a new trail, a hidden café, or a road trip with no plans. The point is to stay curious and keep exploring. The world is full of beautiful moments waiting for you. Comment your next adventure below! 🗺️ #adventure #explore #travel #curiosity #lifestyle #amorasolis",
        "Living life with passion and purpose means choosing joy every day. Follow what lights you up, surround yourself with good energy, and let your passion guide your path. You were made for more than ordinary. Drop a 🔥 if you're living with purpose! #passion #purpose #lifewithmeaning #motivation #braziliangirl #amorasolis",
        "A packing list for the sun-chaser: light fabrics, one great pair of sandals, a good book, and an open mind. Travel light and you'll move through the world with ease. Ready to wander? Save this for your next getaway! 🧳 #packinglist #travelhacks #traveltips #beachgetaway #wanderlust #amorasolis",
        "Brazilian beauty is about sun, sea, and self-love. Glowing skin, natural hair, and a radiant smile — confidence is the most beautiful accessory. Embrace your natural beauty and let it shine. Double tap if you love your natural glow! 💫 #brazilianbeauty #naturalbeauty #selflove #glow #confidence #amorasolis",
        "Some of the best moments happen when you say yes to the unexpected. Say yes to the spontaneous trip, the new friendship, the sunset detour. Life rewards the brave. Share this with someone who always says yes to adventure! ✨ #sayyes #adventure #spontaneity #travel #lifewelllived #amorasolis",
        "Paradise is a feeling you carry with you. Even on busy days, you can find a moment of calm — a deep breath, a warm cup, a song that takes you to the coast. Bring paradise wherever you go. Like if you needed this reminder. 🌺 #paradisestateofmind #beachvibes #mindfulness #positivity #amorasolis",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "bright and joyful — speak like a sun-loving Brazilian adventurer",
        "warm and breezy — make viewers feel like they're on a tropical vacation",
        "bold and colorful — celebrate vibrant style and living life to the fullest",
        "inspiring and adventurous — motivate viewers to explore and chase sunshine",
        "relaxed and easygoing — emphasise beach energy and island living",
        "passionate and purposeful — inspire confidence and living with intention",
        "glowing and empowering — celebrate natural beauty and self-love",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Amora Solis'. "
        f"The page covers Brazilian fashion, travel, and lifestyle - chasing sunshine and beautiful moments. It celebrates beach vibes, tropical style, and island living, inspiring confidence, beauty, and adventure, and living life with passion and purpose. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if this took you to the beach! Comment your dream destination below! Share this with your travel buddy! Follow Amora Solis for daily sunshine and travel inspiration!"
        f"Include relevant hashtags in ALL LOWERCASE such as #brazilianfashion #travel #lifestyle #beachvibes #tropicalstyle #islandliving #sunshine #adventure #confidence #beauty #travelinspo #summer #breezy #amorasolis. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["brazilianfashion", "travel", "lifestyle", "beachvibes", "tropicalstyle", "islandliving", "sunshine", "adventure", "confidence", "travelinspo", "summer", "beach", "wanderlust", "amorasolis"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
