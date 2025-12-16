# Copyright (c) 2025, Masaje de Bohol
# License: MIT

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "therapist",
            "label": _("Therapist"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 180
        },
        {
            "fieldname": "therapist_name",
            "label": _("Therapist Name"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "total_invoices",
            "label": _("Invoices"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "total_sales",
            "label": _("Total Sales"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "commission_rate",
            "label": _("Rate %"),
            "fieldtype": "Percent",
            "width": 80
        },
        {
            "fieldname": "total_commission",
            "label": _("Commission"),
            "fieldtype": "Currency",
            "width": 120
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT 
            pi.therapist,
            e.employee_name as therapist_name,
            COUNT(pi.name) as total_invoices,
            SUM(pi.grand_total) as total_sales,
            e.commission_rate,
            SUM(COALESCE(pi.total_commission, 0)) as total_commission
        FROM `tabPOS Invoice` pi
        LEFT JOIN `tabEmployee` e ON pi.therapist = e.name
        WHERE pi.docstatus = 1
            AND pi.therapist IS NOT NULL
            AND pi.therapist != ''
            {conditions}
        GROUP BY pi.therapist
        ORDER BY total_commission DESC
    """.format(conditions=conditions), filters, as_dict=1)
    
    return data


def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append("AND pi.posting_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("AND pi.posting_date <= %(to_date)s")
    
    if filters.get("branch"):
        conditions.append("AND pi.branch = %(branch)s")
    
    if filters.get("therapist"):
        conditions.append("AND pi.therapist = %(therapist)s")
    
    return " ".join(conditions)
