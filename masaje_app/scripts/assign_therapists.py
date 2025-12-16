
import frappe

def run():
    print("--- Assigning Therapists to Bookings ---")
    
    # Get a therapist (EMP-00001 from prev check)
    t_id = frappe.db.get_value("Employee", {"status": "Active"}, "name")
    if not t_id:
        print("No Active Employee found.")
        return

    print(f"Assigning to Therapist: {t_id}")
    
    bookings = frappe.get_all("Service Booking", filters={"therapist": ("is", "not set")}, fields=["name"])
    
    for b in bookings:
        frappe.db.set_value("Service Booking", b.name, "therapist", t_id)
        print(f"Updated {b.name}")
        
    print(f"Assigned {len(bookings)} bookings.")
