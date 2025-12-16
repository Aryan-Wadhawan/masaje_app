
import frappe
from masaje_app.utils import create_pos_invoice_for_booking


def on_service_booking_validate(doc, method):
    """
    Auto-calculate duration_minutes from items table on server-side.
    This is a fallback in case client script doesn't run.
    """
    # Calculate total duration from items
    total_duration = 0
    if doc.items:
        for item in doc.items:
            total_duration += (item.duration_minutes or 0)
    
    # Set duration if calculated from items
    if total_duration > 0:
        doc.duration_minutes = total_duration
    elif not doc.duration_minutes:
        # Default to 60 minutes if no items and no duration set
        doc.duration_minutes = 60


def on_service_booking_insert(doc, method):

    """
    Create draft POS Invoice when Service Booking is created via Desk.
    This handles walk-in customers where receptionist creates booking manually.
    
    Note: Online bookings via api.py create their own invoice, so this checks
    if invoice is already linked to avoid duplicates.
    """
    # Skip if invoice already exists (e.g., created by api.py)
    if doc.invoice:
        return
    
    # Skip if no customer - booking incomplete
    if not doc.customer:
        return
        
    # Skip if status is Cancelled
    if doc.status == "Cancelled":
        return
    
    # Create the draft POS Invoice
    invoice_name = create_pos_invoice_for_booking(doc)
    
    if invoice_name:
        frappe.msgprint(
            f"Draft POS Invoice <a href='/app/pos-invoice/{invoice_name}'>{invoice_name}</a> created.",
            alert=True
        )


def on_service_booking_update(doc, method):
    """
    Handle Service Booking updates - sync with linked POS Invoice if needed.
    """
    # If booking is cancelled and has an invoice, we might want to cancel the draft
    if doc.status == "Cancelled" and doc.invoice:
        # Check if invoice is still in draft
        invoice_status = frappe.db.get_value("POS Invoice", doc.invoice, "docstatus")
        if invoice_status == 0:  # Draft
            frappe.msgprint(
                f"Note: Draft POS Invoice {doc.invoice} exists for this cancelled booking. "
                "Please delete it manually if not needed.",
                alert=True
            )


def on_service_booking_trash(doc, method):
    """
    When Service Booking is deleted, also delete linked draft POS Invoice.
    Submitted invoices cannot be deleted automatically.
    """
    if doc.invoice:
        invoice_status = frappe.db.get_value("POS Invoice", doc.invoice, "docstatus")
        if invoice_status == 0:  # Draft
            # Delete the draft invoice
            frappe.delete_doc("POS Invoice", doc.invoice, ignore_permissions=True)
            frappe.msgprint(
                f"Draft POS Invoice {doc.invoice} also deleted.",
                alert=True
            )
        else:
            # Submitted invoice - just unlink and notify
            frappe.msgprint(
                f"Note: POS Invoice {doc.invoice} is submitted and cannot be auto-deleted.",
                alert=True
            )


def on_pos_invoice_submit(doc, method):

    """
    When POS Invoice is submitted:
    1. If booking exists: sync new items from POS to booking (append only)
    2. If no booking: create new booking (reverse sync for walk-ins)
    3. Calculate and store commission if therapist is set
    """
    from frappe.utils import now_datetime, add_to_date
    
    # First check if a Service Booking already exists for this invoice
    linked_booking = frappe.db.get_value(
        "Service Booking", 
        {"invoice": doc.name}, 
        "name"
    )
    
    if linked_booking:
        # Booking exists - sync any new items from POS (append only)
        sync_pos_items_to_booking(doc, linked_booking)
    else:
        # No booking exists - create one (reverse sync)
        linked_booking = create_service_booking_from_invoice(doc)
    
    # Now handle commission calculation
    therapist = doc.get("therapist")
    if therapist:
        calculate_and_store_commission(doc, therapist, linked_booking)


