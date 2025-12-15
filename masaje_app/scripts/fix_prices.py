
import frappe

def execute():
    price_list = "Bohol Main"
    
    # Define prices for missing items
    # (Item Code, Rate)
    missing_prices = [
        ("Service-Pedicure", 450),
        ("Service-Manicure", 350),
        ("Service-Massage-90", 1400),
        ("Service-Massage-60", 1000), # Re-assert just in case
        ("Product-TigerBalm", 150)    # Re-assert
    ]

    for item_code, rate in missing_prices:
        if frappe.db.exists("Item", item_code):
            # Check if price exists for this PL
            if not frappe.db.exists("Item Price", {"item_code": item_code, "price_list": price_list}):
                frappe.get_doc({
                    "doctype": "Item Price",
                    "item_code": item_code,
                    "price_list": price_list,
                    "price_list_rate": rate,
                    "currency": "PHP"
                }).insert()
                print(f"Created Price: {item_code} = {rate}")
            else:
                # Update existing if 0?
                name = frappe.db.get_value("Item Price", {"item_code": item_code, "price_list": price_list}, "name")
                frappe.db.set_value("Item Price", name, "price_list_rate", rate)
                print(f"Updated Price: {item_code} = {rate}")
        else:
            print(f"Item {item_code} does not exist, skipping.")

    frappe.db.commit()
