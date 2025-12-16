
import frappe

def run():
    print("--- Setting up Inventory Integration ---")
    
    item_uom = "Millilitre" # Matching the "Millilitre" found in UOM list
    
    # 1. Create Stock Items (Consumables)
    items = [
        {"item_code": "Massage Oil", "item_group": "Consumables", "stock_uom": item_uom, "valuation_rate": 0.5},
        {"item_code": "Lavender Essence", "item_group": "Consumables", "stock_uom": item_uom, "valuation_rate": 2.0}
    ]
    
    if not frappe.db.exists("Item Group", "Consumables"):
        frappe.get_doc({"doctype": "Item Group", "item_group_name": "Consumables", "parent_item_group": "All Item Groups", "is_group": 0}).insert()

    for i in items:
        if not frappe.db.exists("Item", i["item_code"]):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": i["item_code"],
                "item_group": i["item_group"],
                "is_stock_item": 1,
                "stock_uom": i["stock_uom"],
                "valuation_rate": i["valuation_rate"],
                "opening_stock": 0
            })
            item.insert()
            print(f"Created Item: {i['item_code']}")
            
    # 2. Create Product Bundle (BOM for Service)
    # 1 Massage Service 60m = 50ml Massage Oil + 5ml Lavender Essence
    parent_item = "Massage Service 60m"
    if frappe.db.exists("Item", parent_item):
        if not frappe.db.exists("Product Bundle", {"new_item_code": parent_item}):
            pb = frappe.get_doc({
                "doctype": "Product Bundle",
                "new_item_code": parent_item,
                "items": [
                    {"item_code": "Massage Oil", "qty": 50, "uom": item_uom},
                    {"item_code": "Lavender Essence", "qty": 5, "uom": item_uom}
                ]
            })
            pb.insert()
            print(f"Created Product Bundle for {parent_item}")
        else:
            print(f"Product Bundle for {parent_item} already exists.")
            
    # 3. Add Opening Stock (to allow deduction)
    # We need stock in the Warehouse used by clean POS profile ("Bohol Downtown Store - MDB")
    warehouse = "Bohol Downtown Store - MDB"
    
    # Check if stock exists
    qty = frappe.db.get_value("Bin", {"item_code": "Massage Oil", "warehouse": warehouse}, "actual_qty") or 0
    if qty < 1000:
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "purpose": "Material Receipt",
            "stock_entry_type": "Material Receipt",
            "items": [
                {"item_code": "Massage Oil", "qty": 5000, "uom": item_uom, "t_warehouse": warehouse, "basic_rate": 0.5},
                {"item_code": "Lavender Essence", "qty": 1000, "uom": item_uom, "t_warehouse": warehouse, "basic_rate": 2.0}
            ]
        })
        se.insert()
        se.submit()
        print(f"Added Stock (5000ml Oil, 1000ml Essence) to {warehouse}")
    else:
        print(f"Stock sufficient in {warehouse} (Qty: {qty})")

    print("Inventory Setup Complete.")
