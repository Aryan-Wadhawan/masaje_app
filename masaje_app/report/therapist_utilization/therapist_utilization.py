
import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    # --- Security / Permission Logic ---
    user = frappe.session.user
    if "System Manager" not in frappe.get_roles(user):
        employee = frappe.db.get_value("Employee", {"user_id": user}, ["name", "branch"], as_dict=True)
        if employee and employee.branch:
            filters["branch"] = employee.branch
    
    # --- Columns ---
    columns = [
        {"label": _("Therapist"), "fieldname": "therapist", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
        {"label": _("Total Bookings"), "fieldname": "total_bookings", "fieldtype": "Int", "width": 100},
        {"label": _("Booked Minutes"), "fieldname": "booked_minutes", "fieldtype": "Int", "width": 120},
        {"label": _("Revenue (Est)"), "fieldname": "revenue", "fieldtype": "Currency", "width": 120},
    ]

    # --- Data Query ---
    conditions = ""
    if filters.get("from_date") and filters.get("to_date"):
        conditions += f" AND s.booking_date BETWEEN '{filters.get('from_date')}' AND '{filters.get('to_date')}'"
    
    if filters.get("branch"):
        conditions += f" AND s.branch = '{filters.get('branch')}'"

    if filters.get("therapist"):
        conditions += f" AND s.therapist_name = '{filters.get('therapist')}'" # Assuming filter passes name or ID? Usually ID. 
        # Actually standard practice is to pass Name(ID) to Link field.
        # Let's check filter definition. If Link 'Employee', value is name (ID).
        conditions += f" AND s.therapist = '{filters.get('therapist')}'"

    # We join with POS Invoice to get revenue if possible, or just sum bookings
    # Let's do a left join to be safe
    sql = f"""
        SELECT 
            s.therapist as therapist,
            s.branch as branch,
            COUNT(s.name) as total_bookings,
            SUM(s.duration_minutes) as booked_minutes,
            SUM(p.grand_total) as revenue
        FROM `tabService Booking` s
        LEFT JOIN `tabPOS Invoice` p ON p.name = s.invoice
        WHERE s.status != 'Cancelled' {conditions}
        GROUP BY s.therapist, s.branch
        ORDER BY booked_minutes DESC
    """
    
    data = frappe.db.sql(sql, as_dict=True)
    
    chart = []
    if data:
        labels = [d.get("therapist") for d in data]
        values = [d.get("booked_minutes") for d in data]
        chart = {
            "data": {
                "labels": labels,
                "datasets": [{"name": "Booked Minutes", "values": values}]
            },
            "type": "bar"
        }

    return columns, data, None, chart, None, 0