def on_pos_invoice_cancel(doc, method):
    """
    When POS Invoice is cancelled, revert linked Service Booking to Pending.
    This allows the booking to be re-processed with a new invoice.
    """
    # Find any Service Booking linked to this invoice
    linked_booking = frappe.db.get_value(
        "Service Booking", 
        {"invoice": doc.name}, 
        "name"
    )
    
    if linked_booking:
        # Revert booking status to Pending and clear invoice link
        frappe.db.set_value("Service Booking", linked_booking, {
            "invoice": None,
            "status": "Pending",
            "commission_amount": 0
        })
        frappe.msgprint(
            f"<a href='/app/service-booking/{linked_booking}'>{linked_booking}</a> reverted to Pending.",
            alert=True
        )


def on_pos_invoice_trash(doc, method):
    """
    When POS Invoice is deleted, unlink it from any Service Booking
    and mark the booking as Cancelled.
    """
    # Find any Service Booking linked to this invoice
    linked_booking = frappe.db.get_value(
        "Service Booking", 
        {"invoice": doc.name}, 
        "name"
    )
    
    if linked_booking:
        # Unlink the invoice and mark as Cancelled
        frappe.db.set_value("Service Booking", linked_booking, {
            "invoice": None,
            "status": "Cancelled"
        })
        frappe.msgprint(
            f"<a href='/app/service-booking/{linked_booking}'>{linked_booking}</a> marked Cancelled.",
            alert=True
        )


def sync_pos_items_to_booking(pos_invoice, booking_name):
    """
    Sync items from POS Invoice to existing Service Booking.
    Compares items and reports added/removed changes.
    Also marks the booking as Completed since payment is done.
    """
    from frappe.utils import add_to_date
    
    booking_doc = frappe.get_doc("Service Booking", booking_name)
    
    # Get existing service items in booking (by item code)
    existing_items = {item.service_item for item in booking_doc.items}
    
    # Get service items from POS Invoice (non-stock only)
    pos_service_items = set()
    pos_items_data = {}
    
    for item in pos_invoice.items:
        is_stock = frappe.db.get_value("Item", item.item_code, "is_stock_item")
        if not is_stock:
            pos_service_items.add(item.item_code)
            pos_items_data[item.item_code] = {
                "service_item": item.item_code,
                "service_name": item.item_name,
                "duration_minutes": 60,  # Default
                "price": item.rate
            }
    
    # Calculate differences
    added_items = pos_service_items - existing_items
    removed_items = existing_items - pos_service_items
    
    # Apply changes if any difference
    if added_items or removed_items:
        # Clear existing items and rebuild from POS (full sync)
        booking_doc.items = []
        total_duration = 0
        
        for item_code in pos_service_items:
            item_data = pos_items_data[item_code]
            booking_doc.append("items", item_data)
            total_duration += item_data["duration_minutes"]
        
        # Update duration
        booking_doc.duration_minutes = total_duration
        
        # Update end_datetime based on start and new duration
        if booking_doc.start_datetime:
            booking_doc.end_datetime = add_to_date(booking_doc.start_datetime, minutes=total_duration)
    
    # Sync therapist from POS Invoice (in case it was changed)
    if pos_invoice.get("therapist"):
        booking_doc.therapist = pos_invoice.therapist
    
    # Mark booking as Completed (payment done via POS)
    booking_doc.status = "Completed"
    booking_doc.save(ignore_permissions=True)

    
    # Build notification message
    changes = []
    if added_items:
        changes.append(f"{len(added_items)} added")
    if removed_items:
        changes.append(f"{len(removed_items)} removed")
    
    if changes:
        change_msg = ", ".join(changes)
        frappe.msgprint(
            f"Items synced ({change_msg}). "
            f"<a href='/app/service-booking/{booking_name}'>{booking_name}</a> marked Completed.",
            alert=True
        )
    else:
        frappe.msgprint(
            f"<a href='/app/service-booking/{booking_name}'>{booking_name}</a> marked Completed.",
            alert=True
        )


