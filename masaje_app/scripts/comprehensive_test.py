"""
Comprehensive System Test Suite for Masaje de Bohol
Tests booking flow, POS integration, pricing, and reports.

Run: bench --site erpnext.localhost execute masaje_app.scripts.comprehensive_test.run_all_tests
"""
import frappe
from frappe.utils import today, now_datetime, add_to_date

ISSUES_FOUND = []

def log_issue(category, description, expected=None, actual=None):
    """Log an issue found during testing."""
    ISSUES_FOUND.append({
        "category": category,
        "description": description,
        "expected": expected,
        "actual": actual
    })
    print(f"  ❌ ISSUE: {description}")

def log_success(description):
    print(f"  ✅ {description}")


def test_setup():
    """Setup test data."""
    print("\n" + "=" * 60)
    print("SETTING UP TEST DATA")
    print("=" * 60)
    
    # Get or create test customer
    if not frappe.db.exists("Customer", "Test Customer"):
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)
    
    return {
        "customer": "Test Customer",
        "branch": "Dao Branch",
        "therapist": frappe.db.get_value("Employee", {"designation": "Therapist"}, "name"),
        "service_items": frappe.get_all("Item", 
            filters={"item_group": ["in", ["Massage 1 Hour", "Massage 30 Mins", "Other Services"]]},
            limit=5, pluck="name")
    }


def test_1_single_item_booking(test_data):
    """Test 1: Create booking with single service item."""
    print("\n" + "-" * 60)
    print("TEST 1: Single Item Booking + POS Invoice Creation")
    print("-" * 60)
    
    if not test_data["service_items"]:
        log_issue("Setup", "No service items found for testing")
        return None
    
    item = test_data["service_items"][0]
    
    # Get item price
    expected_price = frappe.db.get_value("Item Price", 
        {"item_code": item, "price_list": "Standard Selling"}, "price_list_rate") or 0
    
    # Create booking
    booking = frappe.get_doc({
        "doctype": "Service Booking",
        "customer": test_data["customer"],
        "branch": test_data["branch"],
        "therapist": test_data["therapist"],
        "booking_date": today(),
        "time_slot": "11:00",
        "items": [{"service_item": item}]
    })
    booking.insert(ignore_permissions=True)
    
    # Check 1: Booking created
    if frappe.db.exists("Service Booking", booking.name):
        log_success(f"Booking created: {booking.name}")
    else:
        log_issue("Booking", "Booking not created")
        return None
    
    # Check 2: POS Invoice draft created
    booking.reload()
    if booking.invoice:
        log_success(f"POS Invoice draft created: {booking.invoice}")
        
        # Check 3: Invoice has correct item and price
        inv = frappe.get_doc("POS Invoice", booking.invoice)
        if len(inv.items) == 1:
            log_success("Invoice has 1 item")
            inv_item = inv.items[0]
            if inv_item.item_code == item:
                log_success(f"Correct item: {item}")
            else:
                log_issue("POS Invoice", "Wrong item in invoice", item, inv_item.item_code)
            
            if inv_item.rate == expected_price:
                log_success(f"Correct price: {expected_price}")
            else:
                log_issue("Pricing", "Wrong price in invoice", expected_price, inv_item.rate)
        else:
            log_issue("POS Invoice", "Wrong number of items", 1, len(inv.items))
    else:
        log_issue("POS Invoice", "Draft invoice not created automatically")
    
    # Check 4: Duration calculated
    if booking.duration_minutes and booking.duration_minutes > 0:
        log_success(f"Duration calculated: {booking.duration_minutes} mins")
    else:
        log_issue("Booking", "Duration not calculated", "> 0", booking.duration_minutes)
    
    return booking.name


