
import frappe

def run():
    item_code = "Massage Service 60m"
    if frappe.db.exists("Item", item_code):
        item = frappe.get_doc("Item", item_code)
        print(f"Item: {item.item_code}")
        print(f"  Is Stock Item: {item.is_stock_item}")
        print(f"  Is Sales Item: {item.is_sales_item}")
        print(f"  Has Variants: {item.has_variants}")
        
        # Check for Product Bundle
        bundles = frappe.get_all("Product Bundle", filters={"new_item_code": item_code}, pluck="name")
        print(f"  Product Bundles (BOM): {bundles}")
    else:
        print(f"Item {item_code} not found.")
