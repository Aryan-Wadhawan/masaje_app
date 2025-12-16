
import frappe

def run():
    print("--- Setting up Sales Persons for Therapists ---")
    
    # Get all active Employees who are Therapists (assuming all employees for now/MVP)
    employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "employee_name"])
    
    # Get or Create Root Sales Person Node
    root_node = "Therapists"
    if not frappe.db.exists("Sales Person", root_node):
        doc = frappe.get_doc({
            "doctype": "Sales Person",
            "sales_person_name": root_node,
            "is_group": 1
        })
        doc.insert()
        print(f"Created Root Sales Person: {root_node}")
    
    for emp in employees:
        sp_name = emp.employee_name
        
        # specific naming convention if needed, e.g. SP-EMP-001
        
        existing = frappe.db.exists("Sales Person", {"employee": emp.name})
        if existing:
            print(f"Sales Person already exists for {emp.employee_name}: {existing}")
            continue
            
        try:
            doc = frappe.get_doc({
                "doctype": "Sales Person",
                "sales_person_name": sp_name,
                "parent_sales_person": root_node,
                "is_group": 0,
                "employee": emp.name, # Link to Employee
                "enabled": 1
            })
            doc.insert()
            print(f"Created Sales Person: {sp_name} linked to {emp.name}")
        except frappe.DuplicateEntryError:
             print(f"Sales Person duplicate error for {sp_name}")

    print("Sales Person Setup Complete.")
