
import frappe
from frappe.utils import add_days, nowdate, getdate

def run():
    frappe.set_user("Administrator")
    
    # 1. ensure Branches
    branches = ["Bohol Main", "Panglao Branch"]
    for b in branches:
        if not frappe.db.exists("Branch", b):
            frappe.get_doc({"doctype": "Branch", "branch": b}).insert()

    # 2. Ensure Items
    service_item = "Massage Service 60m"
    if not frappe.db.exists("Item", service_item):
        frappe.get_doc({
            "doctype": "Item", "item_code": service_item, "item_group": "Services", "is_stock_item": 0
        }).insert()
        
    # 3. Ensure Price List
    pl = "Standard Selling"
    if not frappe.db.exists("Price List", pl):
        frappe.get_doc({"doctype": "Price List", "price_list_name": pl, "selling": 1}).insert()
        
    if not frappe.db.exists("Item Price", {"item_code": service_item, "price_list": pl}):
        frappe.get_doc({
            "doctype": "Item Price", "item_code": service_item, "price_list": pl, "price_list_rate": 1500
        }).insert()

    # 4. Create Bookings & Invoices across last 7 days
    dates = [0, -1, -2, -3] # Today, Yesterday, etc.
    
    for i, day_offset in enumerate(dates):
        date = add_days(nowdate(), day_offset)
        
        for branch in branches:
            # Create 2 bookings per branch per day
            for j in range(2):
                cust_name = f"Test Cust {branch[0]}{i}{j}"
                if not frappe.db.exists("Customer", cust_name):
                    frappe.get_doc({"doctype": "Customer", "customer_name": cust_name}).insert()
                
                # Create Booking
                booking = frappe.get_doc({
                    "doctype": "Service Booking",
                    "customer": cust_name,
                    "customer_name": cust_name,
                    "branch": branch,
                    "booking_date": date,
                    "time_slot": f"{10+j}:00",
                    "status": "Completed", # Important for logic? Report creates counts on ALL non-cancelled
                    "service_item": service_item,
                    "duration_minutes": 60,
                    "therapist": "Integration Therapist" if frappe.db.exists("Employee", "Integration Therapist") else None 
                    # Note: Therapist Utilization needs therapist.
                })
                # Check therapist
                if not booking.therapist:
                     # Create dummy therapist
                     t_name = f"Therapist {branch}"
                     if not frappe.db.exists("Employee", {"first_name": t_name}):
                         frappe.get_doc({
                             "doctype":"Employee", "first_name": t_name, "status":"Active", 
                             "date_of_joining": "2020-01-01", "date_of_birth":"1990-01-01", "gender":"Female",
                             "branch": branch
                         }).insert()
                     booking.therapist = frappe.db.get_value("Employee", {"first_name": t_name}, "name")
                
                booking.insert(ignore_permissions=True)
                
                # Creates POS Invoice (Simulating behavior or manually creating)
                # Report logic: JOIN Service Booking ON s.invoice = p.name
                # So we MUST create POS Invoice and link it.
                
                pos_inv = frappe.get_doc({
                    "doctype": "POS Invoice",
                    "customer": cust_name,
                    "posting_date": date,
                    "due_date": date,
                    "company": "Masaje de Bohol",
                    "pos_profile": frappe.db.get_value("POS Profile", {"company": "Masaje de Bohol"}, "name") or "Integration POS",
                    "items": [{
                        "item_code": service_item,
                        "qty": 1,
                        "rate": 1500,
                        "amount": 1500
                    }],
                    "payments":  [{
                        "mode_of_payment": "Cash",
                        "amount": 1500,
                        "account": frappe.db.get_value("Account", {"account_type": "Cash", "company": "Masaje de Bohol"}, "name") or "Cash - MDB"
                    }]
                })
                
                # Need to set warehouse if missing
                if not pos_inv.items[0].warehouse:
                     pos_inv.items[0].warehouse = frappe.db.get_value("Warehouse", {"company": "Masaje de Bohol"}, "name")
                
                pos_inv.insert(ignore_permissions=True)
                pos_inv.submit()
                
                # Link back
                booking.invoice = pos_inv.name
                booking.duration_minutes = 60
                booking.save()
                
    print("SUCCESS: Generated Test Data for Reports")
