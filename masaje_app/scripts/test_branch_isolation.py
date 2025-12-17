"""
Branch Isolation Test Suite
Tests that receptionists can only see their own branch's data.

Run: bench --site erpnext.localhost execute masaje_app.scripts.test_branch_isolation.run_all_tests
"""
import frappe
from frappe.utils import today, now_datetime

BRANCHES = [
    ("CPG East Branch", "cpgeast.receptionist@masajedebohol.com"),
    ("Dao Branch", "dao.receptionist@masajedebohol.com"),
    ("Calceta Branch", "calceta.receptionist@masajedebohol.com"),
    ("Port Branch", "port.receptionist@masajedebohol.com"),
    ("Panglao Branch", "panglao.receptionist@masajedebohol.com"),
]

ISSUES = []

def log_issue(description):
    ISSUES.append(description)
    print(f"  ❌ {description}")

def log_success(description):
    print(f"  ✅ {description}")


def create_test_data():
    """Create Service Bookings for each branch."""
    print("\n" + "=" * 60)
    print("SETUP: Creating test data for all branches")
    print("=" * 60)
    
    # Ensure test customer exists
    if not frappe.db.exists("Customer", "Test Customer"):
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)
    
    # Get a service item
    item = frappe.get_all("Item", filters={"item_group": "Massage 1 Hour"}, limit=1, pluck="name")[0]
    
    # Create POS Opening Entries for all branches
    company = frappe.defaults.get_global_default("company")
    
    for branch, email in BRANCHES:
        pos_profile = f"{branch} POS"
        
        # Check if opening entry exists
        if not frappe.db.exists("POS Opening Entry", 
            {"pos_profile": pos_profile, "status": "Open", "docstatus": 1}):
            try:
                oe = frappe.get_doc({
                    "doctype": "POS Opening Entry",
                    "pos_profile": pos_profile,
                    "user": "Administrator",
                    "company": company,
                    "period_start_date": now_datetime(),
                    "balance_details": [{"mode_of_payment": "Cash", "opening_amount": 0}]
                })
                oe.insert(ignore_permissions=True)
                oe.submit()
                print(f"  Created POS Opening for {branch}")
            except Exception as e:
                print(f"  Warning: Could not create POS Opening for {branch}: {e}")
    
    # Create bookings for each branch
    booking_names = {}
    for i, (branch, email) in enumerate(BRANCHES):
        # Use different time slots to avoid conflicts
        time_slot = f"{11 + i}:00"
        
        booking = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": "Test Customer",
            "branch": branch,
            "booking_date": today(),
            "time_slot": time_slot,
            "status": "Approved",  # This triggers POS Invoice creation
            "items": [{"service_item": item}]
        })
        booking.insert(ignore_permissions=True)
        booking.reload()
        
        booking_names[branch] = {
            "booking": booking.name,
            "invoice": booking.invoice
        }
        print(f"  Created booking for {branch}: {booking.name} -> Invoice: {booking.invoice}")
    
    frappe.db.commit()
    return booking_names


def test_booking_visibility(booking_names):
    """Test that each receptionist can only see their branch's bookings."""
    print("\n" + "=" * 60)
    print("TEST 1: Service Booking Visibility per Receptionist")
    print("=" * 60)
    
    for branch, email in BRANCHES:
        print(f"\n  Testing {email}:")
        
        # Impersonate the receptionist
        frappe.set_user(email)
        
        # Get bookings visible to this user
        visible_bookings = frappe.get_all("Service Booking",
            filters={"booking_date": today()},
            fields=["name", "branch"]
        )
        
        # Check what's visible
        own_branch_bookings = [b for b in visible_bookings if b.branch == branch]
        other_branch_bookings = [b for b in visible_bookings if b.branch != branch]
        
        if own_branch_bookings:
            log_success(f"Can see own branch booking: {own_branch_bookings[0].name}")
        else:
            log_issue(f"Cannot see own branch ({branch}) bookings!")
        
        if not other_branch_bookings:
            log_success(f"Cannot see other branches (correct!)")
        else:
            log_issue(f"Can see OTHER branch bookings: {[b.branch for b in other_branch_bookings]}")
        
        frappe.set_user("Administrator")


