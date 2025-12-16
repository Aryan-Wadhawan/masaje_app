import frappe
from frappe.tests.utils import FrappeTestCase
from masaje_app.api import get_available_slots, create_booking
from frappe.utils import add_days, nowdate, add_to_date

class TestAdvancedScheduling(FrappeTestCase):
    def setUp(self):
        # Create necessary meta-data
        self.create_test_data()
        
    def create_test_data(self):
        # 1. Branches
        if not frappe.db.exists("Branch", "Test Main"):
            frappe.get_doc({"doctype": "Branch", "branch": "Test Main"}).insert()
        if not frappe.db.exists("Branch", "Test Downtown"):
            frappe.get_doc({"doctype": "Branch", "branch": "Test Downtown"}).insert()
            
        # 2. Therapist (Roaming)
        if not frappe.db.exists("Employee", "Therapist Roamer"):
            frappe.get_doc({
                "doctype": "Employee",
                "first_name": "Therapist",
                "last_name": "Roamer",
                "branch": "Test Main", # Home branch
                "status": "Active",
                "gender": "Female",
                "date_of_birth": "1990-01-01",
                "date_of_joining": nowdate()
            }).insert()
            
        # 3. Schedules (Dynamic)
        # Mon @ Main
        self.create_schedule("Therapist Roamer", "Monday", "Test Main")
        # Tue @ Downtown
        self.create_schedule("Therapist Roamer", "Tuesday", "Test Downtown")
        
        # 4. Warehouse & POS Profile for Pricing Check
        self.create_pos_env("Test Main")
        self.create_pos_env("Test Downtown")
        
        # 5. Item Prices
        self.create_prices()

    def create_schedule(self, therapist, day, branch):
        s_name = f"{therapist}-{day}"
        frappe.db.delete("Therapist Schedule", {"name": s_name})
        
        frappe.get_doc({
            "doctype": "Therapist Schedule",
            "therapist": frappe.db.get_value("Employee", {"first_name": therapist.split()[0]}, "name"),
            "day_of_week": day,
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "branch": branch,
            "is_off": 0
        }).insert(ignore_permissions=True)

    def create_pos_env(self, branch):
        # 1. Warehouse
        wh_name = f"{branch} Store"
        final_wh = wh_name
        if frappe.db.exists("Warehouse", f"{wh_name} - MDB"):
            final_wh = f"{wh_name} - MDB"
        elif not frappe.db.exists("Warehouse", wh_name):
             d = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": wh_name, "company": "Masaje de Bohol"})
             d.insert(ignore_permissions=True)
             final_wh = d.name
        
        # 2. POS Profile
        prof = f"{branch} POS"
        if not frappe.db.exists("POS Profile", prof):
            # Create dependencies
            # Payment Mode
            if not frappe.db.exists("Mode of Payment", "Cash"):
                frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": "Cash", "type": "Cash"}).insert()
            
            # Account
            cash_acc = frappe.db.get_value("Account", {"account_type": "Cash", "is_group": 0, "company": "Masaje de Bohol"}, "name")
            if not cash_acc:
                # Create Cash Account
                root_asset = frappe.db.get_value("Account", {"is_group": 1, "root_type": "Asset", "company": "Masaje de Bohol"}, "name")
                if not root_asset:
                     # Create Root for test if totally empty
                     root_asset = "Test Assets"
                     frappe.get_doc({"doctype":"Account", "account_name": root_asset, "is_group": 1, "root_type": "Asset", "company": "Masaje de Bohol"}).insert()
                
                cash_acc = "Cash - MDB"
                frappe.get_doc({
                    "doctype": "Account", "account_name": "Cash", "parent_account": root_asset, 
                    "company": "Masaje de Bohol", "account_type": "Cash", "currency": "PHP"
                }).insert(ignore_permissions=True)
                cash_acc = frappe.db.get_value("Account", {"account_name": "Cash", "company": "Masaje de Bohol"}, "name")

            # Write Off Account
            wo_acc = frappe.db.get_value("Account", {"account_type": "Expense Account", "is_group": 0, "company": "Masaje de Bohol"}, "name")
            if not wo_acc:
                 root_exp = frappe.db.get_value("Account", {"is_group": 1, "root_type": "Expense", "company": "Masaje de Bohol"}, "name")
                 if not root_exp:
                      root_exp = "Test Expenses"
                      frappe.get_doc({"doctype":"Account", "account_name": root_exp, "is_group": 1, "root_type": "Expense", "company": "Masaje de Bohol"}).insert()
                 
                 frappe.get_doc({
                    "doctype": "Account", "account_name": "Test Write Off", "parent_account": root_exp,
                    "company": "Masaje de Bohol", "account_type": "Expense Account", "currency": "PHP"
                 }).insert(ignore_permissions=True)
                 wo_acc = frappe.db.get_value("Account", {"account_name": "Test Write Off", "company": "Masaje de Bohol"}, "name")

            # Cost Center
            cc_name = "Main - MDB"
            if not frappe.db.exists("Cost Center", cc_name):
                 cc_name = frappe.db.get_value("Cost Center", {"is_group": 0, "company": "Masaje de Bohol"}, "name")
                 if not cc_name:
                      frappe.get_doc({"doctype": "Cost Center", "cost_center_name": "Main - MDB", "company": "Masaje de Bohol", "is_group": 0}).insert()
                      cc_name = "Main - MDB"

            # Price List
            pl = f"{branch} List"
            if not frappe.db.exists("Price List", pl):
                frappe.get_doc({"doctype": "Price List", "price_list_name": pl, "selling": 1}).insert()

            pos_profile = frappe.get_doc({
                "doctype": "POS Profile",
                "name": prof,
                "pos_profile_name": prof,
                "company": "Masaje de Bohol",
                "warehouse": final_wh,
                "selling_price_list": pl,
                "currency": "PHP",
                "write_off_account": wo_acc,
                "write_off_cost_center": cc_name,
                "payments": [{
                    "mode_of_payment": "Cash",
                    "account": cash_acc,
                    "default": 1
                }]
            })
            pos_profile.insert(ignore_permissions=True)
            
        # 3. Create POS Opening Entry (MANDATORY for Invoice)
        # Check if open
        user = frappe.session.user
        if not frappe.db.exists("POS Opening Entry", {"pos_profile": prof, "status": "Open", "user": user}):
             op = frappe.get_doc({
                 "doctype": "POS Opening Entry",
                 "period_start_date": nowdate(),
                 "pos_profile": prof,
                 "user": user,
                 "company": "Masaje de Bohol",
                 "balance_details": [{"mode_of_payment": "Cash", "opening_amount": 0}]
             })
             op.insert(ignore_permissions=True)
             op.submit()

    def create_prices(self):
        # Ensure Item exists
        if not frappe.db.exists("Item", "Service-Test"):
            frappe.get_doc({"doctype": "Item", "item_code": "Service-Test", "item_group": "Services", "is_stock_item": 0}).insert()
            
        # Set Prices
        if not frappe.db.exists("Item Price", {"item_code": "Service-Test", "price_list": "Test Main List"}):
            frappe.get_doc({
                 "doctype": "Item Price", 
                 "item_code": "Service-Test", 
                 "price_list": "Test Main List", 
                 "price_list_rate": 1000
            }).insert(ignore_permissions=True)
         
        if not frappe.db.exists("Item Price", {"item_code": "Service-Test", "price_list": "Test Downtown List"}):
            frappe.get_doc({
                 "doctype": "Item Price", 
                 "item_code": "Service-Test", 
                 "price_list": "Test Downtown List", 
                 "price_list_rate": 800
            }).insert(ignore_permissions=True)


    def test_roaming_availability(self):
        # 1. Find a future Monday
        from frappe.utils import get_date_str
        import datetime
        
        today = datetime.date.today()
        monday = today + datetime.timedelta(days=(7 - today.weekday()))
        tuesday = monday + datetime.timedelta(days=1)
        
        mon_date = monday.strftime("%Y-%m-%d")
        tue_date = tuesday.strftime("%Y-%m-%d")
        
        # Case A: Check availability at Main on Monday (Should have slots)
        slots_main_mon = get_available_slots(branch="Test Main", date=mon_date, service_item="Service-Test")
        self.assertTrue(len(slots_main_mon) > 0, "Should have slots at Main on Monday")
        
        # Case B: Check availability at Downtown on Monday (Should be empty)
        slots_dt_mon = get_available_slots(branch="Test Downtown", date=mon_date, service_item="Service-Test")
        self.assertEqual(len(slots_dt_mon), 0, "Should NOT have slots at Downtown on Monday")
        
        # Case C: Check availability at Downtown on Tuesday (Should have slots)
        slots_dt_tue = get_available_slots(branch="Test Downtown", date=tue_date, service_item="Service-Test")
        self.assertTrue(len(slots_dt_tue) > 0, "Should have slots at Downtown on Tuesday")
        
    def test_cross_branch_pricing(self):
        # 2. Book Roamer at Downtown (Tue)
        from frappe.utils import get_date_str
        import datetime
        
        today = datetime.date.today()
        # Find next Tuesday
        days_ahead = 1 - today.weekday() # If today is Mon(0), Tue is +1. If Tue(1), next Tue is +7? 
        if days_ahead <= 0: days_ahead += 7
        tuesday = today + datetime.timedelta(days=days_ahead)
        tue_date = tuesday.strftime("%Y-%m-%d")
        
        # Create Booking
        # Note: Customer creation is handled inside create_booking if not exists
        res = create_booking(
            customer_name="Test Customer",
            phone="9999999999",
            email="test@example.com",
            branch="Test Downtown",
            items="Service-Test",
            date=tue_date,
            time="09:00"
        )
        
        self.assertTrue(res.get("invoice"), "Invoice should be created")
        
        # Verify Invoice Price
        inv = frappe.get_doc("POS Invoice", res["invoice"])
        self.assertEqual(inv.items[0].rate, 800, "Should use Downtown Price (800)")
        self.assertEqual(inv.pos_profile, "Test Downtown POS")
        
        # 3. Book Roamer at Main (Next Mon)
        days_ahead_mon = 0 - today.weekday() 
        if days_ahead_mon <= 0: days_ahead_mon += 7
        monday = today + datetime.timedelta(days=days_ahead_mon)
        mon_date = monday.strftime("%Y-%m-%d")
        
        res_main = create_booking(
            customer_name="Test Customer",
            phone="9999999999",
            email="test@example.com",
            branch="Test Main",
            items="Service-Test",
            date=mon_date,
            time="09:00"
        )
        inv_main = frappe.get_doc("POS Invoice", res_main["invoice"])
        self.assertEqual(inv_main.items[0].rate, 1000, "Should use Main Price (1000)")
        
        print("\n[SUCCESS] Cross-Branch Pricing Verified.")
