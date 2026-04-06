from sqlalchemy import text
from datetime import datetime

class CopyInspectionService:
    @staticmethod
    def copy_inspection(db, inspection_id, new_inspection_type_id, current_user):
        from app.routers.tank_inspection_router import generate_report_number
        
        # 1. Fetch original inspection details
        orig_row = db.execute(
            text("SELECT * FROM tank_inspection_details WHERE inspection_id = :id"),
            {"id": inspection_id}
        ).fetchone()

        if not orig_row:
            raise ValueError("Original inspection not found")

        # Convert to dict
        if hasattr(orig_row, "_mapping"):
            orig_data = dict(orig_row._mapping)
        else:
            orig_data = dict(orig_row)

        # 2. Prepare new data
        new_data = orig_data.copy()
        
        # Remove fields that should be new
        fields_to_remove = [
            "inspection_id", "report_number", "created_at", "updated_at", 
            "is_submitted", "web_submitted", "is_reviewed", "reviewed_by",
            "inspection_type_id"
        ]
        for f in fields_to_remove:
            new_data.pop(f, None)

        # Update specific fields
        new_data["inspection_type_id"] = new_inspection_type_id
        now = datetime.now()
        new_data["inspection_date"] = now
        new_data["created_at"] = now
        new_data["updated_at"] = now
        
        # Reset status flags
        new_data["is_submitted"] = 0
        new_data["web_submitted"] = 0
        new_data["is_reviewed"] = 0
        new_data["reviewed_by"] = None
        
        # Safe user access
        if isinstance(current_user, dict):
            new_data["created_by"] = current_user.get("login_name", "System")
            new_data["emp_id"] = current_user.get("emp_id")
        else:
            new_data["created_by"] = getattr(current_user, "login_name", "System")
            new_data["emp_id"] = getattr(current_user, "emp_id", None)
            
        # Refetch pi_next_inspection_date in case it was updated in tank_certificate after the original inspection
        from app.routers.tank_inspection_router import fetch_pi_next_inspection_date
        pi_date = fetch_pi_next_inspection_date(db, new_data.get("tank_number"))
        if pi_date:
            new_data["pi_next_inspection_date"] = pi_date
        
        # Generate new report number
        new_report_number = generate_report_number(db, new_data["inspection_date"], inspection_type_id=new_data["inspection_type_id"])
        new_data["report_number"] = new_report_number

        # 3. Create new inspection record
        keys = list(new_data.keys())
        values_placeholders = [f":{k}" for k in keys]
        
        sql = f"""
            INSERT INTO tank_inspection_details ({", ".join(keys)})
            VALUES ({", ".join(values_placeholders)})
        """
        
        result = db.execute(text(sql), new_data)
        new_inspection_id = result.lastrowid

        # 4. Copy Checklist Items
        checklist_rows = db.execute(
            text("SELECT * FROM inspection_checklist WHERE inspection_id = :id"),
            {"id": inspection_id}
        ).fetchall()

        if checklist_rows:
            chk_keys = [
                "inspection_id", "tank_id", "emp_id", "job_id", "job_name", 
                "sub_job_id", "sub_job_description", "sn", "status_id", 
                "status", "comment", "image_id_assigned", "flagged"
            ]
            
            chk_values = []
            for row in checklist_rows:
                r = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
                chk_values.append({
                    "inspection_id": new_inspection_id,
                    "tank_id": r.get("tank_id") or new_data.get("tank_id"),
                    "emp_id": r.get("emp_id") or new_data.get("emp_id"),
                    "job_id": r.get("job_id"),
                    "job_name": r.get("job_name"),
                    "sub_job_id": r.get("sub_job_id"),
                    "sub_job_description": r.get("sub_job_description"),
                    "sn": r.get("sn"),
                    "status_id": r.get("status_id"),
                    "status": r.get("status"),
                    "comment": r.get("comment"),
                    "image_id_assigned": r.get("image_id_assigned"),
                    "flagged": r.get("flagged", 0)
                })
            
            if chk_values:
                chk_sql = f"""
                    INSERT INTO inspection_checklist ({", ".join(chk_keys)})
                    VALUES (:inspection_id, :tank_id, :emp_id, :job_id, :job_name, :sub_job_id, :sub_job_description, :sn, :status_id, :status, :comment, :image_id_assigned, :flagged)
                """
                db.execute(text(chk_sql), chk_values)

        # 5. Copy Tank Images
        image_rows = db.execute(
            text("SELECT * FROM tank_images WHERE inspection_id = :id"),
            {"id": inspection_id}
        ).fetchall()

        if image_rows:
            img_keys = [
                "inspection_id", "tank_number", "image_type", "image_path", 
                "thumbnail_path", "image_id", "emp_id", "created_date", 
                "is_marked", "is_assigned"
            ]
            img_values = []
            for row in image_rows:
                r = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
                img_values.append({
                    "inspection_id": new_inspection_id,
                    "tank_number": r.get("tank_number") or new_data.get("tank_number"),
                    "image_type": r.get("image_type"),
                    "image_path": r.get("image_path"),
                    "thumbnail_path": r.get("thumbnail_path"),
                    "image_id": r.get("image_id"),
                    "emp_id": r.get("emp_id") or new_data.get("emp_id"),
                    "created_date": r.get("created_date") or new_data.get("inspection_date"),
                    "is_marked": r.get("is_marked", 0),
                    "is_assigned": r.get("is_assigned", 0)
                })
            
            if img_values:
                img_sql = f"""
                    INSERT INTO tank_images ({", ".join(img_keys)})
                    VALUES (:inspection_id, :tank_number, :image_type, :image_path, :thumbnail_path, :image_id, :emp_id, :created_date, :is_marked, :is_assigned)
                """
                db.execute(text(img_sql), img_values)

        db.commit()
        return new_inspection_id, new_report_number
