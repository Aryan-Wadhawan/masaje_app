
import frappe
from frappe.utils import get_datetime, add_to_date
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
def get_available_slots(branch, date, service_item):
    """
    Returns available time slots for a given date and service.
    For MVP, we return a fixed set of slots if they aren't fully booked.
    Real logic would cross-reference Therapist Schedule and valid Employee for that Branch.
    """
    # 1. Determine Day of Week
    date_obj = get_datetime(date)
    day_name = date_obj.strftime("%A")

    # 2. Get Therapists working on this day
    # Assuming ANY therapist can do the service for now
    schedules = frappe.get_all("Therapist Schedule", 
        filters={"day_of_week": day_name, "is_off": 0},
        fields=["therapist", "start_time", "end_time"],
        ignore_permissions=True
    )
    
    if not schedules:
        return []

    # Mock availability: Fixed slots
    # In real world, we would subtract existing bookings from these slots.
    possible_slots = ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"]
    
    # Check existing bookings for this branch on this date
    booked_slots = frappe.get_all("Service Booking", 
        filters={"booking_date": date, "branch": branch, "status": ["in", ["Pending", "Approved"]]},
        pluck="time_slot",
        ignore_permissions=True
    )
    
    # Convert timedeltas to string HH:MM
    booked_slots_str = [str(t)[:5] for t in booked_slots]
    
    available = [s for s in possible_slots if s not in booked_slots_str]
    return available

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
