from app.database import get_db_connection, DB_NAME
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_product_id_column():
    conn = get_db_connection(use_db=True)
    try:
        with conn.cursor() as cursor:
            # 1. Check current column type
            cursor.execute(
                "SELECT DATA_TYPE FROM information_schema.columns "
                "WHERE table_schema=%s AND table_name='tank_details' AND column_name='product_id'",
                (DB_NAME,)
            )
            result = cursor.fetchone()
            if result:
                current_type = result['DATA_TYPE'].lower()
                logger.info(f"Current type of tank_details.product_id: {current_type}")
                
                if current_type != 'text':
                    logger.info("Altering column tank_details.product_id to TEXT...")
                    # Note: We use TEXT to support long comma-separated strings of IDs
                    cursor.execute("ALTER TABLE tank_details MODIFY COLUMN product_id TEXT")
                    conn.commit()
                    logger.info("Successfully altered column to TEXT.")
                else:
                    logger.info("Column is already TEXT.")
            else:
                logger.error("Column tank_details.product_id not found!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_product_id_column()