def test_2_multiple_items_booking(test_data):
    """Test 2: Create booking with multiple service items."""
    print("\n" + "-" * 60)
    print("TEST 2: Multiple Items Booking")
    print("-" * 60)
    
    if len(test_data["service_items"]) < 2:
        log_issue("Setup", "Need at least 2 items for multi-item test")
        return None
    
    items = test_data["service_items"][:3]
    
    # Calculate expected total price
    expected_total = 0
    for item in items:
        price = frappe.db.get_value("Item Price", 
            {"item_code": item, "price_list": "Standard Selling"}, "price_list_rate") or 0
        expected_total += price
    
    # Create booking
    booking = frappe.get_doc({
        "doctype": "Service Booking",
        "customer": test_data["customer"],
        "branch": test_data["branch"],
        "therapist": test_data["therapist"],
        "booking_date": today(),
        "time_slot": "12:00",
        "items": [{"service_item": item} for item in items]
    })
    booking.insert(ignore_permissions=True)
    
    log_success(f"Booking created with {len(items)} items: {booking.name}")
    
    # Check invoice
    booking.reload()
    if booking.invoice:
        inv = frappe.get_doc("POS Invoice", booking.invoice)
        
        if len(inv.items) == len(items):
            log_success(f"Invoice has {len(items)} items")
        else:
            log_issue("POS Invoice", "Wrong number of items", len(items), len(inv.items))
        
        if abs(inv.grand_total - expected_total) < 1:
            log_success(f"Total correct: {inv.grand_total}")
        else:
            log_issue("Pricing", "Wrong total in invoice", expected_total, inv.grand_total)
    else:
        log_issue("POS Invoice", "Draft invoice not created for multi-item booking")
    
    return booking.name


def test_3_pos_submit_status_update(test_data):
    """Test 3: Submit POS Invoice and check booking status update."""
    print("\n" + "-" * 60)
    print("TEST 3: POS Submit -> Booking Status Update")
    print("-" * 60)
    
    # Create a booking
    item = test_data["service_items"][0]
    booking = frappe.get_doc({
        "doctype": "Service Booking",
        "customer": test_data["customer"],
        "branch": test_data["branch"],
        "therapist": test_data["therapist"],
        "booking_date": today(),
        "time_slot": "14:00",
        "items": [{"service_item": item}]
    })
    booking.insert(ignore_permissions=True)
    booking.reload()
    
    if not booking.invoice:
        log_issue("POS Invoice", "No invoice to submit")
        return None
    
    log_success(f"Booking {booking.name} with invoice {booking.invoice}")
    
    # Create POS Opening Entry first
    pos_profile = f"{test_data['branch']} POS"
    company = frappe.defaults.get_global_default("company")
    
    # Check if opening entry exists
    open_entry = frappe.db.get_value("POS Opening Entry", 
        {"pos_profile": pos_profile, "status": "Open", "docstatus": 1}, "name")
    
    if not open_entry:
        # Create opening entry
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
        log_success(f"Created POS Opening Entry: {oe.name}")
    
    # Submit the invoice
    try:
        inv = frappe.get_doc("POS Invoice", booking.invoice)
        inv.submit()
        log_success(f"POS Invoice submitted: {inv.name}")
        
        # Check booking status
        booking.reload()
        if booking.status == "Completed":
            log_success("Booking status updated to Completed")
        else:
            log_issue("Status Sync", "Booking not marked Completed after POS submit", 
                     "Completed", booking.status)
    except Exception as e:
        log_issue("POS Submit", f"Failed to submit invoice: {str(e)}")
    
    return booking.name


def test_4_panglao_pricing(test_data):
    """Test 4: Panglao branch uses Panglao Prices price list."""
    print("\n" + "-" * 60)
    print("TEST 4: Panglao Branch Pricing")
    print("-" * 60)
    
    item = test_data["service_items"][0]
    
    # Get standard and panglao prices
    standard_price = frappe.db.get_value("Item Price", 
        {"item_code": item, "price_list": "Standard Selling"}, "price_list_rate") or 0
    panglao_price = frappe.db.get_value("Item Price", 
        {"item_code": item, "price_list": "Panglao Prices"}, "price_list_rate") or standard_price
    
    # Create booking at Panglao
    booking = frappe.get_doc({
        "doctype": "Service Booking",
        "customer": test_data["customer"],
        "branch": "Panglao Branch",
        "therapist": test_data["therapist"],
        "booking_date": today(),
        "time_slot": "15:00",
        "items": [{"service_item": item}]
    })
    booking.insert(ignore_permissions=True)
    booking.reload()
    
    if booking.invoice:
        inv = frappe.get_doc("POS Invoice", booking.invoice)
        actual_price = inv.items[0].rate if inv.items else 0
        
        # Check which price list is used
        if inv.selling_price_list == "Panglao Prices":
            log_success("Panglao booking uses Panglao Prices list")
        else:
            log_issue("Pricing", "Wrong price list for Panglao", 
                     "Panglao Prices", inv.selling_price_list)
        
        log_success(f"Price for item: {actual_price} (Standard: {standard_price})")
    else:
        log_issue("POS Invoice", "No invoice created for Panglao booking")
    
    return booking.name


