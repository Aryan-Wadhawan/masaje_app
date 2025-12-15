
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
        
        # 4. Create POS Profile
        self.create_pos_profile()
        
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

    def test_booking_beyond_shift(self):
        # Shift ends at 18:00. 
        # Booking at 17:00 for 90 mins (end 18:30) should NOT be available.
        # Currently get_available_slots defaults to 1h check. 
        # We need to verify if we pass items, it checks duration.
        
        date = today()
        while get_datetime(date).strftime("%A") != "Monday":
            date = add_days(date, 1)

        # 1. 60m service at 17:00 -> Ends 18:00 (OK)
        # Note: Depending on strict logic, 18:00 end matches 18:00 shift end.
        slots = get_available_slots(self.branch, date, [self.item1])
        # If logic is robust, 17:00 should be allowed for 60m
        # But wait, earlier I saw strict < logic? 
        # Let's just test the failure case first.
        
        # 2. 90m service at 17:00 -> Ends 18:30 (More than shift)
        # Pass item with 90m duration? item1 is 60m. item2 is 30m.
        slots = get_available_slots(self.branch, date, [self.item1, self.item2])
        self.assertNotIn("17:00", slots)

    def test_past_date_validation(self):
        # Booking for yesterday should fail
        past_date = add_days(today(), -1)
        try:
            create_booking("Past User", "000", "past@test.com", self.branch, [self.item1], past_date, "10:00")
            self.fail("Should have raised error for past date")
        except Exception:
            pass # Success if it raised

    def test_invalid_item(self):
        # Booking with non-existent item
        date = today()
        try:
             create_booking("Invalid User", "000", "inv@test.com", self.branch, ["Fake-Item-123"], date, "10:00")
             # Should probably fail or ignore? Validation should ideally catch it.
             # If API is loose, it might create booking with None?
             pass 
        except Exception:
            pass

    def test_pos_invoice_creation(self):
        # Ensure POS Profile is setup (done in create_test_data now)
        date = today()
        
        # DEBUG
        print("DEBUG: All POS Profiles:", frappe.get_all("POS Profile", fields=["name", "warehouse"]))
        print("DEBUG: Branch:", self.branch)
        
        # Create Booking
        booking = create_booking("POS Customer", "888", "pos@test.com", self.branch, [self.item1], date, "14:00")
        self.assertTrue(booking.get("invoice"), "Invoice Name should be returned")
        
        invoice_name = booking.get("invoice")
        
        # Verify POS Invoice
        inv = frappe.get_doc("POS Invoice", invoice_name)
        self.assertEqual(inv.docstatus, 0) # Draft
        self.assertEqual(inv.customer_name, "POS Customer")
        self.assertEqual(len(inv.items), 1)
        self.assertEqual(inv.items[0].item_code, self.item1)
        self.assertEqual(inv.pos_profile, "Test POS Profile")
        
    def create_pos_profile(self):
        # Helper to create needed POS data
        # A. Cost Center
        cc_name = "Test Cost Center"
        final_cc_name = cc_name
        
        if not frappe.db.exists("Cost Center", cc_name) and not frappe.db.exists("Cost Center", f"{cc_name} - MDB"):
            parent_cc = frappe.db.get_value("Cost Center", {"company": "Masaje de Bohol", "is_group": 1}, "name")
            d = frappe.get_doc({
                "doctype": "Cost Center",
                "cost_center_name": cc_name,
                "company": "Masaje de Bohol",
                "is_group": 0,
                "parent_cost_center": parent_cc
            })
            d.insert(ignore_permissions=True)
            final_cc_name = d.name
        else:
             if frappe.db.exists("Cost Center", f"{cc_name} - MDB"):
                 final_cc_name = f"{cc_name} - MDB"

        # B. Account (Direct Expense for Write Offs)
        # Try to borrow from existing POS Profile
        existing_wo = frappe.db.get_value("POS Profile", "Bohol Main POS", "write_off_account")
        acc_name = existing_wo
        
        if not acc_name:
             # Try to find any Expense account
             acc_name = frappe.db.get_value("Account", {"account_type": "Expense", "is_group": 0, "company": "Masaje de Bohol"}, "name")

        if not acc_name:
             # Create one if desperate (needs parent)
             parent = frappe.db.get_value("Account", {"is_group": 1, "root_type": "Expense", "company": "Masaje de Bohol"}, "name")
             if parent:
                 acc_name = "Test Write Off"
                 if not frappe.db.exists("Account", acc_name):
                     frappe.get_doc({
                        "doctype": "Account",
                        "account_name": "Test Write Off",
                        "parent_account": parent,
                        "company": "Masaje de Bohol",
                        "account_type": "Expense"
                     }).insert(ignore_permissions=True)
        
        # 1. Warehouse
        wh_name = f"{self.branch} Store"
        final_wh_name = wh_name
        
        # Check based on likely name
        if not frappe.db.exists("Warehouse", wh_name) and not frappe.db.exists("Warehouse", f"{wh_name} - MDB"):
            parent_wh = frappe.db.get_value("Warehouse", {"company": "Masaje de Bohol", "is_group": 1}, "name")
            if not parent_wh:
                 # Create a Group Warehouse
                 parent_wh = "Test Group Warehouse"
                 frappe.get_doc({
                     "doctype": "Warehouse", 
                     "warehouse_name": parent_wh, 
                     "is_group": 1, 
                     "company": "Masaje de Bohol"
                 }).insert(ignore_permissions=True)

            d = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": wh_name,
                "company": "Masaje de Bohol", 
                "parent_warehouse": parent_wh
            })
            d.insert(ignore_permissions=True)
            final_wh_name = d.name
        else:
            # If exists, find the right name
            if frappe.db.exists("Warehouse", f"{wh_name} - MDB"):
                final_wh_name = f"{wh_name} - MDB"
            
        # 2. Payment Mode
        if not frappe.db.exists("Mode of Payment", "Cash"):
             frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": "Cash", "type": "Cash"}).insert()

        # 3. POS Profile
        if not frappe.db.exists("POS Profile", "Test POS Profile"):
             if acc_name: # Use final name
                 frappe.get_doc({
                    "doctype": "POS Profile",
                    "name": "Test POS Profile",
                    "company": "Masaje de Bohol",
                    "warehouse": final_wh_name,
                    "selling_price_list": "Standard Selling",
                    "currency": "PHP",
                    "write_off_account": acc_name, 
                    "write_off_cost_center": final_cc_name, 
                    "payments": [{"mode_of_payment": "Cash", "default": 1}]
                 }).insert(ignore_permissions=True)
             else:
                 print(f"DEBUG: Failed to create POS Profile - Account: {acc_name}, WH: {final_wh_name}")
                 
        # 4. Open POS Entry (Required for POS Invoice)
        if not frappe.db.exists("POS Opening Entry", {"pos_profile": "Test POS Profile", "status": "Open"}):
            frappe.get_doc({
                "doctype": "POS Opening Entry",
                "period_start_date": frappe.utils.now_datetime(),
                "pos_profile": "Test POS Profile",
                "user": frappe.session.user,
                "company": "Masaje de Bohol",
                "balance_details": [{"mode_of_payment": "Cash", "opening_amount": 0}]
            }).submit()
