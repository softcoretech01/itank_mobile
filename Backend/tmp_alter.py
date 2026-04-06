from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE tank_valve_and_shell ADD COLUMN status SMALLINT DEFAULT 1"))
        conn.commit()
        print("Successfully added status column.")
    except Exception as e:
        print(f"Error (maybe column already exists?): {e}")
