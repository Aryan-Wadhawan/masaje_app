import frappe

def debug():
    profiles = frappe.get_all("POS Profile", fields=["name", "company", "selling_price_list", "warehouse"])
    
    print("-" * 30)
    print("POS PROFILES CONFIG")
    print("-" * 30)
    
    for p in profiles:
        print(f"Profile: {p.name}")
        print(f"  > Warehouse: {p.warehouse}")
        print(f"  > Price List: {p.selling_price_list}")
        
        # Check specific item prices for this list
        items = ["Service-Massage-60", "Service-Manicure", "Service-Pedicure", "Product-TigerBalm"]
        print(f"  > checking prices in '{p.selling_price_list}':")
        for item in items:
            price = frappe.db.get_value("Item Price", 
                                        {"item_code": item, "price_list": p.selling_price_list}, 
                                        "price_list_rate")
            print(f"    - {item}: {price}")
        print("-" * 20)

if __name__ == "__main__":
    frappe.connect()
    debug()
