import frappe

def debug():
    # 1. Check POS Profile
    profile_name = "Bohol Main POS"
    if not frappe.db.exists("POS Profile", profile_name):
        print(f"ERROR: POS Profile '{profile_name}' not found!")
        return

    profile = frappe.get_doc("POS Profile", profile_name)
    price_list = profile.selling_price_list
    print(f"POS Profile: {profile_name}")
    print(f"Using Price List: {price_list}")
    print(f"Company: {profile.company}")
    print("-" * 20)

    # 2. Check Items
    # Fetch all items that are services or products we care about
    items = frappe.get_all("Item", fields=["name", "item_name", "item_code"], 
                           filters={"disabled": 0, "is_sales_item": 1})
    
    print(f"Found {len(items)} active sales items.")
    
    for item in items:
        # Check Price
        price = frappe.db.get_value("Item Price", 
                                    {"item_code": item.name, "price_list": price_list}, 
                                    "price_list_rate")
        
        print(f"Item: {item.item_name} ({item.name}) -> Price in '{price_list}': {price}")

    print("-" * 20)
    # Check if there are ANY prices for this price list
    all_prices = frappe.get_all("Item Price", filters={"price_list": price_list}, fields=["item_code", "price_list_rate"])
    print(f"Total Item Prices defined for '{price_list}': {len(all_prices)}")

if __name__ == "__main__":
    frappe.connect()
    debug()
