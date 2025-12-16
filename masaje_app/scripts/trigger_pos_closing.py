
import frappe

def run():
    print("--- Simulating POS Closing Entry ---")
    
    user = "Administrator"
    date = frappe.utils.today()
    pos_profile = frappe.db.get_value("POS Profile", {"warehouse": ["like", "%Bohol%"]}, "name")
    
    # Check for open Period/Opening Entry? 
    # v13+ usually uses POS Opening Entry. 
    # If no opening entry, we might need one.
    # But let's try just Closing Entry for the Invoices we made.
    
    # Actually, recent ERPNext requires POS Opening for the session.
    # If we didn't have one, maybe that's why stock didn't reduce?
    # But we created invoices as Administrator.
    
    if not pos_profile:
        print("POS Profile not found.")
        return

    # Check for existing Opening Entry
    opening = frappe.db.get_value("POS Opening Entry", {"pos_profile": pos_profile, "status": "Open", "docstatus": 1}, "name")
    if not opening:
        print("No Open Session found. Creating Opening Entry first...")
        op = frappe.new_doc("POS Opening Entry")
        op.period_start_date = date
        op.pos_profile = pos_profile
        op.user = user
        op.company = "Masaje de Bohol"
        op.docstatus = 1
        op.insert(ignore_permissions=True)
        opening = op.name
        print(f"Created Opening Entry: {opening}")
    else:
        print(f"Using Closing Entry: {opening}")
    
    # Now create Closing Entry
    closing = frappe.new_doc("POS Closing Entry")
    closing.pos_opening_entry = opening
    closing.period_end_date = date
    closing.posting_date = date
    closing.posting_time = frappe.utils.nowtime()
    closing.pos_profile = pos_profile
    closing.user = user
    closing.company = "Masaje de Bohol"
    
    # It usually fetches invoices automatically on save
    closing.save()
    
    # Check if invoices are linked
    print(f"Linked Invoices in Closing: {len(closing.pos_transactions)}")
    
    closing.submit()
    print(f"Submitted POS Closing: {closing.name}")
    
    print("POS Closing Complete. Stock should be updated now.")