def create_service_booking_from_invoice(pos_invoice):
    """
    Create a Service Booking from a POS Invoice (reverse sync).
    Used when receptionist uses POS directly without creating a booking first.
    
    The booking is created with:
    - end_datetime = now (payment time)
    - start_datetime = now - total_duration
    - status = Completed
    """
    from frappe.utils import now_datetime, add_to_date
    
    # Calculate total duration from invoice items
    total_duration = 0
    service_items = []
    
    for item in pos_invoice.items:
        # Check if it's a service item (not stock)
        is_stock = frappe.db.get_value("Item", item.item_code, "is_stock_item")
        if not is_stock:
            # Default duration 60 minutes per service
            item_duration = 60
            total_duration += item_duration
            service_items.append({
                "service_item": item.item_code,
                "service_name": item.item_name,
                "duration_minutes": item_duration,
                "price": item.rate
            })

    
    # If no service items, don't create booking
    if not service_items:
        return None
    
    # Default duration if nothing calculated
    if total_duration == 0:
        total_duration = 60
    
    # Calculate times: end = now, start = now - duration
    end_time = now_datetime()
    start_time = add_to_date(end_time, minutes=-total_duration)
    
    try:
        # Get branch - MUST be from POS Profile, each branch has its own POS
        branch = pos_invoice.branch
        
        if not branch and pos_invoice.pos_profile:
            # Method 1: Extract from warehouse name "Bohol Main Store - MDB" → "Bohol Main"
            warehouse = frappe.db.get_value("POS Profile", pos_invoice.pos_profile, "warehouse")
            if warehouse:
                # Format: "Bohol Main Store - MDB" → "Bohol Main"
                branch_name = warehouse.replace(" Store", "").split(" - ")[0]
                if frappe.db.exists("Branch", branch_name):
                    branch = branch_name
            
            # Method 2: Extract from POS Profile name "Bohol Main POS" → "Bohol Main"
            if not branch:
                pos_name = pos_invoice.pos_profile
                branch_name = pos_name.replace(" POS", "").strip()
                if frappe.db.exists("Branch", branch_name):
                    branch = branch_name
        
        # If still no branch, log error but don't use a fallback - report integrity matters
        if not branch:
            frappe.log_error(
                f"Cannot determine branch for POS Invoice {pos_invoice.name} with POS Profile {pos_invoice.pos_profile}",
                "Masaje App - Branch Error"
            )
            return None
        
        booking = frappe.new_doc("Service Booking")
        booking.customer = pos_invoice.customer
        booking.branch = branch
        booking.therapist = pos_invoice.get("therapist")
        booking.booking_date = frappe.utils.today()
        booking.time_slot = frappe.utils.nowtime()[:5]  # HH:MM format
        booking.start_datetime = start_time
        booking.end_datetime = end_time
        booking.duration_minutes = total_duration
        booking.status = "Completed"
        booking.invoice = pos_invoice.name

        
        # Add items
        for item in service_items:
            booking.append("items", item)
        
        booking.insert(ignore_permissions=True)
        
        frappe.msgprint(
            f"Service Booking <a href='/app/service-booking/{booking.name}'>{booking.name}</a> "
            "auto-created from POS Invoice.",
            alert=True
        )
        
        return booking.name
        
    except Exception as e:
        frappe.log_error(f"Failed to create Service Booking from POS Invoice: {str(e)}", "Masaje App")
        return None


def calculate_and_store_commission(doc, therapist, linked_booking=None):
    """
    Calculate and store commission for a POS Invoice.
    """
    # Get commission rate from Employee
    commission_rate = frappe.db.get_value("Employee", therapist, "commission_rate") or 0
    
    if not commission_rate:
        return
    
    # Calculate commission on grand_total
    commission_amount = (doc.grand_total or 0) * (commission_rate / 100)
    
    # Update the invoice with commission
    doc.db_set("total_commission", commission_amount, update_modified=False)
    doc.db_set("commission_amount", commission_amount, update_modified=False)
    doc.db_set("commission_rate", commission_rate, update_modified=False)
    doc.db_set("amount_eligible_for_commission", doc.grand_total, update_modified=False)
    
    # Update linked Service Booking if exists
    if linked_booking:
        frappe.db.set_value("Service Booking", linked_booking, {
            "commission_amount": commission_amount,
            "therapist": therapist
        }, update_modified=False)
    
    frappe.msgprint(
        f"Commission of {commission_rate}% ({frappe.format_value(commission_amount, {'fieldtype': 'Currency'})}) "
        f"calculated for therapist.",
        alert=True
    )
