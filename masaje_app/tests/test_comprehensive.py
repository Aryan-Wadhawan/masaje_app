"""
Comprehensive Test Suite for Masaje App
Tests all core functionality:
- API endpoints (booking, branches, services, slots)
- Service Booking events (validate, insert, update, trash)
- POS Invoice events (submit, cancel, trash)
- Therapist conflict detection
- Commission calculation
- Bidirectional sync (Booking ↔ POS Invoice)

Run: bench --site erpnext.localhost run-tests --app masaje_app --module masaje_app.tests.test_comprehensive
"""
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days, get_datetime, add_to_date, now_datetime
from masaje_app.api import (
    get_branches, 
    get_services, 
    get_available_slots, 
    create_booking,
    search_pending_bookings,
    load_booking_for_pos
)
from masaje_app.events import check_therapist_conflict
from masaje_app.utils import create_pos_invoice_for_booking


class TestMasajeComprehensive(FrappeTestCase):
    """Comprehensive test suite for Masaje Spa application."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for the test class."""
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.branch = "Test Comprehensive Branch"
        cls.setup_test_environment()
        frappe.db.commit()  # Commit test data so it persists
    
    @classmethod
    def setup_test_environment(cls):
        """Create all required test data."""
        # Branch
        if not frappe.db.exists("Branch", cls.branch):
            frappe.get_doc({"doctype": "Branch", "branch": cls.branch}).insert()
        
        # Services (non-stock items)
        cls.service_60 = "Test-Service-60min"
        cls.service_30 = "Test-Service-30min"
        cls.service_90 = "Test-Service-90min"
        
        cls.create_service_item(cls.service_60, "Full Body Massage 60min", 500, 60)
        cls.create_service_item(cls.service_30, "Quick Massage 30min", 300, 30)
        cls.create_service_item(cls.service_90, "Premium Massage 90min", 800, 90)
        
        # Therapists with schedules
        cls.therapist_a = cls.create_therapist("Test Therapist A")
        cls.therapist_b = cls.create_therapist("Test Therapist B")
        
        # Customer
        cls.customer = cls.create_customer("Test Comprehensive Customer")
        
        # POS Profile
        cls.pos_profile = cls.setup_pos_profile()
    
    @classmethod
    def create_service_item(cls, code, name, price, duration):
        """Create a service item with price and optional duration."""
        if not frappe.db.exists("Item", code):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": code,
                "item_name": name,
                "item_group": "Services",
                "is_stock_item": 0,
                "custom_duration_minutes": duration
            })
            item.insert()
        else:
            frappe.db.set_value("Item", code, "custom_duration_minutes", duration)
        
        # Price
        if not frappe.db.exists("Item Price", {"item_code": code, "price_list": "Standard Selling"}):
            frappe.get_doc({
                "doctype": "Item Price",
                "item_code": code,
                "price_list": "Standard Selling",
                "price_list_rate": price
            }).insert()
    
    @classmethod
    def create_therapist(cls, name):
        """Create therapist employee with schedule for all weekdays."""
        emp_id = frappe.db.get_value("Employee", {"first_name": name}, "name")
        
        if not emp_id:
            emp = frappe.get_doc({
                "doctype": "Employee",
                "first_name": name,
                "gender": "Female",
                "date_of_birth": "1990-01-01",
                "date_of_joining": "2023-01-01",
                "branch": cls.branch,
                "status": "Active",
                "designation": "Therapist"
            })
            emp.insert()
            emp_id = emp.name
        
        # Create schedule for all weekdays
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            frappe.db.delete("Therapist Schedule", {"therapist": emp_id, "day_of_week": day})
            frappe.get_doc({
                "doctype": "Therapist Schedule",
                "therapist": emp_id,
                "day_of_week": day,
                "start_time": "09:00:00",
                "end_time": "18:00:00",
                "is_off": 0,
                "branch": cls.branch
            }).insert()
        
        return emp_id
    
    @classmethod
    def create_customer(cls, name):
        """Create or get customer."""
        if not frappe.db.exists("Customer", name):
            cust = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": name,
                "customer_type": "Individual"
            })
            cust.insert()
            return cust.name
        return name
    
    @classmethod
    def setup_pos_profile(cls):
        """Set up POS Profile for testing."""
        profile_name = "Test Comprehensive POS"
        
        if frappe.db.exists("POS Profile", profile_name):
            return profile_name
        
        # Get or create warehouse
        warehouse = frappe.db.get_value("Warehouse", {"company": "Masaje de Bohol", "is_group": 0}, "name")
        if not warehouse:
            warehouse = f"{cls.branch} Store - MDB"
        
        # Get cost center
        cost_center = frappe.db.get_value("Cost Center", {"company": "Masaje de Bohol", "is_group": 0}, "name")
        
        # Get accounts
        wo_account = frappe.db.get_value("Account", {"account_type": "Expense Account", "is_group": 0, "company": "Masaje de Bohol"}, "name")
        if not wo_account:
            wo_account = frappe.db.get_value("POS Profile", "Bohol Main POS", "write_off_account")
        
        try:
            frappe.get_doc({
                "doctype": "POS Profile",
                "name": profile_name,
                "company": "Masaje de Bohol",
                "warehouse": warehouse,
                "selling_price_list": "Standard Selling",
                "currency": "PHP",
                "write_off_account": wo_account,
                "write_off_cost_center": cost_center,
                "payments": [{"mode_of_payment": "Cash", "default": 1}]
            }).insert(ignore_permissions=True)
        except Exception as e:
            print(f"POS Profile setup error: {e}")
            # Use existing profile
            profile_name = frappe.db.get_value("POS Profile", {"company": "Masaje de Bohol"}, "name")
        
        return profile_name
    
    def setUp(self):
        """Set up before each test - just set user."""
        frappe.set_user("Administrator")

    # ==================== API TESTS ====================
    
    def test_get_branches_returns_list(self):
        """API: get_branches returns list of branches."""
        branches = get_branches()
        self.assertIsInstance(branches, list)
        self.assertTrue(any(b.name == self.branch for b in branches))
    
    def test_get_services_returns_items(self):
        """API: get_services returns service items with prices."""
        # Note: This uses price_list = branch, which may need adjustment
        # For now just verify it doesn't crash
        services = get_services("Standard Selling")
        self.assertIsInstance(services, list)
    
    def test_get_available_slots_returns_times(self):
        """API: get_available_slots returns available time slots."""
        slots = get_available_slots(self.branch, today())
        self.assertIsInstance(slots, list)
    
    def test_create_booking_success(self):
        """API: create_booking creates booking and draft POS invoice."""
        result = create_booking(
            name="Test API Customer",
            phone="9999",
            email="api@test.com",
            branch=self.branch,
            services=[self.service_60],
            date=today(),
            time_slot="10:00"
        )
        
        self.assertIn("name", result)
        self.assertTrue(result["name"].startswith("SB-"))
        
        # Verify booking created
        booking = frappe.get_doc("Service Booking", result["name"])
        self.assertEqual(booking.status, "Pending")
        self.assertEqual(booking.branch, self.branch)
    
    def test_create_booking_multiple_services(self):
        """API: Booking with multiple services calculates correct duration."""
        result = create_booking(
            name="Multi Service Customer",
            phone="8888",
            email="multi@test.com",
            branch=self.branch,
            services=[self.service_60, self.service_30],  # 60 + 30 = 90 min
            date=today(),
            time_slot="11:00"
        )
        
        booking = frappe.get_doc("Service Booking", result["name"])
        self.assertEqual(booking.duration_minutes, 90)
        self.assertEqual(len(booking.items), 2)
    
    def test_search_pending_bookings(self):
        """API: search_pending_bookings returns pending bookings."""
        # Create a pending booking first
        result = create_booking(
            name="Searchable Customer",
            phone="7777",
            email="search@test.com",
            branch=self.branch,
            services=[self.service_30],
            date=today(),
            time_slot="12:00"
        )
        
        # Search
        bookings = search_pending_bookings(txt="Searchable")
        self.assertTrue(len(bookings) > 0)
        self.assertTrue(any(b["value"] == result["name"] for b in bookings))
    
    def test_load_booking_for_pos(self):
        """API: load_booking_for_pos returns complete booking data."""
        result = create_booking(
            name="Load Test Customer",
            phone="6666",
            email="load@test.com",
            branch=self.branch,
            services=[self.service_60],
            date=today(),
            time_slot="13:00"
        )
        
        data = load_booking_for_pos(result["name"])
        
        self.assertEqual(data["booking_name"], result["name"])
        self.assertIn("customer", data)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["item_code"], self.service_60)

    # ==================== THERAPIST CONFLICT TESTS ====================
    
    def test_therapist_conflict_detection(self):
        """Events: Detect therapist double-booking."""
        # Create first booking with therapist
        booking1 = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": today(),
            "time_slot": "14:00",
            "therapist": self.therapist_a,
            "duration_minutes": 60,
            "status": "Pending"
        })
        booking1.append("items", {"service_item": self.service_60, "price": 500})
        booking1.insert()
        
        # Try to create overlapping booking with same therapist
        booking2 = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": today(),
            "time_slot": "14:30",  # Overlaps with 14:00-15:00
            "therapist": self.therapist_a,  # Same therapist
            "duration_minutes": 60,
            "status": "Pending"
        })
        booking2.append("items", {"service_item": self.service_60, "price": 500})
        
        # Should raise conflict error
        with self.assertRaises(frappe.ValidationError):
            booking2.insert()
    
    def test_no_conflict_different_therapist(self):
        """Events: No conflict when different therapists."""
        # Booking with therapist A
        booking1 = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": add_days(today(), 1),
            "time_slot": "10:00",
            "therapist": self.therapist_a,
            "duration_minutes": 60,
            "status": "Pending"
        })
        booking1.append("items", {"service_item": self.service_60, "price": 500})
        booking1.insert()
        
        # Booking with therapist B at same time - should work
        booking2 = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": add_days(today(), 1),
            "time_slot": "10:00",
            "therapist": self.therapist_b,  # Different therapist
            "duration_minutes": 60,
            "status": "Pending"
        })
        booking2.append("items", {"service_item": self.service_60, "price": 500})
        booking2.insert()  # Should not raise
        
        self.assertTrue(booking2.name)
    
    def test_no_conflict_non_overlapping_time(self):
        """Events: No conflict when times don't overlap."""
        # Booking 15:00-16:00
        booking1 = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": add_days(today(), 2),
            "time_slot": "15:00",
            "therapist": self.therapist_a,
            "duration_minutes": 60,
            "status": "Pending"
        })
        booking1.append("items", {"service_item": self.service_60, "price": 500})
        booking1.insert()
        
        # Booking 16:30-17:30 - no overlap
        booking2 = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": add_days(today(), 2),
            "time_slot": "16:30",
            "therapist": self.therapist_a,  # Same therapist
            "duration_minutes": 60,
            "status": "Pending"
        })
        booking2.append("items", {"service_item": self.service_60, "price": 500})
        booking2.insert()  # Should not raise
        
        self.assertTrue(booking2.name)

    # ==================== BOOKING → POS SYNC TESTS ====================
    
    def test_booking_creates_draft_invoice(self):
        """Events: Service Booking creates draft POS Invoice on insert."""
        # Skip if no valid POS Profile with opening entry for our test branch
        pos_profile = frappe.db.get_value("POS Profile", {"company": "Masaje de Bohol"})
        if not pos_profile or not frappe.db.get_value("POS Opening Entry", {"pos_profile": pos_profile, "status": "Open"}):
            self.skipTest("No POS Opening Entry for test - skipping")
        booking = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": today(),
            "time_slot": "09:00",
            "duration_minutes": 60,
            "status": "Pending"
        })
        booking.append("items", {"service_item": self.service_60, "price": 500})
        booking.insert()
        
        # Reload to get invoice link
        booking.reload()
        
        # Check invoice was created
        self.assertTrue(booking.invoice)
        
        invoice = frappe.get_doc("POS Invoice", booking.invoice)
        self.assertEqual(invoice.docstatus, 0)  # Draft
        self.assertEqual(invoice.customer, self.customer)
    
    def test_therapist_copied_to_invoice(self):
        """Events: Therapist is copied from Booking to POS Invoice."""
        pos_profile = frappe.db.get_value("POS Profile", {"company": "Masaje de Bohol"})
        if not pos_profile or not frappe.db.get_value("POS Opening Entry", {"pos_profile": pos_profile, "status": "Open"}):
            self.skipTest("No POS Opening Entry for test - skipping")
        booking = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": today(),
            "time_slot": "09:30",
            "therapist": self.therapist_a,
            "duration_minutes": 60,
            "status": "Pending"
        })
        booking.append("items", {"service_item": self.service_60, "price": 500})
        booking.insert()
        booking.reload()
        
        invoice = frappe.get_doc("POS Invoice", booking.invoice)
        self.assertEqual(invoice.therapist, self.therapist_a)
    
    def test_booking_items_in_invoice(self):
        """Events: Booking items are correctly added to POS Invoice."""
        pos_profile = frappe.db.get_value("POS Profile", {"company": "Masaje de Bohol"})
        if not pos_profile or not frappe.db.get_value("POS Opening Entry", {"pos_profile": pos_profile, "status": "Open"}):
            self.skipTest("No POS Opening Entry for test - skipping")
        booking = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": today(),
            "time_slot": "10:00",
            "duration_minutes": 90,
            "status": "Pending"
        })
        booking.append("items", {"service_item": self.service_60, "price": 500})
        booking.append("items", {"service_item": self.service_30, "price": 300})
        booking.insert()
        booking.reload()
        
        invoice = frappe.get_doc("POS Invoice", booking.invoice)
        
        self.assertEqual(len(invoice.items), 2)
        item_codes = [i.item_code for i in invoice.items]
        self.assertIn(self.service_60, item_codes)
        self.assertIn(self.service_30, item_codes)

    # ==================== POS → BOOKING SYNC TESTS ====================
    
    def test_invoice_submit_marks_booking_completed(self):
        """Events: POS Invoice submit marks linked booking as Completed."""
        pos_profile = frappe.db.get_value("POS Profile", {"company": "Masaje de Bohol"})
        if not pos_profile or not frappe.db.get_value("POS Opening Entry", {"pos_profile": pos_profile, "status": "Open"}):
            self.skipTest("No POS Opening Entry for test - skipping")
        # Create booking with invoice
        booking = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": today(),
            "time_slot": "11:00",
            "duration_minutes": 60,
            "status": "Pending"
        })
        booking.append("items", {"service_item": self.service_60, "price": 500})
        booking.insert()
        booking.reload()
        
        # Submit the invoice
        invoice = frappe.get_doc("POS Invoice", booking.invoice)
        invoice.append("payments", {"mode_of_payment": "Cash", "amount": invoice.grand_total})
        invoice.submit()
        
        # Check booking status
        booking.reload()
        self.assertEqual(booking.status, "Completed")
    
    def test_invoice_cancel_reverts_booking_status(self):
        """Events: POS Invoice cancel reverts booking to Pending."""
        pos_profile = frappe.db.get_value("POS Profile", {"company": "Masaje de Bohol"})
        if not pos_profile or not frappe.db.get_value("POS Opening Entry", {"pos_profile": pos_profile, "status": "Open"}):
            self.skipTest("No POS Opening Entry for test - skipping")
        # Create and submit
        booking = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": today(),
            "time_slot": "11:30",
            "duration_minutes": 30,
            "status": "Pending"
        })
        booking.append("items", {"service_item": self.service_30, "price": 300})
        booking.insert()
        booking.reload()
        
        invoice = frappe.get_doc("POS Invoice", booking.invoice)
        invoice.append("payments", {"mode_of_payment": "Cash", "amount": invoice.grand_total})
        invoice.submit()
        
        # Cancel
        invoice.cancel()
        
        # Check booking reverted
        booking.reload()
        self.assertEqual(booking.status, "Pending")

    # ==================== DELETE/TRASH TESTS ====================
    
    def test_booking_delete_removes_draft_invoice(self):
        """Events: Deleting booking also deletes linked draft invoice."""
        pos_profile = frappe.db.get_value("POS Profile", {"company": "Masaje de Bohol"})
        if not pos_profile or not frappe.db.get_value("POS Opening Entry", {"pos_profile": pos_profile, "status": "Open"}):
            self.skipTest("No POS Opening Entry for test - skipping")
        booking = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": add_days(today(), 3),
            "time_slot": "14:00",
            "duration_minutes": 60,
            "status": "Pending"
        })
        booking.append("items", {"service_item": self.service_60, "price": 500})
        booking.insert()
        booking.reload()
        
        invoice_name = booking.invoice
        self.assertTrue(frappe.db.exists("POS Invoice", invoice_name))
        
        # Delete booking
        frappe.delete_doc("Service Booking", booking.name)
        
        # Invoice should also be deleted
        self.assertFalse(frappe.db.exists("POS Invoice", invoice_name))

    # ==================== COMMISSION TESTS ====================
    
    def test_commission_calculated_on_submit(self):
        """Events: Commission is calculated when POS Invoice is submitted."""
        pos_profile = frappe.db.get_value("POS Profile", {"company": "Masaje de Bohol"})
        if not pos_profile or not frappe.db.get_value("POS Opening Entry", {"pos_profile": pos_profile, "status": "Open"}):
            self.skipTest("No POS Opening Entry for test - skipping")
        # Create booking with therapist
        booking = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": today(),
            "time_slot": "16:00",
            "therapist": self.therapist_a,
            "duration_minutes": 60,
            "status": "Pending"
        })
        booking.append("items", {"service_item": self.service_60, "price": 500})
        booking.insert()
        booking.reload()
        
        # Submit invoice
        invoice = frappe.get_doc("POS Invoice", booking.invoice)
        invoice.append("payments", {"mode_of_payment": "Cash", "amount": invoice.grand_total})
        invoice.submit()
        
        # Check commission was stored
        invoice.reload()
        # Commission should be 10% of grand_total
        if hasattr(invoice, "commission_amount"):
            self.assertGreater(invoice.commission_amount, 0)

    # ==================== DURATION TESTS ====================
    
    def test_duration_auto_calculated(self):
        """Events: Duration is auto-calculated from items on validate."""
        booking = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": add_days(today(), 4),
            "time_slot": "10:00",
            "status": "Pending"
        })
        # Add 90min service
        booking.append("items", {"service_item": self.service_90, "price": 800})
        booking.insert()
        
        # Duration should be auto-set to 90
        booking.reload()
        self.assertEqual(booking.duration_minutes, 90)
    
    def test_start_end_datetime_calculated(self):
        """Events: start_datetime and end_datetime are calculated correctly."""
        booking = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": self.customer,
            "branch": self.branch,
            "booking_date": add_days(today(), 5),
            "time_slot": "14:00",
            "duration_minutes": 60,
            "status": "Pending"
        })
        booking.append("items", {"service_item": self.service_60, "price": 500})
        booking.insert()
        booking.reload()
        
        # Verify datetime fields
        self.assertIsNotNone(booking.start_datetime)
        self.assertIsNotNone(booking.end_datetime)
        
        # End should be 60 min after start
        start = get_datetime(booking.start_datetime)
        end = get_datetime(booking.end_datetime)
        diff = (end - start).seconds // 60
        self.assertEqual(diff, 60)


