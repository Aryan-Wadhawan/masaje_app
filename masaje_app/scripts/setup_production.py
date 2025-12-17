"""
Setup Production Services for Masaje de Bohol
Creates price lists, item groups, and all services with prices.

Run: bench --site erpnext.localhost execute masaje_app.scripts.setup_production.setup_services
"""
import frappe

# ============================================================
# CONFIGURATION
# ============================================================

# Branches that have Sauna
SAUNA_BRANCHES = ["Dao Branch", "Panglao Branch"]
ALL_BRANCHES = ["CPG East Branch", "Dao Branch", "Calceta Branch", "Port Branch", "Panglao Branch"]

# Item Groups
ITEM_GROUPS = [
    {"name": "Massage 1 Hour", "parent": "Services"},
    {"name": "Massage 30 Mins", "parent": "Services"},
    {"name": "Other Services", "parent": "Services"},
    {"name": "Special Packages", "parent": "Services"},
]

# Services with prices and durations
# Format: (name, english_name, price, duration_mins, group, sauna_only)
SERVICES = [
    # MASSAGE | 1 HOUR
    ("Bol-anong Amuma", "Signature Massage", 449, 60, "Massage 1 Hour", False),
    ("Himas Masaje", "Swedish Massage", 449, 60, "Massage 1 Hour", False),
    ("Hitad Masaje", "Thai Massage", 500, 60, "Massage 1 Hour", False),
    ("Alimyon", "Aromatherapy", 549, 60, "Massage 1 Hour", False),
    ("Painit sa Likod", "Ventosa", 549, 60, "Massage 1 Hour", False),
    ("Du-ot", "Shiatsu", 500, 60, "Massage 1 Hour", False),
    
    # MASSAGE | 30 MINS
    ("Tusok-tusok", "Foot Reflex 30min", 280, 30, "Massage 30 Mins", False),
    ("Masaje sa Tiil", "Foot Massage", 280, 30, "Massage 30 Mins", False),
    ("Masaje sa Likod", "Back Massage", 280, 30, "Massage 30 Mins", False),
    ("Foot Reflex 1 Hour", "Foot Reflex 1 Hour", 449, 60, "Massage 30 Mins", False),
    
    # OTHER SERVICES
    ("Foot Spa with Scrub", "Foot Spa with Scrub", 449, 0, "Other Services", False),
    ("Body Scrub", "Body Scrub", 899, 0, "Other Services", False),
    ("Waxing Armpit", "Waxing (Armpit)", 379, 0, "Other Services", False),
    ("Waxing Legs", "Waxing (Legs)", 499, 0, "Other Services", False),
    ("Sauna", "Sauna", 649, 0, "Other Services", True),  # Sauna only at Dao/Panglao
    ("Home Service", "Home Service Addon", 700, 0, "Other Services", False),
    ("Hotel Service", "Hotel Service Addon", 850, 0, "Other Services", False),
    
    # SPECIAL PACKAGES (duration = sum of components where possible)
    # Sauna(0) + 1hr massage(60) = 60min
    ("Sauna + Signature", "Sauna + Signature/Swedish/Thai", 999, 60, "Special Packages", True),
    ("Sauna + Ventosa", "Sauna + Ventosa", 1099, 60, "Special Packages", True),
    ("Sauna + Aroma Massage", "Sauna + Aroma Massage", 1099, 60, "Special Packages", True),
    # Sauna(0) + Body Scrub(0) + Massage(60) = 60min
    ("Sauna + Body Scrub + Aroma", "Sauna + Body Scrub + Aroma/Ventosa", 1899, 60, "Special Packages", True),
    ("Sauna + Body Scrub + Signature", "Sauna + Body Scrub + Signature/Shiatsu", 1849, 60, "Special Packages", True),
    ("Sauna + Body Scrub + Swedish", "Sauna + Body Scrub + Swedish/Thai", 1849, 60, "Special Packages", True),
    # No Sauna packages
    ("Body Scrub + Aroma", "Body Scrub + Aroma/Ventosa", 1300, 60, "Special Packages", False),
    ("Body Scrub + Signature", "Body Scrub + Signature/Shiatsu/Swedish/Thai", 1250, 60, "Special Packages", False),
    ("Foot Reflex + Back Massage", "Foot Reflex + Back Massage", 449, 60, "Special Packages", False),
]


def setup_price_lists():
    """Create price lists for Standard and Panglao."""
    print("\n1. Setting up Price Lists...")
    
    price_lists = [
        {"name": "Standard Selling", "selling": 1, "buying": 0},  # Already exists, just ensure it's there
        {"name": "Panglao Prices", "selling": 1, "buying": 0},
    ]
    
    for pl in price_lists:
        if not frappe.db.exists("Price List", pl["name"]):
            frappe.get_doc({
                "doctype": "Price List",
                "price_list_name": pl["name"],
                "selling": pl["selling"],
                "buying": pl["buying"],
                "currency": "PHP"
            }).insert()
            print(f"   ✓ Created: {pl['name']}")
        else:
            print(f"   ✓ Exists: {pl['name']}")
    
    frappe.db.commit()


