
import frappe
import frappe.utils
from masaje_app.report.daily_branch_sales import daily_branch_sales

def run():
    print("--- Direct Report Logic Test ---")
    
    today = frappe.utils.nowdate()
    # Expect 2 bookings per branch for today
    print(f"Checking {today}...")
    print("Executing Report Logic directly...")
    
    # Run with filters
    columns, data, message, chart, summary, skip = daily_branch_sales.execute({"from_date": today, "to_date": today})
    
    print(f"Data Rows: {len(data)}")
    for d in data:
        print(f"  {d['branch']}: Bookings={d['total_bookings']}, Sales={d['total_sales']}")
        
    print("\n--- Detailed Booking Check ---")
    bookings = frappe.get_all("Service Booking", fields=["name", "branch", "source", "status", "invoice"], filters={"booking_date": today})
    for b in bookings:
        print(f"  {b.name}: {b.branch} | {b.source} | {b.status} | Invoice: {b.invoice}")

    print("Execution complete.")
