
import frappe
from frappe.utils import get_datetime, add_to_date


def get_pos_profile_for_branch(branch):
    """
    Get POS Profile for a given branch.
    Looks up POS Profile where warehouse name contains the branch name.
    """
    if not branch:
        return None
    
    return frappe.db.get_value(
        "POS Profile", 
        {"warehouse": ["like", f"%{branch}%"]}, 
        "name"
    )


def create_pos_invoice_for_booking(booking_doc, save=True):
    """
    Create a draft POS Invoice for a Service Booking.
    
    Args:
        booking_doc: Service Booking document
        save: Whether to save the invoice (default True)
        
    Returns:
        POS Invoice name if successful, None otherwise
    """
    if not booking_doc.branch:
        frappe.log_error("Cannot create POS Invoice: No branch specified", "Masaje Booking")
        return None
        
    pos_profile_name = get_pos_profile_for_branch(booking_doc.branch)
    
    if not pos_profile_name:
        frappe.log_error(
            f"POS Profile not found for branch: {booking_doc.branch}", 
            "Masaje Booking"
        )
        return None
    
    try:
        profile_doc = frappe.get_doc("POS Profile", pos_profile_name)
        cost_center = frappe.db.get_value("Branch", booking_doc.branch, "default_cost_center")
        warehouse = profile_doc.warehouse
        
        # Create Invoice
        pos_inv = frappe.new_doc("POS Invoice")
        pos_inv.customer = booking_doc.customer
        pos_inv.pos_profile = pos_profile_name
        pos_inv.company = frappe.defaults.get_global_default("company")
        pos_inv.posting_date = booking_doc.booking_date or frappe.utils.today()
        pos_inv.branch = booking_doc.branch
        pos_inv.update_stock = profile_doc.update_stock
        
        # Get items from child table or single service_item
        booking_items = []
        
        if booking_doc.get("items") and len(booking_doc.items) > 0:
            for item in booking_doc.items:
                booking_items.append({
                    "service_item": item.service_item,
                    "price": item.price or get_item_price(item.service_item, profile_doc.selling_price_list)
                })
        elif booking_doc.service_item:
            price = get_item_price(booking_doc.service_item, profile_doc.selling_price_list)
            booking_items.append({
                "service_item": booking_doc.service_item,
                "price": price
            })
        
        if not booking_items:
            frappe.log_error("Cannot create POS Invoice: No items found", "Masaje Booking")
            return None
        
        # Add items to invoice
        total_comm = 0.0
        for item in booking_items:
            item_comm = (item.get("price") or 0) * 0.10
            total_comm += item_comm
            
            # Check if item is a stock item - only add warehouse for stock items
            is_stock_item = frappe.db.get_value("Item", item["service_item"], "is_stock_item")
            
            item_row = {
                "item_code": item["service_item"],
                "qty": 1,
                "rate": item.get("price") or 0,
                "uom": "Unit",
                "conversion_factor": 1,
                "cost_center": cost_center
            }
            
            # Only add warehouse for stock items
            if is_stock_item:
                item_row["warehouse"] = warehouse
            
            pos_inv.append("items", item_row)

        
        # Sales Team Logic
        if booking_doc.therapist:
            sales_person = frappe.db.get_value(
                "Sales Person", 
                {"employee": booking_doc.therapist, "enabled": 1}
            )
            if sales_person:
                pos_inv.append("sales_team", {
                    "sales_person": sales_person,
                    "allocated_percentage": 100,
                })
        
        pos_inv.set_missing_values()
        pos_inv.docstatus = 0  # Draft
        
        if save:
            pos_inv.insert(ignore_permissions=True)
            
            # Update booking with invoice link and commission
            frappe.db.set_value("Service Booking", booking_doc.name, {
                "invoice": pos_inv.name,
                "commission_amount": total_comm
            })
            
            return pos_inv.name
        else:
            return pos_inv
            
    except Exception as e:
        frappe.log_error(f"POS Invoice creation failed: {str(e)}", "Masaje Booking")
        return None


def get_item_price(item_code, price_list=None):
    """
    Get price for an item from a price list.
    Falls back to standard_rate if no price list price found.
    """
    price = None
    
    if price_list:
        price = frappe.db.get_value(
            "Item Price", 
            {"item_code": item_code, "price_list": price_list}, 
            "price_list_rate"
        )
    
    if not price:
        price = frappe.db.get_value(
            "Item Price", 
            {"item_code": item_code, "price_list": "Standard Selling"}, 
            "price_list_rate"
        )
    
    if not price:
        price = frappe.db.get_value("Item", item_code, "standard_rate") or 0
    
    return price


def calculate_booking_commission(booking_doc, rate=0.10):
    """
    Calculate commission for a booking based on service prices.
    
    Args:
        booking_doc: Service Booking document
        rate: Commission rate (default 10%)
        
    Returns:
        Total commission amount
    """
    total_price = 0.0
    
    if booking_doc.get("items") and len(booking_doc.items) > 0:
        for item in booking_doc.items:
            total_price += item.price or 0
    elif booking_doc.service_item:
        total_price = get_item_price(booking_doc.service_item)
    
    return total_price * rate
