
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

    # Determine Duration
    # Helper logic similar to create_booking
    import json
    items = service_item
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except:
            items = [items] if items else []
            
    total_duration = 0
    if not items:
        total_duration = 60 # Default for slot viewing
    else:
        for item in items:
            # Quick check for duration in name/desc or default
            duration = 60
            if "30" in str(item): duration = 30
            if "90" in str(item): duration = 90
            total_duration += duration

    # 1. Get List of Therapists working at this Branch on this Day
    # Filter Schedules directly by branch (Dynamic Branching)
    working_therapists = frappe.db.sql("""
        SELECT ts.therapist, ts.start_time, ts.end_time 
        FROM `tabTherapist Schedule` ts
        JOIN `tabEmployee` emp ON ts.therapist = emp.name
        WHERE ts.day_of_week = %s 
        AND ts.branch = %s
        AND ts.is_off = 0
        AND emp.status = 'Active'
    """, (day_name, branch), as_dict=True)

    if not working_therapists:
        return []

    # 2. Define Time Slots (e.g. 9am to 6pm)
    possible_slots = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
    
    available_slots = []

    # 3. Check Capacity for each slot
    for slot in possible_slots:
        # A. Count Total Capacity for this slot (Therapists working during this time)
        slot_time = get_datetime(f"{date} {slot}").time()
        
        # Calculate expected end time based on DURATION
        booking_end_estimated = (datetime.combine(datetime.today(), slot_time) + timedelta(minutes=total_duration)).time()

        total_capacity = 0
        for t in working_therapists:
             t_start = (datetime.min + t.start_time).time() if isinstance(t.start_time, timedelta) else get_datetime("2000-01-01 " + str(t.start_time)).time()
             t_end = (datetime.min + t.end_time).time() if isinstance(t.end_time, timedelta) else get_datetime("2000-01-01 " + str(t.end_time)).time()
             
             # Check if therapist shift COVERS the entire booking duration
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
    # Validation: Past Date
    if get_datetime(date).date() < get_datetime(today()).date():
        frappe.throw("Cannot book appointments in the past!", frappe.ValidationError)

    # Items: List of service_items or single item?
    import json
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except:
            items = [items] # Fallback if single string
            
    if not items:
         frappe.throw("No service selected!", frappe.ValidationError)

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
        
        if not item_details:
             frappe.throw(f"Item {service_item} not found!", frappe.ValidationError)

        # Check specific price
        price = frappe.get_value("Item Price", {"item_code": service_item, "price_list": price_list}, "price_list_rate")
        if not price: 
            price = item_details.standard_rate or 0
            
        # Duration logic
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
    
    # --- POS Integration: Auto-create Draft Order ---
    invoice_name = None
    
    # Switch to Administrator to bypass permission checks for POS creation (Guest user issue)
    current_user = frappe.session.user
    frappe.set_user("Administrator")
    
    try:
        # Re-fetch POS Profile name to be sure
        pos_profile_name = frappe.db.get_value("POS Profile", {"warehouse": ["like", f"%{branch}%"]}, "name")
        
        if pos_profile_name:
            # Fetch Linked Data
            profile_doc = frappe.get_doc("POS Profile", pos_profile_name)
            cost_center = frappe.db.get_value("Branch", branch, "default_cost_center")
            
            # Create Invoice
            pos_inv = frappe.new_doc("POS Invoice")
            pos_inv.customer = customer
            pos_inv.pos_profile = pos_profile_name
            pos_inv.company = "Masaje de Bohol" 
            pos_inv.posting_date = date 
            pos_inv.branch = branch 
            pos_inv.update_stock = profile_doc.update_stock 
            
            # Commission Logic (Simple 10% for now)
            total_comm = 0.0
            item_wh = frappe.db.get_value("POS Profile", pos_profile_name, "warehouse")
            
            for item in booking_items:
                item_comm = item["price"] * 0.10
                total_comm += item_comm
                
                pos_inv.append("items", {
                    "item_code": item["service_item"],
                    "qty": 1,
                    "rate": item["price"],
                    "uom": "Unit", 
                    "conversion_factor": 1,
                    "warehouse": item_wh,
                    "cost_center": cost_center 
                })
            
            # Sales Team Logic (Standard Commission)
            if booking.therapist:
                sales_person = frappe.db.get_value("Sales Person", {"employee": booking.therapist, "enabled": 1})
                if sales_person:
                    pos_inv.append("sales_team", {
                        "sales_person": sales_person,
                        "allocated_percentage": 100,
                    })
            
            pos_inv.set_missing_values() 
            pos_inv.docstatus = 0 
            pos_inv.insert(ignore_permissions=True)
            invoice_name = pos_inv.name
            
            # Update Booking with commission and invoice link
            frappe.db.set_value("Service Booking", booking.name, {
                "commission_amount": total_comm,
                "invoice": invoice_name
            })
        else:
            frappe.log_error(f"POS Profile not found for branch: {branch}", "Masaje Booking")
            
    except Exception as e:
        frappe.log_error(f"POS Creation Failed: {str(e)}", "Masaje Booking")
        print(f"POS Creation Error: {e}")

    finally:
        frappe.set_user(current_user)

    return {"name": booking.name, "invoice": invoice_name, "message": "Booking Created Successfully"}
