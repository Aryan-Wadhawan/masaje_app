
import frappe
import json

def execute():
    create_workspace()

def create_workspace():
    name = "Masaje Reception"
    if frappe.db.exists("Workspace", name):
        # Update existing
        ws = frappe.get_doc("Workspace", name)
    else:
        ws = frappe.new_doc("Workspace")
        ws.name = name
        ws.label = "Masaje Reception"
        ws.title = "Masaje Reception"

    ws.is_standard = 0
    ws.public = 1
    
    # 1. Clear existing
    ws.shortcuts = []
    ws.links = []
    
    # 2. Add Shortcuts
    ws.append("shortcuts", {
        "label": "Book Now",
        "type": "URL",
        "link": "http://localhost:5173",
        "color": "Green"
    })
    ws.append("shortcuts", {
        "label": "Open POS",
        "type": "Page",
        "link": "pos",
        "color": "Blue"
    })
    ws.append("shortcuts", {
        "label": "Booking Calendar",
        "type": "DocType",
        "link": "Service Booking",
        "url_data": json.dumps({"view": "Calendar"}),
        "color": "Orange"
    })

    # 3. Add Links (Cards)
    # Card: Lists
    ws.append("links", {
        "label": "Service Bookings",
        "type": "Link",
        "link_to": "Service Booking",
        "link_type": "DocType",
        "onboard": 0
    })
    ws.append("links", {
        "label": "Customers",
        "type": "Link",
        "link_to": "Customer",
        "link_type": "DocType",
        "onboard": 0
    })
    ws.append("links", {
        "label": "Therapist Schedules",
        "type": "Link",
        "link_to": "Therapist Schedule",
        "link_type": "DocType",
        "onboard": 0
    })

    # 4. Generate Content JSON (referencing the above)
    # The 'content' field is an array of blocks.
    # We must ensure the 'link' properties here refer to valid routes.
    
    ws.content = json.dumps([
        {
            "type": "header",
            "data": {"text": "Reception Dashboard", "level": 3, "col": 12}
        },
        {
            "type": "shortcut",
            "data": {
                "shortcut_name": "Booking Calendar",
                "label": "Booking Calendar",
                "type": "DocType",
                "link": "Service Booking",
                "url_data": {"view": "Calendar"},
                "color": "Orange"
            }
        },
        {
             "type": "shortcut",
             "data": {
                 "shortcut_name": "New Booking",
                 "label": "New Booking",
                 "type": "DocType",
                 "link": "Service Booking",
                 "color": "Green"
             }
        },
        {
            "type": "shortcut",
            "data": {
                "shortcut_name": "Open POS",
                "label": "Open POS",
                "type": "Page",
                "link": "point-of-sale",
                "color": "Blue"
            }
        },
        {
            "type": "spacer",
            "data": {"col": 12}
        },
        {
            "type": "card",
            "data": {
                "card_name": "Lists",
                "label": "Lists",
                "links": [
                    {"label": "Service Bookings", "type": "Link", "link": "Service Booking", "link_type": "DocType"},
                    {"label": "Customers", "type": "Link", "link": "Customer", "link_type": "DocType"},
                    {"label": "Therapist Schedules", "type": "Link", "link": "Therapist Schedule", "link_type": "DocType"}
                ]
            }
        }
    ])
    
    # 5. Save
    ws.save(ignore_permissions=True)
    
    # 6. Set Roles
    # Explicitly add roles using SQL or Child Table append if not present
    # We need to ensure 'System Manager' (Admin) and 'Receptionist' have access.
    
    roles_to_add = ["Receptionist", "System Manager", "Sales User"]
    
    current_roles = [r.role for r in ws.roles]
    
    for role in roles_to_add:
        if role not in current_roles:
            ws.append("roles", {"role": role})
            
    ws.save(ignore_permissions=True)
    print(f"Created Workspace: {name} with Roles: {roles_to_add}")
