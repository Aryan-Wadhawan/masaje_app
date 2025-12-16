"""
Clear All Test Data from Masaje App
This script removes all test/demo data to prepare for production data.

KEEPS:
- Users
- Branches  
- POS Profiles (configuration)
- Roles
- Permissions
- Accounts & Settings

DELETES:
- Service Bookings
- POS Invoices (draft and cancelled)
- POS Opening/Closing Entries
- Employees
- Therapist Schedules
- Customers
- Service Items (in Services/Packages groups)
- Item Prices for those items
- Sales Persons

Run: bench --site erpnext.localhost execute masaje_app.scripts.clear_all_data.clear_data
"""
import frappe


def clear_data():
    """Clear all test/demo data from the system."""
    print("=" * 60)
    print("CLEARING ALL TEST DATA")
    print("=" * 60)
    
    frappe.flags.in_migrate = True  # Disable some validations
    
    # 1. Delete Service Bookings (and linked POS Invoices via event)
    print("\n1. Deleting Service Bookings...")
    bookings = frappe.get_all("Service Booking", pluck="name")
    for name in bookings:
        try:
            frappe.delete_doc("Service Booking", name, force=True, ignore_permissions=True)
        except Exception as e:
            print(f"   Failed to delete {name}: {e}")
    print(f"   Deleted {len(bookings)} bookings")
    
    # 2. Delete POS Invoices (draft/cancelled only - submitted need to be cancelled first)
    print("\n2. Deleting POS Invoices...")
    # First cancel submitted ones
    submitted = frappe.get_all("POS Invoice", filters={"docstatus": 1}, pluck="name")
    for name in submitted:
        try:
            doc = frappe.get_doc("POS Invoice", name)
            doc.cancel()
        except Exception as e:
            print(f"   Failed to cancel {name}: {e}")
    print(f"   Cancelled {len(submitted)} submitted invoices")
    
    # Now delete all
    all_invoices = frappe.get_all("POS Invoice", pluck="name")
    for name in all_invoices:
        try:
            frappe.delete_doc("POS Invoice", name, force=True, ignore_permissions=True)
        except Exception as e:
            print(f"   Failed to delete {name}: {e}")
    print(f"   Deleted {len(all_invoices)} invoices")
    
    # 3. Delete POS Opening/Closing Entries
    print("\n3. Deleting POS Opening/Closing Entries...")
    closings = frappe.get_all("POS Closing Entry", pluck="name")
    for name in closings:
        try:
            doc = frappe.get_doc("POS Closing Entry", name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc("POS Closing Entry", name, force=True, ignore_permissions=True)
        except Exception as e:
            print(f"   Failed: {e}")
    print(f"   Deleted {len(closings)} closing entries")
    
    openings = frappe.get_all("POS Opening Entry", pluck="name")
    for name in openings:
        try:
            doc = frappe.get_doc("POS Opening Entry", name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc("POS Opening Entry", name, force=True, ignore_permissions=True)
        except Exception as e:
            print(f"   Failed: {e}")
    print(f"   Deleted {len(openings)} opening entries")
    
    # 4. Delete Therapist Schedules
    print("\n4. Deleting Therapist Schedules...")
    schedules = frappe.get_all("Therapist Schedule", pluck="name")
    for name in schedules:
        frappe.delete_doc("Therapist Schedule", name, force=True, ignore_permissions=True)
    print(f"   Deleted {len(schedules)} schedules")
    
    # 5. Delete Employees
    print("\n5. Deleting Employees...")
    employees = frappe.get_all("Employee", pluck="name")
    for name in employees:
        try:
            frappe.delete_doc("Employee", name, force=True, ignore_permissions=True)
        except Exception as e:
            print(f"   Failed to delete {name}: {e}")
    print(f"   Deleted {len(employees)} employees")
    
    # 6. Delete Customers
    print("\n6. Deleting Customers...")
    customers = frappe.get_all("Customer", pluck="name")
    for name in customers:
        try:
            frappe.delete_doc("Customer", name, force=True, ignore_permissions=True)
        except Exception as e:
            print(f"   Failed to delete {name}: {e}")
    print(f"   Deleted {len(customers)} customers")
    
    # 7. Delete Service Items (in Services or Packages group)
    print("\n7. Deleting Service Items...")
    items = frappe.get_all("Item", filters={"item_group": ["in", ["Services", "Packages"]]}, pluck="name")
    for name in items:
        try:
            # Delete item prices first
            prices = frappe.get_all("Item Price", filters={"item_code": name}, pluck="name")
            for price in prices:
                frappe.delete_doc("Item Price", price, force=True, ignore_permissions=True)
            frappe.delete_doc("Item", name, force=True, ignore_permissions=True)
        except Exception as e:
            print(f"   Failed to delete {name}: {e}")
    print(f"   Deleted {len(items)} service items")
    
    # 8. Delete Sales Persons (if any linked to employees)
    print("\n8. Deleting Sales Persons...")
    sales_persons = frappe.get_all("Sales Person", filters={"is_group": 0}, pluck="name")
    for name in sales_persons:
        try:
            frappe.delete_doc("Sales Person", name, force=True, ignore_permissions=True)
        except Exception as e:
            print(f"   Failed to delete {name}: {e}")
    print(f"   Deleted {len(sales_persons)} sales persons")
    
    frappe.db.commit()
    frappe.flags.in_migrate = False
    
    print("\n" + "=" * 60)
    print("DATA CLEARED SUCCESSFULLY!")
    print("=" * 60)
    print("\nKept: Users, Branches, POS Profiles, Roles, Settings")
    print("Ready for production data entry.")


if __name__ == "__main__":
    clear_data()
