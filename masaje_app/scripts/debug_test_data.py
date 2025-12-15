
import frappe
from frappe.utils import today, add_days, get_datetime

def execute():
    branch = "Test Branch Debug"
    
    # 1. Create Branch
    if not frappe.db.exists("Branch", branch):
        frappe.get_doc({"doctype": "Branch", "branch": branch}).insert()
        print(f"Created Branch: {branch}")

    # 2. Create Therapist
    name = "Therapist Debug"
    if not frappe.db.exists("Employee", {"employee_name": name}):
        emp = frappe.get_doc({
            "doctype": "Employee",
            "first_name": name,
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "date_of_joining": "2020-01-01",
            "branch": branch,
            "status": "Active"
        })
        emp.insert()
        print(f"Created Employee: {emp.name}")
    else:
        emp_name = frappe.db.get_value("Employee", {"employee_name": name}, "name")
        print(f"Employee exists: {emp_name}")
        # Ensure branch
        frappe.db.set_value("Employee", emp_name, "branch", branch)

    emp_name = frappe.db.get_value("Employee", {"employee_name": name}, "name")

    # 3. Create Schedule
    if not frappe.db.exists("Therapist Schedule", {"therapist": emp_name, "day_of_week": "Monday"}):
        frappe.get_doc({
            "doctype": "Therapist Schedule",
            "therapist": emp_name,
            "day_of_week": "Monday",
            "start_time": "09:00:00",
            "end_time": "18:00:00",
            "is_off": 0
        }).insert()
        print("Created Schedule")
    else:
        print("Schedule exists")

    # 4. Test Query
    working_therapists = frappe.db.sql("""
        SELECT ts.therapist, ts.start_time, ts.end_time 
        FROM `tabTherapist Schedule` ts
        JOIN `tabEmployee` emp ON ts.therapist = emp.name
        WHERE ts.day_of_week = %s 
        AND emp.branch = %s
        AND ts.is_off = 0
        AND emp.status = 'Active'
    """, ("Monday", branch), as_dict=True)
    
    print(f"Working Therapists Found: {len(working_therapists)}")
    print(working_therapists)
