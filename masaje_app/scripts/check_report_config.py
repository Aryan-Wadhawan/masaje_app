
import frappe

def run():
    r = "Daily Branch Sales"
    if frappe.db.exists("Report", r):
        doc = frappe.get_doc("Report", r)
        print(f"Report: {doc.name}")
        print(f"Type: {doc.report_type}")
        print(f"Is Standard: {doc.is_standard}")
        print(f"Module: {doc.module}")
        print(f"Ref DocType: {doc.ref_doctype}")
        if doc.json:
            print(f"JSON content present (Should be None/Empty for pure Script Report usually, or contain config): {len(doc.json)} chars")
        if doc.query:
            print(f"Query content present (Should be None for Script Report): {doc.query}...")
    else:
        print("Report not found in DB")
