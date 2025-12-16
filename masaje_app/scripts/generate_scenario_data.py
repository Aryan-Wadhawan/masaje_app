
import frappe
from frappe.utils import nowdate

def run():
    frappe.set_user("Administrator")
    print("--- Generating Scenario Data ---")
    
    branches = ["Bohol Main", "Panglao Branch"]
    service_item = "Massage Service 60m"
    date = nowdate()
    
    # Ensure Item exists (re-using logic or assuming exists from previous setup)
    if not frappe.db.exists("Item", service_item):
         print("Error: Item missing (should have been created)")
         return

    for branch in branches:
        print(f"Processing {branch}...")
        
        # Scenario 1: Walk-In (In-Person)
        # 1. Create Customer
        cust_name = f"Test Cust {branch} WalkIn"
        if not frappe.db.exists("Customer", cust_name):
            frappe.get_doc({"doctype": "Customer", "customer_name": cust_name}).insert()
            
        # 2. Create Booking
        booking_in = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": cust_name,
            "customer_name": cust_name,
            "branch": branch,
            "booking_date": date,
            "time_slot": "10:00",
            "status": "Completed", # Walk-in completed
            "service_item": service_item,
            "duration_minutes": 60,
            "source": "Walk-In" 
            # Note: 'source' might not be a standard field yet, but checking logic
        })
        booking_in.insert(ignore_permissions=True)
        
        # 3. Create POS Invoice
        # Fetch Cost Center
        cost_center = frappe.db.get_value("Branch", branch, "default_cost_center")
        
        pos_inv_in = frappe.get_doc({
            "doctype": "POS Invoice",
            "customer": cust_name,
            "posting_date": date,
            "due_date": date,
            "company": "Masaje de Bohol",
            "branch": branch, # Custom Field
            "update_stock": 1,
            "pos_profile": frappe.db.get_value("POS Profile", {"company": "Masaje de Bohol"}, "name") or "Integration POS",
            "items": [{"item_code": service_item, "qty": 1, "rate": 1500, "amount": 1500, "cost_center": cost_center}],
            "payments": [{"mode_of_payment": "Cash", "amount": 1500, "account": "Cash - MDB"}]
        })
        # Set warehouse
        if not pos_inv_in.items[0].warehouse:
             pos_inv_in.items[0].warehouse = frappe.db.get_value("Warehouse", {"company": "Masaje de Bohol"}, "name")
             
        pos_inv_in.insert(ignore_permissions=True)
        pos_inv_in.submit()
        
        # Link back
        booking_in.invoice = pos_inv_in.name
        booking_in.save()
        print(f"  Created Walk-In: {booking_in.name} linked to {pos_inv_in.name}")


        # Scenario 2: Online Booking
        # 1. Create Customer
        cust_name_online = f"Test Cust {branch} Online"
        if not frappe.db.exists("Customer", cust_name_online):
            frappe.get_doc({"doctype": "Customer", "customer_name": cust_name_online}).insert()
            
        # 2. Create Booking (Initially Scheduled/Draft, then Completed)
        booking_on = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": cust_name_online,
            "customer_name": cust_name_online,
            "branch": branch,
            "booking_date": date,
            "time_slot": "14:00",
            "status": "Completed", # Online booking fulfilled
            "service_item": service_item,
            "duration_minutes": 60,
            "source": "Online"
        })
        booking_on.insert(ignore_permissions=True)
        
        # 3. POS Invoice (Payment for Online Booking)
        pos_inv_on = frappe.get_doc({
            "doctype": "POS Invoice",
            "customer": cust_name_online,
            "posting_date": date,
            "due_date": date,
            "company": "Masaje de Bohol",
            "branch": branch, # Custom Field
            "update_stock": 1,
            "pos_profile": frappe.db.get_value("POS Profile", {"company": "Masaje de Bohol"}, "name") or "Integration POS",
            "items": [{"item_code": service_item, "qty": 1, "rate": 1500, "amount": 1500, "cost_center": cost_center}],
            "payments": [{"mode_of_payment": "Cash", "amount": 1500, "account": "Cash - MDB"}] # Simplified to Cash to avoid config errors
        })
        if not pos_inv_on.items[0].warehouse:
             pos_inv_on.items[0].warehouse = frappe.db.get_value("Warehouse", {"company": "Masaje de Bohol"}, "name")
             
        pos_inv_on.insert(ignore_permissions=True)
        pos_inv_on.submit()
        
        booking_on.invoice = pos_inv_on.name
        booking_on.save()
        print(f"  Created Online: {booking_on.name} linked to {pos_inv_on.name}")
        
    print("SUCCESS: Generated Scenario Data (1 Walk-In, 1 Online per Branch)")
