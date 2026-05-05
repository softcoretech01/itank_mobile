from app.database import get_db_connection, DB_NAME
from app.utils.s3_utils import CLOUDFRONT_BASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_recursive_urls():
    if not CLOUDFRONT_BASE_URL:
        logger.info("CLOUDFRONT_BASE_URL not set. Skipping cleanup.")
        return

    conn = get_db_connection(use_db=True)
    try:
        with conn.cursor() as cursor:
            # Find rows with the prefix
            cursor.execute(
                "SELECT id, tank_number_image_path FROM tank_details "
                "WHERE tank_number_image_path LIKE %s",
                (f"%{CLOUDFRONT_BASE_URL}%",)
            )
            rows = cursor.fetchall()
            
            if not rows:
                logger.info("No recursive URLs found in tank_details.")
                return

            logger.info(f"Found {len(rows)} rows to clean up.")
            
            for row in rows:
                row_id = row['id']
                original_path = row['tank_number_image_path']
                
                # Strip all occurrences of the base URL
                cleaned_path = original_path.replace(CLOUDFRONT_BASE_URL, "").lstrip("/")
                # Also handle potentially nested paths like uploads/uploads/
                # but focus on the CDN URL for now
                
                logger.info(f"Cleaning row {row_id}: {original_path[:50]}... -> {cleaned_path}")
                
                cursor.execute(
                    "UPDATE tank_details SET tank_number_image_path=%s WHERE id=%s",
                    (cleaned_path, row_id)
                )
            
            conn.commit()
            logger.info("Successfully cleaned up recursive URLs.")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_recursive_urls()
