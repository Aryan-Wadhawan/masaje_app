
import frappe
from masaje_app.utils import create_pos_invoice_for_booking


def on_service_booking_validate(doc, method):
    """
    Auto-calculate duration_minutes from items table on server-side.
    Also calculates start_datetime/end_datetime and validates therapist conflicts.
    """
    from frappe.utils import get_datetime
    from datetime import datetime, timedelta
    
    # Step 1: Calculate total duration from items (fetch from Item doctype)
    total_duration = 0
    if doc.items:
        for item in doc.items:
            # Get duration from Item's custom_duration_minutes field
            item_duration = frappe.db.get_value("Item", item.service_item, "custom_duration_minutes")
            total_duration += (item_duration or 60)  # Default 60 if not set
    
    # Set duration if calculated from items
    if total_duration > 0:
        doc.duration_minutes = total_duration
    elif not doc.duration_minutes:
        # Default to 60 minutes if no items and no duration set
        doc.duration_minutes = 60
    
    # Step 2: Calculate start_datetime and end_datetime
    if doc.booking_date and doc.time_slot:
        # Combine date and time  
        booking_date = get_datetime(doc.booking_date).date()
        
        # Handle time_slot as string "HH:MM" or timedelta
        if isinstance(doc.time_slot, str):
            time_parts = doc.time_slot.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            start_dt = datetime.combine(booking_date, datetime.min.time().replace(hour=hour, minute=minute))
        elif isinstance(doc.time_slot, timedelta):
            # time_slot stored as timedelta from midnight
            start_dt = datetime.combine(booking_date, datetime.min.time()) + doc.time_slot
        else:
            start_dt = datetime.combine(booking_date, doc.time_slot)
        
        doc.start_datetime = start_dt
        
        # Calculate end time
        duration = doc.duration_minutes or 60
        doc.end_datetime = start_dt + timedelta(minutes=duration)
    
    # Step 3: Check for therapist conflicts (prevent double-booking)
    if doc.therapist and doc.start_datetime and doc.end_datetime:
        check_therapist_conflict(doc)


def check_therapist_conflict(doc):
    """
    Check if therapist is already booked during the booking time.
    Raises exception if conflict found.
    """
    # Find overlapping bookings for same therapist
    conflicts = frappe.db.sql("""
        SELECT name, start_datetime, end_datetime
        FROM `tabService Booking`
        WHERE therapist = %(therapist)s
        AND name != %(name)s
        AND status NOT IN ('Cancelled', 'Completed')
        AND (
            (start_datetime <= %(start)s AND end_datetime > %(start)s)
            OR (start_datetime < %(end)s AND end_datetime >= %(end)s)
            OR (start_datetime >= %(start)s AND end_datetime <= %(end)s)
        )
    """, {
        "therapist": doc.therapist,
        "name": doc.name or "",
        "start": doc.start_datetime,
        "end": doc.end_datetime
    }, as_dict=True)
    
    if conflicts:
        conflict = conflicts[0]
        therapist_name = frappe.db.get_value("Employee", doc.therapist, "employee_name")
        frappe.throw(
            f"{therapist_name} is already booked from "
            f"{frappe.format(conflict.start_datetime, 'Datetime')} to "
            f"{frappe.format(conflict.end_datetime, 'Datetime')}. "
            "Please choose a different therapist or time."
        )


def on_service_booking_insert(doc, method):
    """
    Called when Service Booking is created.
    
    NEW WORKFLOW:
    - POS Invoice is NOT created on insert
    - Draft POS Invoice created only when status changes to 'Approved'
    - This allows online bookings (made after hours) to be reviewed first
    """
    # No auto-creation here - moved to on_update with 'Approved' status trigger
    pass


def on_service_booking_update(doc, method):
    """
    Handle Service Booking updates.
    
    KEY TRIGGERS:
    1. Status = 'Approved' and no invoice → Create draft POS Invoice
    2. Status = 'Cancelled' and has draft invoice → Delete the draft
    """
    # Get previous status to detect change
    previous_status = doc.get_doc_before_save().status if doc.get_doc_before_save() else None
    
    # TRIGGER 1: Status changed to 'Approved' - Create draft POS Invoice
    if doc.status == "Approved" and previous_status != "Approved":
        if not doc.invoice and doc.customer:
            invoice_name = create_pos_invoice_for_booking(doc)
            if invoice_name:
                frappe.msgprint(
                    f"Draft POS Invoice <a href='/app/pos-invoice/{invoice_name}'>{invoice_name}</a> created.",
                    alert=True
                )
            else:
                frappe.msgprint(
                    "Note: Could not create POS Invoice. Please check if POS session is open.",
                    indicator="orange",
                    alert=True
                )
    
    # TRIGGER 2: Status changed to 'Cancelled' - Delete draft invoice if exists
    if doc.status == "Cancelled" and doc.invoice:
        invoice_status = frappe.db.get_value("POS Invoice", doc.invoice, "docstatus")
        if invoice_status == 0:  # Draft
            frappe.delete_doc("POS Invoice", doc.invoice, ignore_permissions=True)
            frappe.db.set_value("Service Booking", doc.name, "invoice", None)
            frappe.msgprint(
                f"Draft POS Invoice {doc.invoice} deleted.",
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
    Sync essential data from POS Invoice to Service Booking.
    
    IMPORTANT: Booking items are NOT overwritten to preserve the original request.
    - Service Booking = What customer originally requested (for comparison)
    - POS Invoice = What was actually paid (source of truth for reports)
    
    This sync only:
    1. Marks booking as Completed
    2. Syncs therapist if changed in POS
    """
    booking_doc = frappe.get_doc("Service Booking", booking_name)
    
    # Sync therapist from POS Invoice (in case it was changed/assigned at checkout)
    if pos_invoice.get("therapist"):
        booking_doc.therapist = pos_invoice.therapist
    
    # Mark booking as Completed (payment done via POS)
    booking_doc.status = "Completed"
    booking_doc.save(ignore_permissions=True)
    
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
        item_data = frappe.db.get_value("Item", item.item_code, ["is_stock_item", "custom_duration_minutes"], as_dict=True)
        if not item_data.is_stock_item:
            # Use custom duration from Item, fallback to 60 minutes
            item_duration = item_data.custom_duration_minutes or 60
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
