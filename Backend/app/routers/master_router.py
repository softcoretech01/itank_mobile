from fastapi import APIRouter
from app.database import get_db_connection

router = APIRouter(prefix="/api/master", tags=["Master Data"])

@router.get("/all")
def get_all_masters():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.callproc("sp_GetAllMasters")
            
            # Fetch results set by set
            manufacturer = cursor.fetchall()
            
            cursor.nextset()
            standard = cursor.fetchall()
            
            cursor.nextset()
            tankcode_iso = cursor.fetchall()
            
            cursor.nextset()
            un__code = cursor.fetchall()
            
            cursor.nextset()
            design_temperature = cursor.fetchall()
            
            cursor.nextset()
            cabinet = cursor.fetchall()
            
            cursor.nextset()
            frame_type = cursor.fetchall()
            
            cursor.nextset()
            inspection_agency = cursor.fetchall()
            
            cursor.nextset()
            size = cursor.fetchall()
            
            cursor.nextset()
            pump = cursor.fetchall()
            
            cursor.nextset()
            mawp = cursor.fetchall()
            
            cursor.nextset()
            ownership = cursor.fetchall()
            
            cursor.nextset()
            products = cursor.fetchall()
            
            cursor.nextset()
            safety_valve_brands = cursor.fetchall()
            
            cursor.nextset()
            master_valves = cursor.fetchall()
            
            cursor.nextset()
            master_gauges = cursor.fetchall()
            
            cursor.nextset()
            pv_code = cursor.fetchall()

            cursor.nextset()
            evacuation_valve_type = cursor.fetchall()

            cursor.nextset()
            color_body_frame = cursor.fetchall()

            return {
                "manufacturer": manufacturer,
                "standard": standard,
                "tankcode_iso": tankcode_iso,
                "un__code": un__code,
                "design_temperature": design_temperature,
                "cabinet": cabinet,
                "frame_type": frame_type,
                "inspection_agency": inspection_agency,
                "size": size,
                "pump": pump,
                "mawp": mawp,
                "ownership": ownership,
                "products": products,
                "safety_valve_brands": safety_valve_brands,
                "master_valves": master_valves,
                "master_gauges": master_gauges,
                "pv_code": pv_code,
                "evacuation_valve_type": evacuation_valve_type,
                "color_body_frame": color_body_frame
            }
    finally:
        conn.close()