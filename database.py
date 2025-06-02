import os
import logging
import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Database connection parameters
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/agri_bot")

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        # Parse DATABASE_URL for Heroku compatibility
        if DATABASE_URL.startswith("postgres://"):
            # Heroku uses postgres:// but psycopg needs postgresql://
            db_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        else:
            db_url = DATABASE_URL
            
        conn = psycopg.connect(db_url, row_factory=dict_row)
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def init_db():
    """Initialize the database schema. Ensures a clean advice table for initial data.
    WARNING: This will drop and recreate the 'advice' table on each startup.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as c:
                # Recreate advice table for a clean state matching initial_data logic
                c.execute('''DROP TABLE IF EXISTS advice CASCADE;''') # CASCADE to remove dependent objects like indexes
                c.execute('''
                    CREATE TABLE advice (
                        id SERIAL PRIMARY KEY,
                        query TEXT NOT NULL UNIQUE,
                        response TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        search_count INTEGER DEFAULT 1
                    );
                ''')
                logger.info("'advice' table recreated successfully.")

                # Create index for faster searches (on the newly created table)
                c.execute('''
                    CREATE INDEX idx_advice_query 
                    ON advice USING gin(to_tsvector('english', query));
                ''')
                
                # Create query logs table (usually want to keep this data)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS query_logs (
                        id SERIAL PRIMARY KEY,
                        user_query TEXT NOT NULL,
                        response_source VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                ''')
                logger.info("'query_logs' table ensured/created successfully.")
                
                conn.commit()
                
                # Synchronize initial data (inserts new, updates changed)
                insert_initial_data(conn) # This should now work reliably on the clean table
                    
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def insert_initial_data(conn):
    """Insert initial agricultural data for Lilongwe.
    If a query already exists (case-insensitive check), it updates the response if it's different.
    New queries are inserted.
    """
    initial_data = [
        ("What crops grow best in Lilongwe?", 
         "In Lilongwe, the following crops grow well:\n\n"
         "🌽 Maize - The staple crop, plant in November-December\n"
         "🥜 Groundnuts - Plant in December-January\n"
         "🌱 Tobacco - Major cash crop, nursery in September\n"
         "🫘 Beans - Plant in January-February\n"
         "🍠 Sweet potatoes - Plant with first rains\n"
         "🥔 Irish potatoes - Plant in cool months (May-July)\n\n"
         "These crops are well-suited to Lilongwe\'s climate with rainfall of 800-1000mm annually."),
        
        ("When is the best planting season in Lilongwe?",
         "The best planting seasons in Lilongwe are:\n\n"
         "🌧️ Main season: November to December (start of rains)\n"
         "☔ Late planting: January (for quick-maturing varieties)\n"
         "🌤️ Winter crops: May to July (irrigation needed)\n\n"
         "The rainy season typically runs from November to April, "
         "with peak rainfall in January-February. Plant with the first good rains!"),
        
        ("How to manage pests in maize?",
         "Common maize pest management strategies for Lilongwe:\n\n"
         "🐛 Fall Armyworm:\n"
         "• Scout fields weekly\n"
         "• Apply neem extract or approved pesticides\n"
         "• Plant early to avoid peak infestations\n\n"
         "🦗 Stalk borers:\n"
         "• Remove and burn crop residues\n"
         "• Use push-pull technology with Desmodium\n"
         "• Apply Bt-based bio-pesticides\n\n"
         "Prevention: Crop rotation, timely planting, and field hygiene are key!"),

        ("What are common soil types in Lilongwe and how to improve them?",
         "Lilongwe predominantly has Ferric Luvisols and Lixisols, which are moderately fertile but can be prone to nutrient leaching and acidity.\n\n"
         "Soil Improvement Tips:\n"
         "🌱 Organic Matter: Incorporate compost, animal manure, or green manures (e.g., cowpea, sunnhemp) to improve soil structure, water retention, and nutrient content.\n"
         "💚 Liming: Test soil pH. If acidic (pH < 5.5), apply agricultural lime as recommended by soil tests to neutralize acidity and improve nutrient availability.\n"
         "🔄 Crop Rotation: Rotate maize with legumes (beans, groundnuts, soyabeans) to improve soil fertility (nitrogen fixation) and break pest cycles.\n"
         "🌳 Agroforestry: Integrate fertilizer trees like Faidherbia albida or Gliricidia sepium to improve soil fertility and provide fodder.\n"
         "💧 Conservation Agriculture: Practice minimum tillage, retain crop residues on the soil surface, and use cover crops to reduce erosion and improve soil health."),

        ("How to control Striga (witchweed) in maize fields in Lilongwe?",
         "Striga (Kaufiti) is a major parasitic weed affecting maize in Lilongwe. Control strategies include:\n\n"
         "✋ Hand Weeding: Uproot Striga plants before they flower and set seed. This is labor-intensive but crucial.\n"
         "🎯 Trap Cropping: Plant crops like Desmodium (silverleaf or greenleaf) as an intercrop. Desmodium stimulates Striga germination but inhibits its attachment to maize roots.\n"
         "🌱 Tolerant/Resistant Varieties: Use maize varieties that are tolerant or resistant to Striga (e.g., IR-Maize varieties like MH30IR, MH39IR from Chitedze Research Station).\n"
         "🔗 Push-Pull Strategy: Intercrop maize with Desmodium and plant Napier grass around the field. Desmodium \'pushes\' away stemborers and \'pulls\' Striga, while Napier grass \'pulls\' stemborers.\n"
         "💊 Herbicide Coated Seed: Use Striga-resistant maize seed coated with herbicide (e.g., Imazapyr Resistant Maize - IRM) where available and recommended.\n"
         "💩 Manure Application: Apply well-decomposed animal manure to improve soil fertility, which can help reduce Striga infestation levels as healthier plants are more resilient."),

        ("What are some common tomato diseases in Lilongwe and their management?",
         "Common tomato diseases in Lilongwe include:\n\n"
         " blight (early and late):\n"
         "• Symptoms: Dark lesions on leaves, stems, and fruit. Late blight is very destructive.\n"
         "• Management: Use resistant varieties, ensure good air circulation (spacing, pruning), avoid overhead irrigation, apply fungicides (e.g., Mancozeb, Copper-based) preventatively, and practice crop rotation.\n\n"
         "🦠 Bacterial Wilt:\n"
         "• Symptoms: Rapid wilting of plants, often starting from the top, while leaves remain green. Vascular discoloration in stems.\n"
         "• Management: Very difficult to control. Use resistant varieties, avoid planting in infected soil for at least 3-4 years, improve soil drainage, and ensure tools are sanitized.\n\n"
         "🍂 Fusarium Wilt:\n"
         "• Symptoms: Yellowing and wilting of leaves, usually on one side of the plant or stem. Brown discoloration of vascular tissue.\n"
         "• Management: Plant resistant varieties, practice crop rotation, improve soil drainage, and maintain soil pH around 6.0-7.0."),
        
        ("Advice on irrigation methods for vegetable farming in Lilongwe during dry season?",
         "Effective irrigation during the dry season (May-October) is crucial for vegetables in Lilongwe:\n\n"
         "💧 Drip Irrigation: Highly efficient, delivers water directly to the plant roots, minimizing water loss. Requires an initial investment but saves water and can improve yields.\n"
         "🪴 Watering Cans: Suitable for small gardens or nurseries. Labor-intensive but allows precise watering.\n"
         "🌊 Furrow Irrigation (Trench): If water is abundant and land is gently sloped. Water flows in small channels between crop rows. Can lead to waterlogging if not managed well.\n"
         "⛲ Sprinkler Irrigation: Can be used but may lead to water loss through evaporation and can promote some fungal diseases if leaves stay wet for long. Best used early morning or late evening.\n\n"
         "Key Considerations:\n"
         "• Water Source: Ensure a reliable water source (borehole, dambo, river - check water rights).\n"
         "• Mulching: Apply organic mulch (e.g., dry grass, maize stalks) around plants to conserve soil moisture and reduce water needs.\n"
         "• Timing: Water early in the morning or late in the afternoon to reduce evaporation.")
    ]
    
    updated_count = 0
    inserted_count = 0
    
    try:
        with conn.cursor() as c:
            for query, response in initial_data:
                # Check if query already exists (case-insensitive)
                c.execute(
                    "SELECT id, response FROM advice WHERE LOWER(query) = LOWER(%s)",
                    (query,)
                )
                existing_entry = c.fetchone()
                
                if existing_entry:
                    # Entry exists, check if response is different
                    if existing_entry['response'] != response:
                        c.execute(
                            "UPDATE advice SET response = %s, created_at = CURRENT_TIMESTAMP WHERE id = %s",
                            (response, existing_entry['id'])
                        )
                        updated_count += 1
                else:
                    # Entry does not exist, insert new
                    c.execute(
                        "INSERT INTO advice (query, response) VALUES (%s, %s) ON CONFLICT (query) DO NOTHING",
                        (query, response)
                    )
                    # Check if insertion happened (PostgreSQL specific)
                    if c.rowcount > 0:
                        inserted_count += 1
            conn.commit()
            if inserted_count > 0:
                logger.info(f"Inserted {inserted_count} new initial records.")
            if updated_count > 0:
                logger.info(f"Updated {updated_count} existing initial records.")
            if inserted_count == 0 and updated_count == 0:
                logger.info("Initial data is already up to date.")
                
    except Exception as e:
        logger.error(f"Failed to insert/update initial data: {e}")

def search_db(query):
    """Search the database for relevant advice"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as c:
                # First try exact match (case-insensitive)
                c.execute(
                    "SELECT response FROM advice WHERE LOWER(query) = LOWER(%s)",
                    (query,)
                )
                result = c.fetchone()
                
                if result:
                    # Update search count
                    c.execute(
                        "UPDATE advice SET search_count = search_count + 1 WHERE LOWER(query) = LOWER(%s)",
                        (query,)
                    )
                    conn.commit()
                    log_query(query, "database")
                    return result['response']
                
                # Try fuzzy search using PostgreSQL text search
                c.execute('''
                    SELECT response, 
                           ts_rank(to_tsvector('english', query), plainto_tsquery('english', %s)) as rank
                    FROM advice 
                    WHERE to_tsvector('english', query) @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC
                    LIMIT 1
                ''', (query, query))
                
                result = c.fetchone()
                if result and result['rank'] > 0.1:  # Threshold for relevance
                    log_query(query, "database_fuzzy")
                    return result['response']
                
                # Try LIKE search as fallback
                keywords = query.split()
                for keyword in keywords:
                    if len(keyword) > 3:  # Skip short words
                        c.execute(
                            "SELECT response FROM advice WHERE query ILIKE %s LIMIT 1",
                            (f"%{keyword}%",)
                        )
                        result = c.fetchone()
                        if result:
                            log_query(query, "database_partial")
                            return result['response']
                
                return None
                
    except Exception as e:
        logger.error(f"Database search error: {e}")
        return None

