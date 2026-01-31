from datetime import datetime, timedelta
from db_config import get_db_connection

def is_overlapping(start_A, end_A, start_B, end_B):
    return start_A < end_B and end_A > start_B

def get_available_slots(centre_id, date_str):
    """
    Smart Slot Finder: Checks bookings for the given ID AND any other IDs 
    that share the same Name (handling Duplicate/Draft/Publish data issues).
    """
    conn = get_db_connection()
    bookings = []
    
    try:
        with conn.cursor() as cursor:
            # STEP 1: Get the Name of the requested center
            cursor.execute("SELECT post_title FROM wp_posts WHERE ID = %s", (centre_id,))
            result = cursor.fetchone()
            
            if not result:
                return [] # Center doesn't exist
            
            center_name = result['post_title']

            # STEP 2: Find ALL IDs that share this Name (Drafts, Private, Published, etc.)
            # This fixes the issue where bookings are on ID 2494 but we found ID 3175
            cursor.execute("SELECT ID FROM wp_posts WHERE post_title = %s", (center_name,))
            related_ids = [row['ID'] for row in cursor.fetchall()]
            
            if not related_ids:
                related_ids = [centre_id] # Fallback

            # STEP 3: Find bookings for ANY of these IDs
            # We use string formatting for the IN clause safely
            format_strings = ',' .join(['%s'] * len(related_ids))
            query = f"""
            SELECT slot_start, slot_end
            FROM tida_order_details
            WHERE product_id IN ({format_strings})
              AND DATE(slot_start) = %s
              AND order_status IN ('wc-completed', 'wc-processing', 'booking') 
            """
            # Note: I added 'booking' to status just in case your custom status is different
            
            params = tuple(related_ids) + (date_str,)
            cursor.execute(query, params)
            bookings = cursor.fetchall()
            
    finally:
        conn.close()

    # STEP 4: Calculate Free Slots (06:00 to 23:59)
    available_slots = []
    current_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Check 18 hours: 6 AM to 11 PM
    for hour in range(6, 24): 
        slot_start = current_date_obj.replace(hour=hour, minute=0, second=0)
        slot_end = slot_start + timedelta(hours=1)
        
        is_blocked = False
        
        for b in bookings:
            # Robust datetime conversion
            b_start = b['slot_start'] if isinstance(b['slot_start'], datetime) else datetime.strptime(str(b['slot_start']), "%Y-%m-%d %H:%M:%S")
            b_end = b['slot_end'] if isinstance(b['slot_end'], datetime) else datetime.strptime(str(b['slot_end']), "%Y-%m-%d %H:%M:%S")
            
            if is_overlapping(slot_start, slot_end, b_start, b_end):
                is_blocked = True
                break 
        
        if not is_blocked:
            available_slots.append({
                "raw_start": slot_start,
                "display": slot_start.strftime("%I:%M %p")
            })
            
    return available_slots