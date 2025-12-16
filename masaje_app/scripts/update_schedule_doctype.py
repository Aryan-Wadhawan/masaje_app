import frappe

def update_schema():
    if not frappe.db.exists("DocType", "Therapist Schedule"):
        print("DocType not found.")
        return

    doc = frappe.get_doc("DocType", "Therapist Schedule")
    
    # Check if field exists
    field_exists = any(f.fieldname == 'branch' for f in doc.fields)
    
    if not field_exists:
        print("Adding 'branch' field...")
        doc.append("fields", {
            "fieldname": "branch",
            "fieldtype": "Link",
            "options": "Branch",
            "label": "Branch",
            "reqd": 1, # Make mandatory
            "in_list_view": 1,
            "insert_after": "therapist" 
        })
        doc.save()
        print("DocType updated successfully.")
    else:
        print("Field 'branch' already exists.")

    # Data Migration: Backfill existing schedules
    # (Since we made it mandatory, existing docs might have issues if we validate, 
    # but strictly in SQL they are just null until we fix them).
    
    print("Backfilling existing schedules...")
    # Default everything to "Bohol Main" for now, or fetch from Employee
    schedules = frappe.get_all("Therapist Schedule", filters={"branch": ["is", "not set"]}, fields=["name", "therapist"])
    
    count = 0
    for s in schedules:
        # Try to find employee's current branch
        branch = frappe.db.get_value("Employee", s.therapist, "branch")
        if not branch:
            branch = "Bohol Main" # Fallback
            
        frappe.db.set_value("Therapist Schedule", s.name, "branch", branch)
        count += 1
        
    frappe.db.commit()
    print(f"Backfilled {count} schedules.")

if __name__ == "__main__":
    frappe.connect()
    update_schema()
