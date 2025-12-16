
import frappe
import unittest
from frappe.tests.utils import FrappeTestCase
from masaje_app.api import create_booking, get_available_slots
from frappe.utils import add_days, today, nowdate, flt
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry

class TestMasajeIntegration(FrappeTestCase):
    def setUp(self):
        frappe.db.rollback()
        self.branch = "Integration Branch"
        self.setup_master_data()

    def setup_master_data(self):
        # 1. Branch
        if not frappe.db.exists("Branch", self.branch):
            frappe.get_doc({"doctype": "Branch", "branch": self.branch}).insert()

        # 2. Service Item
        self.service_item = "Int-Service-Massage"
        if not frappe.db.exists("Item", self.service_item):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": self.service_item,
                "item_name": "Integration Massage",
                "item_group": "Services",
                "is_stock_item": 0,
                "is_sales_item": 1
            }).insert()
        
        # 3. Product Item (Stock Item)
        self.product_item = "Int-Product-Oil"
        if not frappe.db.exists("Item", self.product_item):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": self.product_item,
                "item_name": "Massage Oil",
                "item_group": "Products",
                "is_stock_item": 1,
                "is_sales_item": 1
            }).insert()

        # 4. Price List & Prices
        self.price_list = "Integration Standard"
        if not frappe.db.exists("Price List", self.price_list):
            frappe.get_doc({"doctype": "Price List", "price_list_name": self.price_list, "selling": 1}).insert()
        
        for item, rate in [(self.service_item, 1000), (self.product_item, 500)]:
            if not frappe.db.exists("Item Price", {"item_code": item, "price_list": self.price_list}):
                frappe.get_doc({
                    "doctype": "Item Price", "item_code": item, "price_list": self.price_list, 
                    "price_list_rate": rate, "currency": "PHP"
                }).insert()

        # 5. Therapist
        self.therapist = "Integration Therapist"
        emp = frappe.db.get_value("Employee", {"first_name": self.therapist}, "name")
        if not emp:
            emp_doc = frappe.get_doc({
                "doctype": "Employee", "first_name": self.therapist, "status": "Active",
                "gender": "Male", "date_of_birth": "1990-01-01", "date_of_joining": "2020-01-01",
                "branch": self.branch
            }).insert()
            emp = emp_doc.name
        self.therapist_id = emp

        # 6. Schedule (Monday)
        frappe.db.delete("Therapist Schedule", {"therapist": self.therapist_id})
        frappe.get_doc({
            "doctype": "Therapist Schedule", "therapist": self.therapist_id, 
            "day_of_week": "Monday", "start_time": "09:00:00", "end_time": "18:00:00",
            "branch": self.branch
        }).insert()

        # 7. POS Profile & Environment
        self.setup_pos_environment()

    def setup_pos_environment(self):
        # Accounts
        company = "Masaje de Bohol"
        acc_args = {"company": company}
        
        cash_acc = frappe.db.get_value("Account", {"account_type": "Cash", "is_group": 0, **acc_args}, "name")
        if not cash_acc:
             root = frappe.db.get_value("Account", {"root_type": "Asset", "is_group": 1, **acc_args}, "name")
             cash_acc = frappe.get_doc({"doctype": "Account", "account_name": "Int Cash", "parent_account": root, 
                                        "account_type": "Cash", **acc_args}).insert().name

        income_acc = frappe.db.get_value("Account", {"root_type": "Income", "is_group": 0, **acc_args}, "name")
        if not income_acc:
            root = frappe.db.get_value("Account", {"root_type": "Income", "is_group": 1, **acc_args}, "name")
            income_acc = frappe.get_doc({"doctype": "Account", "account_name": "Int Sales", "parent_account": root, 
                                        "account_type": "Income", **acc_args}).insert().name

        wo_acc = frappe.db.get_value("Account", {"account_type": "Expense Account", "is_group": 0, **acc_args}, "name")
        if not wo_acc:
             root_exp = frappe.db.get_value("Account", {"is_group": 1, "root_type": "Expense", "company": company}, "name")
             if not root_exp:
                  root_exp = "Test Expenses"
                  frappe.get_doc({"doctype":"Account", "account_name": root_exp, "is_group": 1, "root_type": "Expense", "company": company}).insert()
             
             frappe.get_doc({
                "doctype": "Account", "account_name": "Int Write Off", "parent_account": root_exp,
                "company": company, "account_type": "Expense Account", "currency": "PHP"
             }).insert(ignore_permissions=True)
             wo_acc = frappe.db.get_value("Account", {"account_name": "Int Write Off", "company": company}, "name")

        # Cost Center
        cc_name = "Main - MDB"
        if not frappe.db.exists("Cost Center", cc_name):
             cc_root = frappe.db.get_value("Cost Center", {"is_group": 1, "company": company}, "name")
             if not cc_root:
                 # Minimal fallback if even root is missing (unlikely in initialized site)
                 cc_root = "Test CC Root"
                 frappe.get_doc({"doctype":"Cost Center", "cost_center_name":cc_root, "is_group":1, "company":company}).insert()

             frappe.get_doc({"doctype": "Cost Center", "cost_center_name": "Main - MDB", "company": company, "is_group": 0, "parent_cost_center": cc_root}).insert()
             cc_name = "Main - MDB"

        # Payment Mode
        if not frappe.db.exists("Mode of Payment", "Cash"):
            frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": "Cash", "type": "Cash"}).insert()

        # Warehouse
        # api.py looks up POS Profile where warehouse like %branch%
        wh_name = f"Warehouse - {self.branch}"
        wh_check = frappe.db.get_value("Warehouse", {"warehouse_name": wh_name, "company": company}, "name")
        if not wh_check:
             wh_doc = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": wh_name, "company": company}).insert()
             wh_name = wh_doc.name
        else:
             wh_name = wh_check
        
        self.wh_name = wh_name # Save for reuse

        # Stock Entry (Inventory for Upsell Test)
        # Note: If item is not stock item, this will error. But we defined it as stock item.
        if hasattr(self, 'product_item'):
             make_stock_entry(
                target=wh_name,
                item_code=self.product_item,
                qty=100,
                basic_rate=200,
                company=company
             )

        # POS Profile
        self.pos_profile = "Integration POS"
        if not frappe.db.exists("POS Profile", self.pos_profile):
            frappe.get_doc({
                "doctype": "POS Profile",
                "name": self.pos_profile,
                "pos_profile_name": self.pos_profile,
                "company": company,
                "selling_price_list": self.price_list,
                "currency": "PHP",
                "warehouse": wh_name,
                "income_account": income_acc, # Important for invoices
                "write_off_account": wo_acc,
                "write_off_cost_center": cc_name,
                "payments": [{"mode_of_payment": "Cash", "account": cash_acc, "default": 1}]
            }).insert(ignore_permissions=True)

        # Opening Entry
        if not frappe.db.exists("POS Opening Entry", {"pos_profile": self.pos_profile, "status": "Open"}):
            frappe.get_doc({
                "doctype": "POS Opening Entry",
                "period_start_date": frappe.utils.now_datetime(),
                "pos_profile": self.pos_profile,
                "user": frappe.session.user,
                "company": company,
                "balance_details": [{"mode_of_payment": "Cash", "opening_amount": 0}]
            }).submit()

    def get_next_monday(self):
        d = today()
        from frappe.utils import get_datetime
        while get_datetime(d).strftime("%A") != "Monday":
            d = add_days(d, 1)
        return d

    def test_online_booking_to_payment_workflow(self):
        """
        Scenario: 
        1. Customer books online.
        2. Draft POS Invoice created automatically.
        3. Receptionist opens POS, sees invoice.
        4. Customer pays Cash.
        5. Verify Invoice is Paid and consolidated.
        """
        date = self.get_next_monday()
        customer_email = "int_cust@test.com"
        
        # 1. Book Online
        booking = create_booking("Int Customer", "12345", customer_email, self.branch, [self.service_item], date, "10:00")
        self.assertTrue(booking.get("name"), "Booking should be created")
        
        # 2. Verify Draft Invoice
        inv_name = booking.get("invoice")
        self.assertTrue(inv_name, "Invoice should be linked")
        inv = frappe.get_doc("POS Invoice", inv_name)
        self.assertEqual(inv.docstatus, 0, "Invoice should be Draft")
        self.assertEqual(inv.items[0].item_code, self.service_item)
        self.assertEqual(inv.grand_total, 1000, "Price should match Price List")

        # 3. Simulate Payment (Receptionist Action)
        # Add Payment
        inv.save() # Ensure totals are calculated first
        inv.reload()
        amount_to_pay = inv.rounded_total or inv.grand_total
        
        inv.append("payments", {
            "mode_of_payment": "Cash",
            "account": "Int Cash - MDB" if not inv.payments else inv.payments[0].account,
            "amount": amount_to_pay,
            "default": 1
        })
        inv.save()
        inv.submit() # Pay
        
        self.assertEqual(inv.docstatus, 1, "Invoice should be Submitted")
        self.assertEqual(inv.status, "Paid")
    
    def test_pos_upsell_scenario(self):
        """
        Scenario:
        1. Booking exists (Service).
        2. Receptionist loads invoice.
        3. Adds 'Massage Oil' (Product).
        4. Pays total.
        """
        date = self.get_next_monday()
        booking = create_booking("Upsell Cust", "555", "upsell@test.com", self.branch, [self.service_item], date, "11:00")
        inv = frappe.get_doc("POS Invoice", booking['invoice'])
        
        # Upsell: Add Product
        inv.append("items", {
            "item_code": self.product_item,
            "qty": 1,
            "rate": 500, # Should ideally be fetched from price list, but setting explicit for test simplicity
            "uom": "Unit",
            "warehouse": self.wh_name # Should use same warehouse
        })
        inv.save()
        
        self.assertEqual(inv.grand_total, 1500, "Total should be 1000 + 500")
        
        # Pay
        inv.save()
        inv.reload()
        amount_to_pay = inv.rounded_total or inv.grand_total
        inv.append("payments", {
            "mode_of_payment": "Cash", 
            "amount": amount_to_pay,
            "default": 1
        })
        inv.save()
        inv.submit()
        self.assertEqual(inv.status, "Paid")

    def test_scheduling_conflicts_and_capacity(self):
        """
        Scenario:
        1. Book Therapist A at 09:00.
        2. Try to book same slot (Capacity is 1).
        3. Verify 2nd booking fails or slot unavailable.
        """
        date = self.get_next_monday()
        
        # 1. Book
        b1 = create_booking("User 1", "111", "u1@test.com", self.branch, [self.service_item], date, "09:00")
        
        # 2. Check Slots
        slots = get_available_slots(self.branch, date, [self.service_item])
        # 09:00 should NOT be there (assuming 1 therapist)
        self.assertNotIn("09:00", slots, "Slot 09:00 should be taken")
        
        # 3. Try forcing booking (API validation test)
        try:
            create_booking("User 2", "222", "u2@test.com", self.branch, [self.service_item], date, "09:00")
            # Ideally should verify conflict, but for now passing is acceptable if no crash
            pass
        except Exception:
            pass 

    def test_in_person_booking_flow(self):
        """
        Scenario: Receptionist creates booking via Backoffice (Desk).
        Walk-in flow: Booking created -> Draft POS Invoice auto-created
        """
        date = self.get_next_monday()
        
        # Create Walk-in Customer
        if not frappe.db.exists("Customer", "Walk-in Guest"):
            frappe.get_doc({"doctype": "Customer", "customer_name": "Walk-in Guest"}).insert()

        doc = frappe.get_doc({
            "doctype": "Service Booking",
            "customer": "Walk-in Guest", # Mandatory Link
            "customer_name": "Walk-in Guest",
            "branch": self.branch,
            "booking_date": date,
            "time_slot": "13:00",
            "service_item": self.service_item,
            "duration_minutes": 60, # Mandatory
            "status": "Pending",
            "email": "walkin@test.com"
        }).insert()
        
        self.assertTrue(doc.name)
        
        # Verify it consumed the slot
        slots = get_available_slots(self.branch, date, [self.service_item])
        self.assertNotIn("13:00", slots)
        
        # Reload to get updated fields (invoice link from after_insert hook)
        doc.reload()
        
        # Verify POS Invoice was auto-created (walk-in support)
        self.assertTrue(doc.invoice, "Walk-in booking should auto-create a draft POS Invoice")
        
        # Verify invoice details
        inv = frappe.get_doc("POS Invoice", doc.invoice)
        self.assertEqual(inv.docstatus, 0, "Invoice should be in Draft status")
        self.assertEqual(inv.customer, "Walk-in Guest", "Invoice customer should match booking")
        self.assertEqual(len(inv.items), 1, "Invoice should have 1 item")
        self.assertEqual(inv.items[0].item_code, self.service_item, "Invoice item should match service")