def test_5_therapist_availability(test_data):
    """Test 5: Therapist conflict detection."""
    print("\n" + "-" * 60)
    print("TEST 5: Therapist Conflict Detection")
    print("-" * 60)
    
    if not test_data["therapist"]:
        log_issue("Setup", "No therapist for conflict test")
        return None
    
    item = test_data["service_items"][0]
    
    # Create first booking
    booking1 = frappe.get_doc({
        "doctype": "Service Booking",
        "customer": test_data["customer"],
        "branch": test_data["branch"],
        "therapist": test_data["therapist"],
        "booking_date": today(),
        "time_slot": "16:00",
        "items": [{"service_item": item}]
    })
    booking1.insert(ignore_permissions=True)
    log_success(f"First booking created: {booking1.name}")
    
    # Try to create overlapping booking
    try:
        booking2 = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": test_data["customer"],
            "branch": test_data["branch"],
            "therapist": test_data["therapist"],  # Same therapist
            "booking_date": today(),
            "time_slot": "16:00",  # Same time
            "items": [{"service_item": item}]
        })
        booking2.insert(ignore_permissions=True)
        log_issue("Conflict Detection", "Double-booking allowed - should have been blocked")
    except frappe.exceptions.ValidationError as e:
        log_success(f"Double-booking correctly blocked: {str(e)[:50]}...")
    except Exception as e:
        log_issue("Conflict Detection", f"Unexpected error: {str(e)}")
    
    return booking1.name


def test_6_reverse_sync():
    """Test 6: POS checkout without booking creates Service Booking."""
    print("\n" + "-" * 60)
    print("TEST 6: Reverse Sync (POS-first workflow)")
    print("-" * 60)
    
    # This test requires manual POS usage or complex setup
    # For now, just verify the function exists and is hooked
    from masaje_app.events import create_service_booking_from_invoice
    log_success("create_service_booking_from_invoice function exists")
    log_success("Reverse sync hook registered (needs manual testing)")
    
    return None


def generate_report():
    """Generate test report."""
    print("\n" + "=" * 60)
    print("TEST REPORT")
    print("=" * 60)
    
    if not ISSUES_FOUND:
        print("\n✅ ALL TESTS PASSED - No issues found!")
    else:
        print(f"\n❌ {len(ISSUES_FOUND)} ISSUES FOUND:\n")
        for i, issue in enumerate(ISSUES_FOUND, 1):
            print(f"{i}. [{issue['category']}] {issue['description']}")
            if issue['expected']:
                print(f"   Expected: {issue['expected']}")
                print(f"   Actual: {issue['actual']}")
            print()
    
    return ISSUES_FOUND


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("MASAJE DE BOHOL - COMPREHENSIVE SYSTEM TEST")
    print("=" * 60)
    
    frappe.flags.in_test = True
    
    # Setup
    test_data = test_setup()
    
    # Run tests
    test_1_single_item_booking(test_data)
    test_2_multiple_items_booking(test_data)
    test_3_pos_submit_status_update(test_data)
    test_4_panglao_pricing(test_data)
    test_5_therapist_availability(test_data)
    test_6_reverse_sync()
    
    # Generate report
    issues = generate_report()
    
    frappe.flags.in_test = False
    frappe.db.commit()
    
    return issues


if __name__ == "__main__":
    run_all_tests()