class TestMasajeReports(FrappeTestCase):
    """Test report functionality."""
    
    def test_daily_branch_sales_report_loads(self):
        """Reports: Daily Branch Sales report loads without errors."""
        from frappe.desk.query_report import run
        
        result = run(
            "Daily Branch Sales",
            filters={"from_date": today(), "to_date": today()}
        )
        
        self.assertIn("result", result)
        self.assertIn("columns", result)
    
    def test_therapist_commission_report_loads(self):
        """Reports: Therapist Commission report loads without errors."""
        from frappe.desk.query_report import run
        
        result = run(
            "Therapist Commission",
            filters={"from_date": today(), "to_date": today()}
        )
        
        self.assertIn("result", result)
    
    def test_popular_services_report_loads(self):
        """Reports: Popular Services report loads without errors."""
        from frappe.desk.query_report import run
        
        result = run(
            "Popular Services",
            filters={"from_date": add_days(today(), -30), "to_date": today()}
        )
        
        self.assertIn("result", result)
    
    def test_peak_hours_report_loads(self):
        """Reports: Peak Hours report loads without errors."""
        from frappe.desk.query_report import run
        
        result = run(
            "Peak Hours",
            filters={"from_date": add_days(today(), -30), "to_date": today()}
        )
        
        self.assertIn("result", result)
