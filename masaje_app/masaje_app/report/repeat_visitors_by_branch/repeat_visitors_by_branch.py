import frappe
from frappe import _
from typing import Any, Dict, List, Optional, Tuple


def execute(filters: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], None, Dict[str, Any]]:
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart


def get_columns() -> List[Dict[str, Any]]:
    return [
        {
            "fieldname": "customer",
            "label": _("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": 180,
        },
        {
            "fieldname": "customer_name",
            "label": _("Customer Name"),
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "fieldname": "mobile_no",
            "label": _("Mobile No"),
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "fieldname": "branch",
            "label": _("Branch"),
            "fieldtype": "Link",
            "options": "Branch",
            "width": 160,
        },
        {
            "fieldname": "visit_count",
            "label": _("Total Visits"),
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "fieldname": "first_visit",
            "label": _("First Visit"),
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "fieldname": "last_visit",
            "label": _("Last Visit"),
            "fieldtype": "Date",
            "width": 110,
        },
    ]


def get_data(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    conditions = get_conditions(filters)

    data = frappe.db.sql(
        f"""
        SELECT
            sb.customer,
            c.customer_name,
            c.mobile_no,
            sb.branch,
            COUNT(sb.name) AS visit_count,
            MIN(sb.booking_date) AS first_visit,
            MAX(sb.booking_date) AS last_visit
        FROM `tabService Booking` sb
        LEFT JOIN `tabCustomer` c ON sb.customer = c.name
        WHERE sb.status != 'Cancelled'
            {conditions}
        GROUP BY sb.customer, sb.branch
        HAVING COUNT(sb.name) > 1
        ORDER BY visit_count DESC, last_visit DESC
    """,
        filters,
        as_dict=True,
    )

    return data


def get_conditions(filters: Dict[str, Any]) -> str:
    conditions: List[str] = []

    if filters.get("from_date"):
        conditions.append("AND sb.booking_date >= %(from_date)s")

    if filters.get("to_date"):
        conditions.append("AND sb.booking_date <= %(to_date)s")

    if filters.get("branch"):
        conditions.append("AND sb.branch = %(branch)s")

    if filters.get("customer"):
        conditions.append("AND sb.customer = %(customer)s")

    return " ".join(conditions)


def get_chart(data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Simple bar chart of top repeat visitors (by total visits)."""
    if not data:
        return None

    # Top 10 repeat visitors overall
    top = data[:10]
    labels = [f"{row.get('customer_name') or row.get('customer')}" for row in top]
    values = [row.get("visit_count", 0) for row in top]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Total Visits"),
                    "values": values,
                }
            ],
        },
        "type": "bar",
        "colors": ["#5e64ff"],
    }


