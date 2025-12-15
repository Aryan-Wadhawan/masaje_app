
import frappe

def execute():
    # Helper to create item and price
    create_service("Service-Massage-90", "Full Body Massage (90m)", 1500, 1200)
    create_service("Service-Manicure", "Manicure Premium", 500, 450)
    create_service("Service-Pedicure", "Pedicure Premium", 600, 550)

def create_service(item_code, item_name, price_main, price_downtown):
    if not frappe.db.exists("Item", item_code):
        frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": item_name,
            "item_group": "Services",
            "stock_uom": "Unit",
            "is_stock_item": 0,
            "description": item_name
        }).insert()
        print(f"Created Item: {item_name}")

    # Set Prices
    set_price(item_code, "Bohol Main", price_main)
    set_price(item_code, "Bohol Downtown", price_downtown)
    set_price(item_code, "Standard Selling", price_main)

def set_price(item, price_list, rate):
    if not frappe.db.exists("Item Price", {"item_code": item, "price_list": price_list}):
        frappe.get_doc({
            "doctype": "Item Price",
            "item_code": item,
            "price_list": price_list,
            "price_list_rate": rate
        }).insert()
        print(f"Set Price for {item} in {price_list}")

