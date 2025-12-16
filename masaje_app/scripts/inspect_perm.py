import frappe

def inspect():
    cols = frappe.db.get_table_columns("Custom DocPerm")
    print("Columns in Custom DocPerm:")
    for c in cols:
        print(c)

if __name__ == "__main__":
    frappe.connect()
    inspect()
