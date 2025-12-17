
import frappe
from frappe.utils import get_datetime, add_to_date, today, add_days, get_datetime
from typing import List, Dict, Any, Optional

@frappe.whitelist(allow_guest=True)
def get_branches():
    return frappe.get_all("Branch", fields=["name"], ignore_permissions=True)


def _resolve_price_list_for_branch(branch: Optional[str]) -> str:
    """
    Determine which price list to use for a given branch.

    Business rules:
    - Panglao branch uses "Panglao Prices".
    - All other branches use "Standard Selling".
    - If a POS Profile with a specific selling_price_list exists for a branch,
      it can still override this default mapping.
    """
    if not branch:
        return "Standard Selling"

    # Normalize for loose matching
    normalized = branch.lower()
    default_list = "Standard Selling"

    # 1) Hard rule: Panglao uses Panglao Prices
    if "panglao" in normalized:
        default_list = "Panglao Prices"

    # 2) POS Profile can still override (if configured)
    pos_price_list = frappe.db.get_value(
        "POS Profile",
        {"warehouse": ["like", f"%{branch}%"]},
        "selling_price_list",
    )
    return pos_price_list or default_list


def _is_item_available_for_branch(item: Dict[str, Any], branch: Optional[str]) -> bool:
    """
    Filter items based on availability tags in description.

    Convention used in Item.description:
    - e.g. "Sauna (Available at: Dao Branch, Panglao Branch only)"
    - If the text "Available at:" is present, the item is ONLY available at
      the listed branches.
    - If no such tag is present, the item is treated as available at all branches.
    """
    if not branch:
        # When branch is not specified, show global list
        return True

    description = (item.get("description") or "").strip()
    marker = "Available at:"

    if marker not in description:
        # No availability restriction => available everywhere
        return True

    # Extract the part after "Available at:"
    try:
        after_marker = description.split(marker, 1)[1]
    except IndexError:
        return True

    # Remove closing parenthesis or trailing "only" if present
    cleaned = after_marker.replace("only", "").replace(")", "").strip()

    # Split by comma to get individual branch names
    allowed_branches: List[str] = [b.strip() for b in cleaned.split(",") if b.strip()]
    if not allowed_branches:
        # If we cannot parse anything meaningful, don't hide the item
        return True

    branch_normalized = branch.lower()
    return any(b.lower() in branch_normalized or branch_normalized in b.lower() for b in allowed_branches)

@frappe.whitelist(allow_guest=True)
def get_services(branch=None):
    """Fetch services and their prices for a specific branch."""
    
    # 1. Determine Price List for Branch using explicit business rules
    price_list = _resolve_price_list_for_branch(branch)

    # 2. Fetch Services (Non-stock Sales Items) with Price for this list
    # We always use Item Price for the resolved list, but allow a standard_rate
    # fallback for safety (e.g. if an item is missing from the list).
    items: List[Dict[str, Any]] = frappe.db.sql(
        """
        SELECT 
            i.name,
            i.item_name,
            i.description,
            i.item_group,
            COALESCE(ip.price_list_rate, i.standard_rate, 0) as price,
            i.image
        FROM `tabItem` i
        LEFT JOIN `tabItem Price` ip
            ON ip.item_code = i.name
            AND ip.price_list = %s
        WHERE i.is_sales_item = 1 
          AND i.is_stock_item = 0
          AND i.disabled = 0
        ORDER BY i.item_name ASC
    """,
        (price_list,),
        as_dict=True,
    )

    # 3. Apply per-branch availability filtering based on description tags.
    #    This ensures items like Sauna are only shown for branches that are
    #    explicitly listed in "(Available at: ...)".
    filtered: List[Dict[str, Any]] = [
        item for item in items if _is_item_available_for_branch(item, branch)
    ]

    return filtered

@frappe.whitelist(allow_guest=True)
def get_therapists():
    """
    Get all active therapists (no branch filtering).
    Therapists can work at any branch.
    """
    return frappe.db.sql("""
        SELECT name, employee_name, cell_number
        FROM `tabEmployee`
        WHERE designation = 'Therapist' 
        AND status = 'Active'
        ORDER BY employee_name
    """, as_dict=True)


