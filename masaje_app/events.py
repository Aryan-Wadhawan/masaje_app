
import frappe
from masaje_app.utils import create_pos_invoice_for_booking


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


def on_pos_invoice_submit(doc, method):
    """
    Calculate and store commission when POS Invoice is submitted.
    Uses the therapist's commission_rate from Employee record.
    """
    # Check if therapist is set
    therapist = doc.get("therapist")
    if not therapist:
        return
    
    # Get commission rate from Employee
    commission_rate = frappe.db.get_value("Employee", therapist, "commission_rate") or 0
    
    if not commission_rate:
        return
    
    # Calculate commission on service items (grand_total)
    commission_amount = (doc.grand_total or 0) * (commission_rate / 100)
    
    # Update the document directly using db_set (works during submit)
    # Set BOTH the standard field (total_commission) and custom field (commission_amount)
    doc.db_set("total_commission", commission_amount, update_modified=False)
    doc.db_set("commission_amount", commission_amount, update_modified=False)  # Custom field for list view
    doc.db_set("commission_rate", commission_rate, update_modified=False)
    doc.db_set("amount_eligible_for_commission", doc.grand_total, update_modified=False)

    
    # Also update linked Service Booking if exists
    linked_booking = frappe.db.get_value(
        "Service Booking", 
        {"invoice": doc.name}, 
        "name"
    )
    
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
