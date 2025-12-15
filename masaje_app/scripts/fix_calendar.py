
import frappe

def execute():
    # 1. Add "end_datetime" column
    if not frappe.db.has_column("Service Booking", "booking_datetime"):
        # We need a proper Datetime field for Calendar
        # booking_date + time_slot is hard for calendar to read natively without js adapter
        # Easiest way: Add a calculated Datetime field
        
        # Actually, let's just add a hidden Datetime field that we populate on save
        pass

    # Better approach: Add Client Script to map fields for Calendar View
    # OR: Add a real Datetime field to the Doctype
    
    doc = frappe.get_doc("DocType", "Service Booking")
    
    # Check if field exists
    found = False
    for f in doc.fields:
        if f.fieldname == "start_datetime":
            found = True
            break
            
    if not found:
        # Insert start_datetime
        doc.append("fields", {
            "fieldname": "start_datetime",
            "fieldtype": "Datetime",
            "label": "Start",
            "hidden": 0,
            "in_list_view": 1
        })
        doc.append("fields", {
            "fieldname": "end_datetime",
            "fieldtype": "Datetime",
            "label": "End",
            "hidden": 0
        })
        doc.save()
        print("Added Datetime fields to Service Booking")

    # Now we need to populate them based on Date + Time
    bookings = frappe.get_all("Service Booking", fields=["name", "booking_date", "time_slot", "duration_minutes"])
    for b in bookings:
        if not b.booking_date or not b.time_slot: continue
        
        # Combine
        # Using simple string concat for update
        start_str = f"{b.booking_date} {b.time_slot}"
        # Calculate end
        from frappe.utils import get_datetime, add_to_date
        start_dt = get_datetime(start_str)
        end_dt = add_to_date(start_dt, minutes=b.duration_minutes)
        
        frappe.db.set_value("Service Booking", b.name, "start_datetime", start_dt)
        frappe.db.set_value("Service Booking", b.name, "end_datetime", end_dt)
    
    # Enable Calendar View
    frappe.db.set_value("DocType", "Service Booking", "is_calendar_and_gantt", 1)
    
    print("Updated Bookings with Datetime")