def save_to_db(query, response):
    """Save a new query-response pair to the database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as c:
                # Check if similar query already exists
                c.execute(
                    "SELECT id FROM advice WHERE LOWER(query) = LOWER(%s)",
                    (query,)
                )
                
                if not c.fetchone():
                    c.execute(
                        "INSERT INTO advice (query, response) VALUES (%s, %s)",
                        (query, response)
                    )
                    conn.commit()
                    logger.info(f"Saved new Q&A pair: {query[:50]}...")
                else:
                    # Update existing response if needed
                    c.execute(
                        "UPDATE advice SET response = %s WHERE LOWER(query) = LOWER(%s)",
                        (response, query)
                    )
                    conn.commit()
                    logger.info(f"Updated existing Q&A pair: {query[:50]}...")
                    
    except Exception as e:
        logger.error(f"Failed to save to database: {e}")

def log_query(query, source):
    """Log queries for analytics"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as c:
                c.execute(
                    "INSERT INTO query_logs (user_query, response_source) VALUES (%s, %s)",
                    (query, source)
                )
                conn.commit()
    except Exception as e:
        logger.error(f"Failed to log query: {e}")

def get_popular_queries(limit=10):
    """Get most popular queries for analytics"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as c:
                c.execute('''
                    SELECT query, search_count 
                    FROM advice 
                    ORDER BY search_count DESC 
                    LIMIT %s
                ''', (limit,))
                return c.fetchall()
    except Exception as e:
        logger.error(f"Failed to get popular queries: {e}")
        return [] 