"""
Masaje de Bohol - Comprehensive Regression Test Suite
=====================================================

Run all tests:
    bench --site erpnext.localhost execute masaje_app.tests.test_suite.run_all_tests

Run specific test groups:
    bench --site erpnext.localhost execute masaje_app.tests.test_suite.test_booking_flow
    bench --site erpnext.localhost execute masaje_app.tests.test_suite.test_branch_isolation
    bench --site erpnext.localhost execute masaje_app.tests.test_suite.test_reports
"""
import frappe
from frappe.utils import today, now_datetime

# Test configuration
TEST_BRANCHES = [
    ("CPG East Branch", "cpgeast.receptionist@masajedebohol.com"),
    ("Dao Branch", "dao.receptionist@masajedebohol.com"),
    ("Calceta Branch", "calceta.receptionist@masajedebohol.com"),
    ("Port Branch", "port.receptionist@masajedebohol.com"),
    ("Panglao Branch", "panglao.receptionist@masajedebohol.com"),
]

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def log_pass(self, test_name):
        self.passed += 1
        print(f"  ✅ {test_name}")
    
    def log_fail(self, test_name, reason=""):
        self.failed += 1
        self.errors.append(f"{test_name}: {reason}")
        print(f"  ❌ {test_name}: {reason}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"RESULTS: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print("\nFailures:")
            for e in self.errors:
                print(f"  - {e}")
        print(f"{'='*60}")
        return self.failed == 0


# =============================================================================
# TEST GROUP 1: BOOKING FLOW
# =============================================================================

def test_booking_flow():
    """Test the complete booking workflow including approval and POS invoice creation."""
    results = TestResults()
    print("\n" + "="*60)
    print("TEST GROUP: BOOKING FLOW")
    print("="*60)
    
    # Setup
    setup_pos_session("Dao Branch POS")
    
    # Test 1: Create booking with Pending status (no invoice)
    print("\n1. Create Pending Booking...")
    try:
        booking = create_test_booking("Dao Branch", status="Pending")
        if not booking.invoice:
            results.log_pass("Pending booking has no invoice")
        else:
            results.log_fail("Pending booking has no invoice", f"Invoice created: {booking.invoice}")
    except Exception as e:
        results.log_fail("Create Pending Booking", str(e))
        return results
    
    # Test 2: Change to Approved (should create invoice)
    print("\n2. Approve Booking...")
    try:
        booking.status = "Approved"
        booking.save(ignore_permissions=True)
        booking.reload()
        if booking.invoice:
            results.log_pass(f"Approved booking has invoice: {booking.invoice}")
        else:
            results.log_fail("Approved booking has invoice", "No invoice created")
    except Exception as e:
        results.log_fail("Approve Booking", str(e))
    
    # Test 3: Invoice has correct items and price
    print("\n3. Verify Invoice Details...")
    if booking.invoice:
        try:
            inv = frappe.get_doc("POS Invoice", booking.invoice)
            if len(inv.items) > 0:
                results.log_pass(f"Invoice has {len(inv.items)} item(s)")
            else:
                results.log_fail("Invoice has items", "No items")
            
            if inv.grand_total > 0:
                results.log_pass(f"Invoice total: {inv.grand_total}")
            else:
                results.log_fail("Invoice total > 0", f"Total: {inv.grand_total}")
        except Exception as e:
            results.log_fail("Verify Invoice", str(e))
    
    # Test 4: Cancel booking deletes draft invoice
    print("\n4. Cancel Booking...")
    invoice_name = booking.invoice
    try:
        booking.status = "Cancelled"
        booking.save(ignore_permissions=True)
        
        if not frappe.db.exists("POS Invoice", invoice_name):
            results.log_pass("Draft invoice deleted on cancel")
        else:
            results.log_fail("Draft invoice deleted", f"Invoice still exists: {invoice_name}")
    except Exception as e:
        results.log_fail("Cancel Booking", str(e))
    
    # Cleanup
    cleanup_test_booking(booking.name)
    
    return results


# =============================================================================
# TEST GROUP 2: BRANCH ISOLATION
# =============================================================================

def test_branch_isolation():
    """Test that receptionists can only see their own branch data."""
    results = TestResults()
    print("\n" + "="*60)
    print("TEST GROUP: BRANCH ISOLATION")
    print("="*60)
    
    # Setup test data for 2 branches
    setup_pos_session("CPG East Branch POS")
    setup_pos_session("Dao Branch POS")
    
    booking1 = create_test_booking("CPG East Branch", status="Approved", time_slot="06:00")
    booking2 = create_test_booking("Dao Branch", status="Approved", time_slot="06:30")
    frappe.db.commit()
    
    print(f"\nCreated: {booking1.name} (CPG East), {booking2.name} (Dao)")
    
    # Test CPG East receptionist
    print("\n1. Testing CPG East Receptionist...")
    frappe.set_user("cpgeast.receptionist@masajedebohol.com")
    cpg_visible = frappe.get_list("Service Booking", 
        filters={"booking_date": today()}, 
        fields=["name", "branch"])
    
    own_cpg = [b for b in cpg_visible if b.branch == "CPG East Branch"]
    other_cpg = [b for b in cpg_visible if b.branch != "CPG East Branch"]
    
    if own_cpg and not other_cpg:
        results.log_pass(f"Sees only CPG East ({len(own_cpg)} booking(s))")
    else:
        results.log_fail("Sees only own branch", f"Own: {len(own_cpg)}, Other: {len(other_cpg)}")
    
    # Test Dao receptionist
    print("\n2. Testing Dao Receptionist...")
    frappe.set_user("dao.receptionist@masajedebohol.com")
    dao_visible = frappe.get_list("Service Booking", 
        filters={"booking_date": today()}, 
        fields=["name", "branch"])
    
    own_dao = [b for b in dao_visible if b.branch == "Dao Branch"]
    other_dao = [b for b in dao_visible if b.branch != "Dao Branch"]
    
    if own_dao and not other_dao:
        results.log_pass(f"Sees only Dao ({len(own_dao)} booking(s))")
    else:
        results.log_fail("Sees only own branch", f"Own: {len(own_dao)}, Other: {len(other_dao)}")
    
    # Test Employee visibility (should see all)
    print("\n3. Testing Employee Visibility...")
    total_employees = frappe.db.count("Employee", {"status": "Active"})
    visible_employees = len(frappe.get_list("Employee", filters={"status": "Active"}, limit=200))
    
    if visible_employees >= total_employees * 0.9:
        results.log_pass(f"Can see all employees ({visible_employees})")
    else:
        results.log_fail("Can see all employees", f"Only sees {visible_employees}/{total_employees}")
    
    frappe.set_user("Administrator")
    
    # Cleanup
    cleanup_test_booking(booking1.name)
    cleanup_test_booking(booking2.name)
    
    return results


# =============================================================================
# TEST GROUP 3: REPORTS
# =============================================================================

def test_reports():
    """Test all custom reports execute without errors."""
    results = TestResults()
    print("\n" + "="*60)
    print("TEST GROUP: REPORTS")
    print("="*60)
    
    filters = {"from_date": today(), "to_date": today()}
    
    # Test Daily Branch Sales
    print("\n1. Daily Branch Sales Report...")
    try:
        from masaje_app.report.daily_branch_sales.daily_branch_sales import execute
        result = execute(filters)
        if result and len(result) >= 2:
            results.log_pass(f"Returns valid data (columns={len(result[0])}, rows={len(result[1])})")
        else:
            results.log_fail("Returns valid data", "Invalid result format")
    except Exception as e:
        results.log_fail("Daily Branch Sales", str(e))
    
    # Test Therapist Utilization
    print("\n2. Therapist Utilization Report...")
    try:
        from masaje_app.report.therapist_utilization.therapist_utilization import execute
        result = execute(filters)
        if result and len(result) >= 2:
            results.log_pass(f"Returns valid data (columns={len(result[0])}, rows={len(result[1])})")
        else:
            results.log_fail("Returns valid data", "Invalid result format")
    except Exception as e:
        results.log_fail("Therapist Utilization", str(e))
    
    return results


# =============================================================================
# TEST GROUP 4: PERMISSIONS
# =============================================================================

def test_permissions():
    """Test role and permission configuration."""
    results = TestResults()
    print("\n" + "="*60)
    print("TEST GROUP: PERMISSIONS")
    print("="*60)
    
    print("\n1. Checking Receptionist User Permissions...")
    for branch, email in TEST_BRANCHES:
        perms = frappe.get_all("User Permission",
            filters={"user": email, "allow": "Branch"},
            fields=["applicable_for"])
        
        doctypes_restricted = [p.applicable_for for p in perms]
        
        if "Service Booking" in doctypes_restricted and "POS Invoice" in doctypes_restricted:
            results.log_pass(f"{email.split('@')[0]}: Restricted for both doctypes")
        else:
            results.log_fail(f"{email.split('@')[0]}", f"Missing restrictions: {doctypes_restricted}")
    
    print("\n2. Checking Receptionist Roles...")
    for branch, email in TEST_BRANCHES:
        roles = frappe.get_all("Has Role", filters={"parent": email}, pluck="role")
        
        has_receptionist = "Receptionist" in roles
        has_sales_user = "Sales User" in roles
        
        if has_receptionist and has_sales_user:
            results.log_pass(f"{email.split('@')[0]}: Has required roles")
        else:
            results.log_fail(f"{email.split('@')[0]}", 
                f"Receptionist={has_receptionist}, Sales User={has_sales_user}")
    
    return results


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def setup_pos_session(pos_profile):
    """Ensure POS Opening Entry exists for the profile."""
    if frappe.db.exists("POS Opening Entry", 
        {"pos_profile": pos_profile, "status": "Open", "docstatus": 1}):
        return
    
    try:
        company = frappe.defaults.get_global_default("company")
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
    except:
        pass  # May already exist


def create_test_booking(branch, status="Pending", time_slot="07:00"):
    """Create a test Service Booking."""
    # Ensure test customer exists
    if not frappe.db.exists("Customer", "Test Customer"):
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)
    
    # Get a service item
    item = frappe.db.get_value("Item", {"item_group": "Massage 1 Hour"}, "name") or "Du-ot"
    
    booking = frappe.get_doc({
        "doctype": "Service Booking",
        "customer": "Test Customer",
        "branch": branch,
        "booking_date": today(),
        "time_slot": time_slot,
        "status": status,
        "items": [{"service_item": item}]
    })
    booking.insert(ignore_permissions=True)
    booking.reload()
    return booking


