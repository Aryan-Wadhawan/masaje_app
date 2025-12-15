
import frappe
from frappe.utils import get_datetime, add_to_date
from datetime import datetime, timedelta
from frappe.utils import today, add_days, get_datetime

@frappe.whitelist(allow_guest=True)
def get_branches():
    return frappe.get_all("Branch", fields=["name"], ignore_permissions=True)

@frappe.whitelist(allow_guest=True)
def get_services(branch):
    """Fetch services and their prices for a specific branch."""
    # We join Item and Item Price
    items = frappe.db.sql("""
        SELECT i.name, i.item_name, i.description, ip.price_list_rate as price, i.image
        FROM `tabItem` i
        JOIN `tabItem Price` ip ON ip.item_code = i.name
        WHERE i.item_group IN ('Services', 'Packages') 
        AND ip.price_list = %s
    """, (branch,), as_dict=True)
    return items

@frappe.whitelist(allow_guest=True)
def get_available_slots(branch, date, service_item=None):
    """
    Returns available time slots based on Therapist Capacity.
    Capacity = Total Therapists Working - Active Bookings
    """
    date_obj = get_datetime(date)
    day_name = date_obj.strftime("%A")

    # 1. Get List of Therapists working at this Branch on this Day
    # Join Therapist Schedule with Employee to filter by Branch
    working_therapists = frappe.db.sql("""
        SELECT ts.therapist, ts.start_time, ts.end_time 
        FROM `tabTherapist Schedule` ts
        JOIN `tabEmployee` emp ON ts.therapist = emp.name
        WHERE ts.day_of_week = %s 
        AND emp.branch = %s
        AND ts.is_off = 0
        AND emp.status = 'Active'
    """, (day_name, branch), as_dict=True)

    if not working_therapists:
        return []

    # 2. Define Time Slots (e.g. 9am to 6pm)
    # Ideally derived from earliest start and latest end of therapists
    possible_slots = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
    
    available_slots = []

    # 3. Check Capacity for each slot
    for slot in possible_slots:
        # A. Count Total Capacity for this slot (Therapists working during this time)
        slot_time = get_datetime(f"{date} {slot}").time()
        
        # Simple check: Does slot fall within therapist's shift?
        # Note: strict inequality for end time if bookings are 1hr (start 16:00 needs shift ending > 17:00? or >= 17:00? 
        # Usually >= 17:00 if booking is 16:00-17:00. 
        # But here start/end in schedule are usually "09:00" and "18:00".
        # Let's say if shift is 9-18, 17:00 is valid start.
        
        total_capacity = 0
        for t in working_therapists:
             # Convert timedeltas to time objects if needed, or compare strings if format consistent
             # Frappe returns timedeltas usually for Time fields in SQL
             t_start = (datetime.min + t.start_time).time() if isinstance(t.start_time, timedelta) else get_datetime("2000-01-01 " + str(t.start_time)).time()
             t_end = (datetime.min + t.end_time).time() if isinstance(t.end_time, timedelta) else get_datetime("2000-01-01 " + str(t.end_time)).time()
             
             # Assuming 1 Hour Service duration for standard check
             booking_end_estimated = (datetime.combine(datetime.today(), slot_time) + timedelta(hours=1)).time()
             
             if t_start <= slot_time and t_end >= booking_end_estimated:
                 total_capacity += 1

        if total_capacity == 0:
            continue

        # B. Count Active Bookings at this slot + branch
        booked_count = frappe.db.count("Service Booking", {
            "booking_date": date,
            "branch": branch,
            "time_slot": slot,
            "status": ["in", ["Pending", "Approved"]]
        })

        # C. Compare
        if booked_count < total_capacity:
            available_slots.append(slot)

    return available_slots

@frappe.whitelist(allow_guest=True)
def create_booking(customer_name, phone, email, branch, items, date, time):
    # Items: List of service_items or single item?
    # Support both for compatibility
    import json
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except:
            items = [items] # Fallback if single string
            
    customer = frappe.get_value("Customer", {"mobile_no": phone}, "name")
    if not customer:
        customer_doc = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": customer_name,
            "mobile_no": phone,
            "email_id": email,
            "customer_type": "Individual",
            "customer_group": "All Customer Groups",
            "territory": "All Territories"
        })
        customer_doc.insert(ignore_permissions=True)
        customer = customer_doc.name
        
    # Calculate Total Duration
    total_duration = 0
    booking_items = []
    
    # Check price list for branch
    price_list = frappe.get_value("POS Profile", {"warehouse": ["like", f"%{branch}%"]}, "selling_price_list") or "Standard Selling"

    for service_item in items:
        # Get duration and price
        item_details = frappe.db.get_value("Item", service_item, ["item_name", "standard_rate", "description"], as_dict=True)
        # Check specific price
        price = frappe.get_value("Item Price", {"item_code": service_item, "price_list": price_list}, "price_list_rate")
        if not price: 
            price = item_details.standard_rate or 0
            
        # Duration - Assuming it's in a custom field or description?
        # For now, hardcode 60 for "60m" items, or fetch if we had a field. 
        # Let's revert to checking item name/desc or default 60.
        duration = 60 # Default
        if "30" in service_item: duration = 30
        if "90" in service_item: duration = 90
        
        total_duration += duration
        
        booking_items.append({
            "service_item": service_item,
            "service_name": item_details.item_name,
            "price": price,
            "duration_minutes": duration
        })

    # Calculate End Time
    start_str = f"{date} {time}"
    start_dt = get_datetime(start_str)
    end_dt = add_to_date(start_dt, minutes=total_duration)

    booking = frappe.get_doc({
        "doctype": "Service Booking",
        "customer": customer,
        "branch": branch,
        "service_item": items[0] if items else None, 
        "booking_date": date,
        "time_slot": time,
        "duration_minutes": total_duration,
        "start_datetime": start_dt,
        "end_datetime": end_dt,
        "items": booking_items,
        "status": "Pending"
    })
    
    booking.insert(ignore_permissions=True)
    
    return {"name": booking.name, "message": "Booking Created Successfully"}
