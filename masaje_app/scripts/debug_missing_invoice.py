import frappe

def debug():
    customer_name = "postest"
    print(f"Searching for Customer matching '{customer_name}'...")
    
    # 1. Find Customer
    customers = frappe.get_all("Customer", filters={"customer_name": ["like", f"%{customer_name}%"]}, fields=["name", "customer_name"])
    if not customers:
        print("No customer found!")
        return
        
    customer = customers[0]
    print(f"Found Customer: {customer.customer_name} ({customer.name})")
    
    # 2. Find Booking
    bookings = frappe.get_all("Service Booking", 
                              filters={"customer": customer.name}, 
                              order_by="creation desc", 
                              limit=1)
    
    if not bookings:
        print("No bookings found for this customer.")
        return
        
    booking = frappe.get_doc("Service Booking", bookings[0].name)
    print(f"Latest Booking: {booking.name} (Status: {booking.docstatus})")
    print(f"Branch: {booking.branch}")
    
    # 3. Check for POS Invoice
    invoices = frappe.get_all("POS Invoice", filters={"customer": customer.name, "docstatus": 0}, fields=["name", "pos_profile"])
    
    if invoices:
        print(f"FOUND Draft POS Invoices: {invoices}")
    else:
        print("NO Draft POS Invoice found.")
        
        # 4. Simulate Failure Logic
        print("-" * 20)
        print("Simulating Invoice Creation Logic:")
        
        branch = booking.branch
        # Logic from api.py
        pos_profile_name = frappe.db.get_value("POS Profile", {"warehouse": ["like", f"%{branch}%"]}, "name")
        print(f"Target POS Profile for {branch}: {pos_profile_name}")
        
        if not pos_profile_name:
            print("FAILURE: No POS Profile found for this branch!")
            return
            
        # Check Opening Entry
        user = frappe.session.user # In API this is the request user
        # But wait, the API is running as Administrator/Guest usually?
        # Actually, the API doesn't pass a user to get_doc, so it uses current session.
        # But for POS Invoice creation, we usually need an Open Entry.
        
        # Let's check for ANY open entry for this profile
        open_entry = frappe.db.get_value("POS Opening Entry", 
                                         {"pos_profile": pos_profile_name, "status": "Open", "docstatus": 1}, 
                                         "name")
        print(f"Open POS Entry for {pos_profile_name}: {open_entry}")
        
        if not open_entry:
            print("FAILURE: No Open POS Entry found! This is required to create a POS Invoice.")

if __name__ == "__main__":
    frappe.connect()
    debug()
