
import frappe

def run():
    print("--- Diagnostic Check ---")
    
    # Check Bookings
    bookings = frappe.get_all("Service Booking", fields=["name", "branch", "invoice", "booking_date", "status"], filters={"branch": "Bohol Main"}, limit=5)
    print(f"Bookings (Bohol Main): {len(bookings)}")
    for b in bookings:
        print(f"  Booking: {b.name}, Inv: {b.invoice}, Status: {b.status}, Date: {b.booking_date}")
        if b.invoice:
            inv = frappe.db.get_value("POS Invoice", b.invoice, ["name", "docstatus", "grand_total"], as_dict=True)
            print(f"    -> Linked Invoice: {inv}")
            
    # Check Raw SQL Join
    sql = """
        SELECT count(*)
        FROM `tabPOS Invoice` p
        JOIN `tabService Booking` s ON s.invoice = p.name
        WHERE p.docstatus = 1 AND s.branch = 'Bohol Main'
    """
    count = frappe.db.sql(sql)[0][0]
    print(f"Raw SQL Join Count: {count}")
    
    if count == 0:
        print("\nDEBUG: Why 0?")
        # Check if invoices exist at all
        inv_count = frappe.db.count("POS Invoice", filters={"docstatus": 1})
        print(f"Total Submitted Invoices: {inv_count}")
        
        # Check if bookings have invoices
        bk_w_inv = frappe.db.count("Service Booking", filters={"invoice": ["is", "set"]})
        print(f"Bookings with Invoice set: {bk_w_inv}")