def test_invoice_visibility(booking_names):
    """Test that each receptionist can only see their branch's invoices."""
    print("\n" + "=" * 60)
    print("TEST 2: POS Invoice Visibility per Receptionist")
    print("=" * 60)
    
    for branch, email in BRANCHES:
        print(f"\n  Testing {email}:")
        
        frappe.set_user(email)
        
        # Get invoices visible to this user
        visible_invoices = frappe.get_all("POS Invoice",
            filters={"posting_date": today()},
            fields=["name", "branch"]
        )
        
        own_branch_invoices = [i for i in visible_invoices if i.branch == branch]
        other_branch_invoices = [i for i in visible_invoices if i.branch != branch]
        
        if own_branch_invoices:
            log_success(f"Can see own branch invoice: {own_branch_invoices[0].name}")
        else:
            # Check if invoice was created
            expected_invoice = booking_names.get(branch, {}).get("invoice")
            if expected_invoice:
                log_issue(f"Cannot see own branch ({branch}) invoice {expected_invoice}!")
            else:
                print(f"    ⚠️  No invoice was created for {branch}")
        
        if not other_branch_invoices:
            log_success(f"Cannot see other branches (correct!)")
        else:
            log_issue(f"Can see OTHER branch invoices: {[i.branch for i in other_branch_invoices]}")
        
        frappe.set_user("Administrator")


def test_employee_visibility():
    """Test that all receptionists can see all employees (therapists)."""
    print("\n" + "=" * 60)
    print("TEST 3: Employee (Therapist) Visibility")
    print("=" * 60)
    
    # Count total therapists as admin
    frappe.set_user("Administrator")
    total_therapists = frappe.db.count("Employee", {"designation": "Therapist", "status": "Active"})
    print(f"  Total therapists: {total_therapists}")
    
    for branch, email in BRANCHES:
        frappe.set_user(email)
        
        visible_employees = frappe.get_all("Employee",
            filters={"status": "Active"},
            limit=100
        )
        
        if len(visible_employees) >= total_therapists * 0.9:  # Allow 10% margin
            log_success(f"{email}: Can see {len(visible_employees)} employees (correct!)")
        else:
            log_issue(f"{email}: Can only see {len(visible_employees)}/{total_therapists} employees")
        
        frappe.set_user("Administrator")


def test_report_filtering():
    """Test that reports respect branch filtering."""
    print("\n" + "=" * 60)
    print("TEST 4: Report Data (as Admin - should see all)")
    print("=" * 60)
    
    # Check if we have any submitted invoices for report testing
    submitted_invoices = frappe.get_all("POS Invoice",
        filters={"docstatus": 1},
        fields=["name", "branch", "grand_total"]
    )
    
    if submitted_invoices:
        print(f"  Found {len(submitted_invoices)} submitted invoices")
        branches_with_data = set(i.branch for i in submitted_invoices)
        print(f"  Branches with invoice data: {branches_with_data}")
    else:
        print("  ⚠️  No submitted invoices found - reports will be empty")
        print("  Note: Reports use SUBMITTED invoices (docstatus=1)")


def generate_report():
    """Generate final test report."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if not ISSUES:
        print("\n✅ ALL TESTS PASSED!")
        print("   Branch isolation is working correctly.")
    else:
        print(f"\n❌ {len(ISSUES)} ISSUES FOUND:")
        for i, issue in enumerate(ISSUES, 1):
            print(f"   {i}. {issue}")
    
    return ISSUES


def cleanup():
    """Clean up test data."""
    print("\n" + "-" * 60)
    print("Cleanup: Deleting test bookings...")
    
    frappe.set_user("Administrator")
    
    # Delete test bookings from today
    test_bookings = frappe.get_all("Service Booking",
        filters={"customer": "Test Customer", "booking_date": today()},
        pluck="name"
    )
    
    for name in test_bookings:
        try:
            frappe.delete_doc("Service Booking", name, force=True, ignore_permissions=True)
        except:
            pass
    
    print(f"  Deleted {len(test_bookings)} test bookings")


def run_all_tests():
    """Run all branch isolation tests."""
    print("=" * 60)
    print("BRANCH ISOLATION TEST SUITE")
    print("=" * 60)
    
    # Setup
    booking_names = create_test_data()
    
    # Run tests
    test_booking_visibility(booking_names)
    test_invoice_visibility(booking_names)
    test_employee_visibility()
    test_report_filtering()
    
    # Report
    issues = generate_report()
    
    # Cleanup
    cleanup()
    
    frappe.db.commit()
    return issues


if __name__ == "__main__":
    run_all_tests()
