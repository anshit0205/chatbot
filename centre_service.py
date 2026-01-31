from db_config import get_db_connection

def find_nearby_centres(lat, lng, radius=100, limit=5): 
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            safe_limit = int(limit) if limit else 5
            
            # Fetch slightly more candidates (limit * 4) to allow for filterin
            query = """
            SELECT 
                p.ID as id,
                p.post_title,
                addr.meta_value as address,
                lat.meta_value as latitude,
                lng.meta_value as longitude,
                (
                    6371 * acos(
                        LEAST(1.0, GREATEST(-1.0,
                            cos(radians(%s)) * cos(radians(CAST(lat.meta_value AS DECIMAL(10,8)))) * cos(radians(CAST(lng.meta_value AS DECIMAL(11,8))) - radians(%s)) + 
                            sin(radians(%s)) * sin(radians(CAST(lat.meta_value AS DECIMAL(10,8))))
                        ))
                    )
                ) AS distance
            FROM wp_posts p
            INNER JOIN wp_postmeta lat ON p.ID = lat.post_id AND lat.meta_key = 'latitude'
            INNER JOIN wp_postmeta lng ON p.ID = lng.post_id AND lng.meta_key = 'longitude'
            LEFT JOIN wp_postmeta addr ON p.ID = addr.post_id AND addr.meta_key = 'address'
            WHERE p.post_type = 'product' 
            HAVING distance < %s
            ORDER BY distance ASC
            LIMIT %s; 
            """
            cursor.execute(query, (lat, lng, lat, radius, safe_limit * 4))
            
            raw_results = cursor.fetchall()
            unique_results = []
            seen_locations = set()
            
            for r in raw_results:
                try:
                    # FIX: Round to 3 decimal places (~100m precision)
                    # This merges entries that are basically in the same building/complex
                    r_lat = float(r['latitude'])
                    r_lng = float(r['longitude'])
                    loc_key = (round(r_lat, 3), round(r_lng, 3))
                    
                    if loc_key not in seen_locations:
                        unique_results.append(r)
                        seen_locations.add(loc_key)
                except:
                    continue

            return unique_results[:safe_limit]
    finally:
        conn.close()

# ... (Keep find_centre_by_name and get_total_academy_count exactly as they were) ...
def find_centre_by_name(name_query):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
            SELECT p.ID as id, p.post_title, m.meta_value as address
            FROM wp_posts p
            JOIN wp_postmeta m ON p.ID = m.post_id AND m.meta_key = 'address'
            WHERE p.post_type = 'product' 
            AND p.post_title LIKE %s
            LIMIT 1
            """
            cursor.execute(query, (f"%{name_query}%",))
            return cursor.fetchone()
    finally:
        conn.close()

def get_total_academy_count():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
            SELECT COUNT(DISTINCT post_title) as count 
            FROM wp_posts 
            WHERE post_type = 'product' AND post_status = 'publish'
            """
            cursor.execute(query)
            result = cursor.fetchone()
            return result['count'] if result else 0
    finally:
        conn.close()