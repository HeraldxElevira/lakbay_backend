import psycopg2
from app.database.db import get_connection

destinations = [
    {
        "name": "Mount Apo National Park",
        "description": "The highest mountain in the Philippines, offering breathtaking panoramic views, diverse flora and fauna, and challenging trails for trekkers.",
        "lat": 6.9875,
        "lng": 125.2708,
        "estimated_cost": 5000.00,
        "vibes": "nature,adventure,hiking,mountain",
        "rating": 4.9
    },
    {
        "name": "Eden Nature Park & Resort",
        "description": "A beautiful mountain resort nestled at the foot of Mount Apo in Davao City, offering pine forests, organic gardens, and exciting outdoor adventures.",
        "lat": 7.0058,
        "lng": 125.4300,
        "estimated_cost": 1200.00,
        "vibes": "nature,relaxing,family,chill,cool",
        "rating": 4.7
    },
    {
        "name": "Dahican Beach",
        "description": "A stunning 7-kilometer stretch of white sand in Mati facing the Pacific Ocean, world-famous for skimboarding, surfing, and nesting sea turtles.",
        "lat": 6.9272,
        "lng": 126.3023,
        "estimated_cost": 1500.00,
        "vibes": "beach,adventure,surfing,nature,relaxing",
        "rating": 4.8
    },
    {
        "name": "Hagimit Falls",
        "description": "A lush, tropical oasis in Samal Island featuring multiple cascading waterfalls, natural swimming pools, and shaded campsites perfect for families.",
        "lat": 7.0869,
        "lng": 125.7066,
        "estimated_cost": 500.00,
        "vibes": "nature,relaxing,waterfalls,family,chill",
        "rating": 4.6
    },
    {
        "name": "Pearl Farm Beach Resort",
        "description": "An iconic premium resort on Samal Island with private white sand beaches, gorgeous over-water stilt houses, and stunning views of the Davao Gulf.",
        "lat": 7.1065,
        "lng": 125.6888,
        "estimated_cost": 12000.00,
        "vibes": "beach,luxury,relaxing,romantic,chill",
        "rating": 4.9
    },
    {
        "name": "Aliwagwag Falls Ecopark",
        "description": "Known as the highest cascading waterfall in the Philippines with 84 tiers of pristine river water surrounded by a lush protected rainforest.",
        "lat": 7.7342,
        "lng": 126.2947,
        "estimated_cost": 800.00,
        "vibes": "nature,waterfalls,sightseeing,adventure",
        "rating": 4.8
    },
    {
        "name": "Cape San Agustin",
        "description": "A scenic cape in Governor Generoso where the Davao Gulf meets the Pacific Ocean, featuring pinkish beaches, unique rock formations, and three historic lighthouses.",
        "lat": 6.2736,
        "lng": 126.1917,
        "estimated_cost": 2000.00,
        "vibes": "nature,adventure,sightseeing,historic,romantic",
        "rating": 4.7
    },
    {
        "name": "Kopiat Island",
        "description": "An pristine, uninhabited island sanctuary in Davao de Oro known for its crystal-clear turquoise waters, vibrant coral reefs, and sea turtle nesting grounds.",
        "lat": 7.3014,
        "lng": 125.8617,
        "estimated_cost": 1800.00,
        "vibes": "beach,nature,snorkeling,island,adventure",
        "rating": 4.6
    },
    {
        "name": "Lake Leonard",
        "description": "A peaceful caldera lake in Maco, Davao de Oro surrounded by thick rainforests, offering a quiet environment for camping, rafting, and bird watching.",
        "lat": 7.3828,
        "lng": 126.0494,
        "estimated_cost": 600.00,
        "vibes": "nature,relaxing,camping,lake,quiet",
        "rating": 4.5
    },
    {
        "name": "San Victor Island",
        "description": "A tiny 3-hectare paradise off the coast of Baganga with powdery white sand, turquoise waters, and a very quiet, serene atmosphere.",
        "lat": 7.5256,
        "lng": 126.5819,
        "estimated_cost": 1000.00,
        "vibes": "beach,nature,relaxing,island,quiet",
        "rating": 4.6
    },
    {
        "name": "Mount Hamiguitan Wildlife Sanctuary",
        "description": "A UNESCO World Heritage Site in San Isidro, Davao Oriental, famous for its unique pygmy bonsai forest and rich biodiversity of endangered flora and fauna.",
        "lat": 6.7264,
        "lng": 126.1833,
        "estimated_cost": 3000.00,
        "vibes": "nature,adventure,hiking,unesco,mountain",
        "rating": 4.8
    },
    {
        "name": "Malagos Garden Resort",
        "description": "A 12-hectare eco-tourism resort in Calinan, famous for its world-class chocolate museum, butterfly sanctuary, bird show, and beautiful orchid gardens.",
        "lat": 7.1842,
        "lng": 125.4217,
        "estimated_cost": 1200.00,
        "vibes": "nature,family,educational,food,chill",
        "rating": 4.6
    },
    {
        "name": "Jack's Ridge",
        "description": "A popular hilltop dining and historical spot in Davao City, offering a stunning panoramic view of the city lights and the gulf, located on a historic WWII site.",
        "lat": 7.0544,
        "lng": 125.5786,
        "estimated_cost": 800.00,
        "vibes": "urban,food,sightseeing,historic,nightlife",
        "rating": 4.5
    },
    {
        "name": "Crocodile Park & Zoo",
        "description": "A wildlife conservation park in Davao City showcasing crocodiles of all sizes, along with exotic birds, butterflies, reptiles, and local cultural shows.",
        "lat": 7.0983,
        "lng": 125.5978,
        "estimated_cost": 600.00,
        "vibes": "family,nature,educational,adventure",
        "rating": 4.4
    },
    {
        "name": "People's Park",
        "description": "A beautifully landscaped cultural park in the heart of Davao City featuring giant sculptures by artist Kublai Millan, dancing fountains, and lush gardens.",
        "lat": 7.0722,
        "lng": 125.6083,
        "estimated_cost": 100.00,
        "vibes": "urban,relaxing,park,culture,family,free",
        "rating": 4.5
    },
    {
        "name": "Isla Reta Beach (Talicud Island)",
        "description": "Located on Talicud Island behind Samal, Isla Reta offers a gorgeous stretch of fine white sand shaded by Talisay trees, and incredibly clear tropical waters.",
        "lat": 6.9806,
        "lng": 125.6881,
        "estimated_cost": 900.00,
        "vibes": "beach,snorkeling,camping,nature,chill",
        "rating": 4.7
    },
    {
        "name": "Haven's Peak Highland Resort",
        "description": "Perched on a hill in the cool highlands of Maragusan, Davao de Oro, offering crisp mountain breeze, fog-covered mornings, and lovely view of the valleys.",
        "lat": 7.3228,
        "lng": 126.1558,
        "estimated_cost": 1500.00,
        "vibes": "nature,relaxing,cool,mountain,chill",
        "rating": 4.6
    },
    {
        "name": "Tagbibinta Falls",
        "description": "A majestic 700-foot waterfall cascading in multiple tiers through the cool mountains of Maragusan, surrounded by rich greenery and walking paths.",
        "lat": 7.3478,
        "lng": 126.1367,
        "estimated_cost": 400.00,
        "vibes": "nature,waterfalls,adventure,hiking",
        "rating": 4.5
    },
    {
        "name": "Roxas Night Market",
        "description": "A bustling evening street food and shopping market in downtown Davao City, famous for charcoal-grilled delicacies, durian ice cream, and bargain finds.",
        "lat": 7.0706,
        "lng": 125.6128,
        "estimated_cost": 300.00,
        "vibes": "urban,food,shopping,nightlife,local",
        "rating": 4.6
    },
    {
        "name": "Sleeping Dinosaur Island Viewdeck",
        "description": "The iconic viewdeck along the highway in Mati, Davao Oriental, offering postcard views of a peninsula shaped like a sleeping dinosaur dipping into Pujada Bay.",
        "lat": 6.8533,
        "lng": 126.2300,
        "estimated_cost": 200.00,
        "vibes": "nature,sightseeing,adventure,romantic,quick_stop",
        "rating": 4.7
    }
]

def seed():
    conn = None
    cur = None
    try:
        print("Connecting to Neon PostgreSQL database...")
        conn = get_connection()
        cur = conn.cursor()
        
        print("Deleting existing destinations to avoid duplicates...")
        cur.execute("DELETE FROM destinations;")
        
        # Reset serial sequence if it exists so ids start at 1
        try:
            cur.execute("ALTER SEQUENCE destinations_destination_id_seq RESTART WITH 1;")
            print("Reset auto-increment sequence.")
        except Exception:
            # Table might not use standard serial sequence name or naming is different
            conn.rollback()
            cur = conn.cursor()
            print("Sequence reset skipped or failed (not critical).")
            
        print(f"Seeding {len(destinations)} high-quality Davao Region destinations...")
        for dest in destinations:
            cur.execute("""
                INSERT INTO destinations (name, description, lat, lng, estimated_cost, vibes, rating)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                dest["name"],
                dest["description"],
                dest["lat"],
                dest["lng"],
                dest["estimated_cost"],
                dest["vibes"],
                dest["rating"]
            ))
            
        conn.commit()
        print("Successfully seeded all Davao Region destinations!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    seed()