@frappe.whitelist(allow_guest=True)
def get_available_slots(branch, date, service_item=None):
    """
    Returns available time slots based on Therapist Capacity.
    Capacity = Total Active Therapists - Active Bookings
    Note: Therapists can work at any branch (no branch filtering).
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

    # 1. Get ALL active therapists (no branch/schedule filtering)
    # Therapists can work at any branch as per business requirement
    working_therapists = frappe.get_all("Employee",
        filters={"designation": "Therapist", "status": "Active"},
        fields=["name"],
        ignore_permissions=True
    )

    if not working_therapists:
        return []
    
    total_capacity = len(working_therapists)

    # 2. Define Time Slots (11am to 10pm based on operating hours)
    possible_slots = ["11:00", "12:00", "13:00", "14:00", "15:00", "16:00", 
                      "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]
    
    available_slots = []

    # 3. Check Capacity for each slot
    for slot in possible_slots:
        # Count Active Bookings at this slot + branch
        booked_count = frappe.db.count("Service Booking", {
            "booking_date": date,
            "branch": branch,
            "time_slot": slot,
            "status": ["in", ["Pending", "Approved"]]
        })

        # Remaining Capacity = Total Therapists - Booked Slots
        remaining_capacity = total_capacity - booked_count

        if remaining_capacity > 0:
            available_slots.append({
                "time": slot,
                "capacity": remaining_capacity
            })

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

    # Check if customer exists by phone number
    customer = frappe.get_value("Customer", {"mobile_no": phone}, "name")
    
    if not customer:
        # Check if customer name already exists to avoid "Renamed to..." message
        existing_name = frappe.db.get_value("Customer", customer_name, "name")
        final_customer_name = customer_name
        
        if existing_name:
            # Name taken (by someone with diff phone), so make it unique
            # Use Name + Last 4 digits of phone
            final_customer_name = f"{customer_name} ({phone[-4:]})"
            
        customer_doc = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": final_customer_name,
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
    
    # NOTE: POS Invoice is NOT created here (online bookings)
    # Workflow: 
    # 1. Online booking creates Service Booking (status: Pending)
    # 2. Receptionist reviews and changes status to 'Approved'
    # 3. Draft POS Invoice auto-created on approval (via on_update hook)
    # 4. Customer arrives, receptionist loads draft and checks out
    
    return {
        "name": booking.name, 
        "invoice": None,  # No invoice for online bookings
        "message": "Booking Created Successfully! Please wait for confirmation."
    }


@frappe.whitelist()
def search_pending_bookings(txt="", branch=None):
    """
    Search pending/approved bookings for POS.
    Used by the "Load Booking" link field in POS.
    Returns bookings from today onwards that are not yet completed/cancelled.
    """
    filters = {
        "status": ["in", ["Pending", "Approved", "In Progress"]],
        "booking_date": [">=", frappe.utils.today()]
    }
    
    # Filter by branch if provided (from user permission)
    if branch:
        filters["branch"] = branch
    
    # Text search on customer name or booking ID
    if txt:
        bookings = frappe.db.sql("""
            SELECT 
                sb.name,
                sb.customer,
                c.customer_name,
                sb.booking_date,
                TIME_FORMAT(sb.time_slot, '%%H:%%i') as time_slot,
                sb.therapist,
                e.employee_name as therapist_name,
                sb.status,
                sb.branch
            FROM `tabService Booking` sb
            LEFT JOIN `tabCustomer` c ON sb.customer = c.name
            LEFT JOIN `tabEmployee` e ON sb.therapist = e.name
            WHERE sb.status IN ('Pending', 'Approved', 'In Progress')
            AND sb.booking_date >= %(today)s
            AND (sb.name LIKE %(txt)s OR c.customer_name LIKE %(txt)s)
            ORDER BY sb.booking_date, sb.time_slot
            LIMIT 20
        """, {"today": frappe.utils.today(), "txt": f"%{txt}%"}, as_dict=True)
    else:
        bookings = frappe.db.sql("""
            SELECT 
                sb.name,
                sb.customer,
                c.customer_name,
                sb.booking_date,
                TIME_FORMAT(sb.time_slot, '%%H:%%i') as time_slot,
                sb.therapist,
                e.employee_name as therapist_name,
                sb.status,
                sb.branch
            FROM `tabService Booking` sb
            LEFT JOIN `tabCustomer` c ON sb.customer = c.name
            LEFT JOIN `tabEmployee` e ON sb.therapist = e.name
            WHERE sb.status IN ('Pending', 'Approved', 'In Progress')
            AND sb.booking_date >= %(today)s
            ORDER BY sb.booking_date, sb.time_slot
            LIMIT 20
        """, {"today": frappe.utils.today()}, as_dict=True)
    
    # Format for link field
    results = []
    for b in bookings:
        display = f"{b.time_slot} - {b.customer_name or b.customer}"
        if b.therapist_name:
            display += f" ({b.therapist_name})"
        results.append({
            "value": b.name,
            "description": display,
            "customer": b.customer,
            "customer_name": b.customer_name,
            "therapist": b.therapist,
            "therapist_name": b.therapist_name
        })
    
    return results


@frappe.whitelist()
def load_booking_for_pos(booking_name):
    """
    Load complete booking data for populating POS.
    Returns customer, therapist, and items.
    """
    if not booking_name:
        return {"error": "Booking name required"}
    
    booking = frappe.get_doc("Service Booking", booking_name)
    
    # Get customer info
    customer = frappe.get_doc("Customer", booking.customer)
    
    # Get therapist info
    therapist_name = None
    if booking.therapist:
        therapist_name = frappe.db.get_value("Employee", booking.therapist, "employee_name")
    
    # Get items
    items = []
    if booking.get("items"):
        for item in booking.items:
            item_doc = frappe.get_doc("Item", item.service_item)
            items.append({
                "item_code": item.service_item,
                "item_name": item_doc.item_name,
                "rate": item.price or 0,
                "qty": 1,
                "uom": item_doc.stock_uom or "Unit"
            })
    elif booking.service_item:
        item_doc = frappe.get_doc("Item", booking.service_item)
        items.append({
            "item_code": booking.service_item,
            "item_name": item_doc.item_name,
            "rate": 0,  # Will be fetched from price list in POS
            "qty": 1,
            "uom": item_doc.stock_uom or "Unit"
        })
    
    return {
        "booking_name": booking.name,
        "customer": booking.customer,
        "customer_name": customer.customer_name,
        "therapist": booking.therapist,
        "therapist_name": therapist_name,
        "branch": booking.branch,
        "items": items,
        "booking_date": str(booking.booking_date),
        "time_slot": str(booking.time_slot) if booking.time_slot else None
    }
