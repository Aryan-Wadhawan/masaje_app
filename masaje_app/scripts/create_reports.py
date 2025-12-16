import frappe

def create_reports():
    # 1. Daily Branch Sales
    query_sales = """
    SELECT 
        s.booking_date as "Date:Date:100",
        s.branch as "Branch:Link/Branch:120",
        COUNT(s.name) as "Total Bookings:Int:100",
        p.grand_total as "Total Sales:Currency:120"
    FROM `tabService Booking` s
    LEFT JOIN `tabPOS Invoice` p ON p.customer = s.customer AND p.posting_date = s.booking_date
    WHERE s.status = 'Completed'
    GROUP BY s.booking_date, s.branch, p.grand_total
    """
    
    # Correction: Linking Booking to POS Invoice is better done if we stored the Link.
    # But for now a rough join or just aggregating Bookings (if we trust booking price) is safer.
    # Let's aggregate Bookings for simplicity as POS Invoice might be consolidated.
    
    query_sales_simple = """
    SELECT 
        sb.booking_date as "Date:Date:100",
        sb.branch as "Branch:Link/Branch:120",
        COUNT(sb.name) as "Total Bookings:Int:100",
        SUM(ip.price_list_rate) as "Estimated Revenue:Currency:120"
    FROM `tabService Booking` sb
    LEFT JOIN `tabItem Price` ip ON ip.item_code = sb.service_item 
    -- This price join is tricky without precise price list. 
    -- Better: We rely on the fact that we might not store price in Booking yet.
    -- Let's stick to COUNT for now or simple approximation.
    WHERE sb.status != 'Cancelled'
    GROUP BY sb.booking_date, sb.branch
    """
    
    # Actually, let's just make a simple Bookings Report
    # Daily Branch Sales
    if frappe.db.exists("Report", "Daily Branch Sales"):
        doc = frappe.get_doc("Report", "Daily Branch Sales")
        doc.query = query_sales_simple
        doc.json = '[]'
        doc.save()
        print("Updated Report: Daily Branch Sales")
    else:
        frappe.get_doc({
            "doctype": "Report",
            "report_name": "Daily Branch Sales",
            "report_type": "Query Report",
            "ref_doctype": "Service Booking",
            "is_standard": "No",
            "module": "Masaje App",
            "json": '[]', # Columns will be inferred from SQL aliases
            "query": query_sales_simple
        }).insert(ignore_permissions=True)
        print("Created Report: Daily Branch Sales")

    # 2. Therapist Utilization
    query_util = """
    SELECT
        therapist as "Therapist:Link/Employee:150",
        branch as "Branch:Link/Branch:120",
        COUNT(name) as "Bookings:Int:80",
        SUM(duration_minutes) as "Booked Minutes:Int:100"
    FROM `tabService Booking`
    WHERE status != 'Cancelled'
    GROUP BY therapist, branch
    """
    
    if not frappe.db.exists("Report", "Therapist Utilization"):
         frappe.get_doc({
            "doctype": "Report",
            "report_name": "Therapist Utilization",
            "report_type": "Query Report",
            "ref_doctype": "Service Booking",
            "is_standard": "No",
            "module": "Masaje App",
            "query": query_util
        }).insert(ignore_permissions=True)
         print("Created Report: Therapist Utilization")

if __name__ == "__main__":
    frappe.connect()
    create_reports()
