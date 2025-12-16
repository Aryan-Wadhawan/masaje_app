[
    {
        "fieldname": "from_date",
        "fieldtype": "Date",
        "label": "From Date",
        "mandatory": 0,
        "default": "frappe.datetime.add_months(frappe.datetime.get_today(), -1)"
    },
    {
        "fieldname": "to_date",
        "fieldtype": "Date",
        "label": "To Date",
        "mandatory": 0,
        "default": "frappe.datetime.get_today()"
    },
    {
        "fieldname": "branch",
        "fieldtype": "Link",
        "label": "Branch",
        "options": "Branch",
        "mandatory": 0
    },
    {
        "fieldname": "therapist",
        "fieldtype": "Link",
        "label": "Therapist",
        "options": "Employee",
        "mandatory": 0
    }
]