def cleanup_test_booking(booking_name):
    """Clean up a test booking and its linked invoice."""
    try:
        booking = frappe.get_doc("Service Booking", booking_name)
        if booking.invoice:
            inv_status = frappe.db.get_value("POS Invoice", booking.invoice, "docstatus")
            if inv_status == 0:
                frappe.delete_doc("POS Invoice", booking.invoice, force=True, ignore_permissions=True)
        frappe.delete_doc("Service Booking", booking_name, force=True, ignore_permissions=True)
    except:
        pass


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all test groups."""
    print("="*60)
    print("MASAJE DE BOHOL - REGRESSION TEST SUITE")
    print("="*60)
    print(f"Date: {today()}")
    print(f"User: {frappe.session.user}")
    
    all_results = []
    
    # Run all test groups
    all_results.append(("Booking Flow", test_booking_flow()))
    all_results.append(("Branch Isolation", test_branch_isolation()))
    all_results.append(("Reports", test_reports()))
    all_results.append(("Permissions", test_permissions()))
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    total_passed = sum(r[1].passed for r in all_results)
    total_failed = sum(r[1].failed for r in all_results)
    
    for name, result in all_results:
        status = "✅" if result.failed == 0 else "❌"
        print(f"  {status} {name}: {result.passed} passed, {result.failed} failed")
    
    print(f"\nTOTAL: {total_passed} passed, {total_failed} failed")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  SOME TESTS FAILED - Review errors above")
    
    frappe.db.commit()
    return total_failed == 0


if __name__ == "__main__":
    run_all_tests()
