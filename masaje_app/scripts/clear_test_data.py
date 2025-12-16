
import frappe

def run():
    print("--- Clearing Test Data (Aggressive) ---")
    
    # 1. Delete Service Bookings first (Child)
    # Filter by our test customer pattern "Test Cust%"
    bookings = frappe.get_all("Service Booking", filters={"customer": ["like", "Test Cust%"]}, pluck="name")
    for b in bookings:
        try:
            frappe.delete_doc("Service Booking", b, force=1)
            print(f"Deleted Booking {b}")
        except Exception as e:
            print(f"Error deleting {b}: {e}")

    # 2. Cancel and Delete POS Invoices
    # Filter by Test Customer pattern
    invoices = frappe.get_all("POS Invoice", filters={"customer": ["like", "Test Cust%"]}, pluck="name")
    for inv in invoices:
        try:
            doc = frappe.get_doc("POS Invoice", inv)
            if doc.docstatus == 1:
                doc.cancel()
            doc.delete()
            print(f"Deleted Invoice {inv}")
        except Exception as e:
            print(f"Error deleting {inv}: {e}")

    # 3. Delete Customers
    customers = frappe.get_all("Customer", filters={"customer_name": ["like", "Test Cust%"]}, pluck="name")
    for c in customers:
        frappe.delete_doc("Customer", c, force=1)
        print(f"Deleted Customer {c}")

    print("Cleanup Completed.")