def setup_item_groups():
    """Create item groups for service categories."""
    print("\n2. Setting up Item Groups...")
    
    # Get or create root parent (All Item Groups)
    root_parent = None
    if frappe.db.exists("Item Group", "All Item Groups"):
        root_parent = "All Item Groups"
    else:
        # Check if there's a root item group
        root_groups = frappe.db.get_all("Item Group", 
            filters={"is_group": 1, "parent_item_group": ["in", ["", None]]},
            limit=1)
        if root_groups:
            root_parent = root_groups[0].name
        else:
            # Create All Item Groups as root
            try:
                frappe.get_doc({
                    "doctype": "Item Group",
                    "item_group_name": "All Item Groups",
                    "is_group": 1
                }).insert()
                root_parent = "All Item Groups"
                print("   ✓ Created: All Item Groups (root)")
            except Exception as e:
                print(f"   ⚠ Could not create root: {e}, using empty parent")
                root_parent = ""
    
    # Ensure parent group exists
    if not frappe.db.exists("Item Group", "Services"):
        frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": "Services",
            "parent_item_group": root_parent or "",
            "is_group": 1
        }).insert()
        print("   ✓ Created: Services (parent)")
    
    for group in ITEM_GROUPS:
        if not frappe.db.exists("Item Group", group["name"]):
            frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": group["name"],
                "parent_item_group": group["parent"],
                "is_group": 0
            }).insert()
            print(f"   ✓ Created: {group['name']}")
        else:
            print(f"   ✓ Exists: {group['name']}")
    
    frappe.db.commit()


def setup_branch_availability_field():
    """Skip custom field - use description to note branch availability instead."""
    print("\n3. Skipping custom branch field (using description instead)...")
    print("   ✓ Sauna services will have branch restriction in description")


def setup_services():
    """Create all service items with prices."""
    print("\n4. Setting up Services...")
    
    # Ensure UOM exists
    uom = "Nos"
    if not frappe.db.exists("UOM", uom):
        # Try "Unit" instead
        if frappe.db.exists("UOM", "Unit"):
            uom = "Unit"
        else:
            # Create Nos UOM
            try:
                frappe.get_doc({
                    "doctype": "UOM",
                    "uom_name": "Nos"
                }).insert()
                print(f"   ✓ Created UOM: Nos")
            except Exception as e:
                print(f"   ⚠ Could not create UOM: {e}, trying Unit")
                uom = "Unit"
    
    for service in SERVICES:
        name, english, price, duration, group, sauna_only = service
        item_code = name.replace(" ", "-").replace("/", "-").replace("+", "-")
        
        if frappe.db.exists("Item", item_code):
            print(f"   ✓ Exists: {name}")
            continue
        
        # Create Item
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": name,
            "description": english,
            "item_group": group,
            "is_stock_item": 0,
            "stock_uom": uom,  # Unit of Measure for services
            "custom_duration_minutes": duration
        })
        item.insert()
        
        # Add price to Standard Selling
        frappe.get_doc({
            "doctype": "Item Price",
            "item_code": item_code,
            "price_list": "Standard Selling",
            "price_list_rate": price
        }).insert()
        
        # Add same price to Panglao (user will update later)
        frappe.get_doc({
            "doctype": "Item Price",
            "item_code": item_code,
            "price_list": "Panglao Prices",
            "price_list_rate": price  # Same for now, update later
        }).insert()
        
        # Set branch availability for Sauna services
        if sauna_only:
            # Need to update with Table MultiSelect - for now just note in description
            frappe.db.set_value("Item", item_code, "description", 
                f"{english} (Available at: Dao Branch, Panglao Branch only)")
        
        print(f"   ✓ Created: {name} (₱{price}, {duration}min)")
    
    frappe.db.commit()
    print(f"\n   Total: {len(SERVICES)} services created")


def setup_services_full():
    """Run complete service setup."""
    print("=" * 60)
    print("SETTING UP PRODUCTION SERVICES")
    print("=" * 60)
    
    setup_price_lists()
    setup_item_groups()
    setup_branch_availability_field()
    setup_services()
    
    print("\n" + "=" * 60)
    print("✓ SERVICES SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update Panglao prices in: Stock > Price List > Panglao Prices")
    print("2. Set branch availability for Sauna services if needed")


if __name__ == "__main__":
    setup_services_full()
