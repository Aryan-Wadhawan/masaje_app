
import frappe
from frappe.tests.utils import FrappeTestCase
from masaje_app.api import get_available_slots, create_booking
from frappe.utils import add_days, today, get_datetime, add_to_date

class TestMasajeAPI(FrappeTestCase):
    def setUp(self):
        frappe.db.rollback()
        self.branch = "Test Branch"
        self.create_test_data()

    def create_test_data(self):
        # 1. Create Branch
        if not frappe.db.exists("Branch", self.branch):
            frappe.get_doc({"doctype": "Branch", "branch": self.branch}).insert()

        # 2. Create Items
        self.item1 = "Test-Service-60"
        self.item2 = "Test-Service-30"
        self.create_item(self.item1, "Test Massage 60", 60)
        self.create_item(self.item2, "Test Massage 30", 30)

        # 3. Create Therapists & Schedules
        # Therapist A: Mon 9-18
        # Therapist B: Mon 9-18
        self.create_therapist("Therapist A", self.branch, "Monday")
        self.create_therapist("Therapist B", self.branch, "Monday")
        
    def create_item(self, code, name, duration):
        if not frappe.db.exists("Item", code):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": code,
                "item_name": name,
                "item_group": "Services",
                "is_stock_item": 0
            }).insert()
        # Mock price
        if not frappe.db.exists("Item Price", {"item_code": code}):
             frappe.get_doc({
                "doctype": "Item Price", 
                "item_code": code, 
                "price_list": "Standard Selling", 
                "price_list_rate": 100
             }).insert()

    def create_therapist(self, name, branch, day):
        # Create Employee
        emp_id = frappe.db.get_value("Employee", {"first_name": name}, "name")
        if not emp_id:
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
            emp_id = emp.name
        else:
            frappe.db.set_value("Employee", emp_id, "branch", branch)
            frappe.db.set_value("Employee", emp_id, "status", "Active")

        # Create Schedule
        frappe.db.delete("Therapist Schedule", {"therapist": emp_id, "day_of_week": day})
        
        frappe.get_doc({
            "doctype": "Therapist Schedule",
            "therapist": emp_id,
            "day_of_week": day,
            "start_time": "09:00:00",
            "end_time": "18:00:00",
            "is_off": 0
        }).insert()
        
        print(f"DEBUG: Created Therapist {name} ({emp_id}) at {branch} on {day}")

    def test_smart_scheduling_capacity(self):
        # Determine next Monday
        date = today()
        while get_datetime(date).strftime("%A") != "Monday":
            date = add_days(date, 1)

        # 1. Check Availability (Should have 2 slots capacity)
        slots = get_available_slots(self.branch, date)
        self.assertIn("10:00", slots)

        # 2. Book 1st slot
        booking1 = create_booking("Customer 1", "0001", "c1@test.com", self.branch, [self.item1], date, "10:00")
        self.assertTrue(booking1.get("name"))

        # 3. Check Availability (Should STILL be available - 1/2 capacity used)
        slots = get_available_slots(self.branch, date)
        self.assertIn("10:00", slots)

        # 4. Book 2nd slot
        booking2 = create_booking("Customer 2", "0002", "c2@test.com", self.branch, [self.item1], date, "10:00")
        self.assertTrue(booking2.get("name"))

        # 5. Check Availability (Should NOT be available - 2/2 capacity used)
        slots = get_available_slots(self.branch, date)
        self.assertNotIn("10:00", slots)

    def test_multi_service_duration(self):
        date = today()
        # Item 1 (60m) + Item 2 (30m) = 90m
        booking = create_booking("Cart Customer", "999", "cart@test.com", self.branch, [self.item1, self.item2], date, "09:00")
        doc = frappe.get_doc("Service Booking", booking["name"])
        
        self.assertEqual(doc.duration_minutes, 90)
        self.assertEqual(len(doc.items), 2)
        # Verify End Date calculation
        expected_end = add_to_date(doc.start_datetime, minutes=90)
        self.assertEqual(get_datetime(doc.end_datetime), get_datetime(expected_end))
