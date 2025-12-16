
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
