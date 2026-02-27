from app.database import get_db, engine
from sqlalchemy import text

def check_columns():
    with engine.connect() as conn:
        try:
            result = conn.execute(text("DESCRIBE tank_status"))
            print("Columns in tank_status:")
            for row in result:
                print(row)
        except Exception as e:
            print(f"Error describing tank_status: {e}")

if __name__ == "__main__":
    check_columns()
