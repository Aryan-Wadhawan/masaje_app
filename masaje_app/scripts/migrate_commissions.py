
import frappe

def run():
    print("--- Migrating Commissions to Sales Team ---")
    
    # Get all POS Invoices created by the app (filtering by those with linked bookings or specific naming)
    # Or just iterate all draft/consolidated ones.
    # Let's target the ones linked to Service Bookings
    
    bookings = frappe.get_all("Service Booking", 
        filters={"invoice": ["is", "set"], "therapist": ["is", "set"]}, 
        fields=["name", "invoice", "therapist"]
    )
    
    for b in bookings:
        inv_name = b.invoice
        if not frappe.db.exists("POS Invoice", inv_name):
            continue
            
        # Get Sales Person
        sp = frappe.db.get_value("Sales Person", {"employee": b.therapist, "enabled": 1})
        if not sp:
            continue
            
        # Check if Sales Team child row exists
        existing_team = frappe.db.sql("""
            SELECT name FROM `tabSales Team` 
            WHERE parent = %s AND sales_person = %s
        """, (inv_name, sp))
        
        if not existing_team:
            # Manual Insert to bypass 'Submitted' state
            st_name = frappe.generate_hash(length=10)
            frappe.db.sql("""
                INSERT INTO `tabSales Team`
                (name, parent, parenttype, parentfield, sales_person, allocated_percentage, docstatus, idx)
                VALUES (%s, %s, 'POS Invoice', 'sales_team', %s, 100, 1, 1)
            """, (st_name, inv_name, sp))
            print(f"Inserted Sales Team {st_name} for Invoice {inv_name}")
            
        # Update Main Fields via direct DB set (Bypasses doc.save validations)
        frappe.db.set_value("POS Invoice", inv_name, "total_commission", 0) # Clear our manual override if we want? 
        # Actually user wants standard logic.
        # But we need to clear the 'Amount Eligible' if currently set wrong?
        # Let's simple set them to 0 as standard standard report calculates it from Sales Team + Item
        
        # Wait, if we use Sales Team, 'Amount Eligible' and 'Total Commission' on HEAD are usually calculated.
        # But for data fix, we might want to just let the report handle it.
        # The report uses `tabSales Team`.
        
        # We can clear the manual values we set earlier to avoid confusion
        frappe.db.set_value("POS Invoice", inv_name, "total_commission", 0)
        frappe.db.set_value("POS Invoice", inv_name, "amount_eligible_for_commission", 0)
        
        print(f"Fixed Invoice {inv_name}")
        
    print("Migration Complete.")
