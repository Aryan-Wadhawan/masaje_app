import frappe
from frappe.utils import getdate

def check_availability():
    date_str = "2025-12-16" # Date from screenshot
    date_obj = getdate(date_str)
    day_name = date_obj.strftime("%A") # Tuesday
    branch = "Bohol Main" # Assuming default branch
    
    print(f"Checking availability for: {day_name} ({date_str}) at {branch}")
    
    # 1. Find Therapists at Branch
    therapists = frappe.get_all("Employee", filters={"branch": branch, "status": "Active"}, pluck="name")
    print(f"Active Therapists at {branch}: {therapists}")
    
    # 2. Check Schedules
    schedules = frappe.get_all("Therapist Schedule", 
                               filters={
                                   "therapist": ["in", therapists],
                                   "day_of_week": day_name
                               },
                               fields=["therapist", "start_time", "end_time", "is_off"])
    
    if not schedules:
        print(f"NO schedules found for {day_name}!")
    else:
        for s in schedules:
            print(f"Schedule: {s.therapist} - {s.start_time} to {s.end_time} (Off: {s.is_off})")

if __name__ == "__main__":
    frappe.connect()
    check_availability()
