# Book a Service - Page Controller
# Route: /book

import frappe

def get_context(context):
    """Context for the booking page."""
    context.no_cache = 1
    context.title = "Book a Service | Masaje de Bohol"
    
    # Fetch initial data for the page
    context.branches = frappe.get_all("Branch", fields=["name"], ignore_permissions=True)
    
    # Get all service items with prices (we'll fetch prices dynamically per branch)
    context.services = frappe.db.sql("""
        SELECT DISTINCT i.name, i.item_name, i.description, i.image, i.item_group
        FROM `tabItem` i
        WHERE i.item_group IN (
            SELECT name FROM `tabItem Group` 
            WHERE parent_item_group = 'Services' OR name = 'Services'
        )
        AND i.disabled = 0
        ORDER BY i.item_group, i.item_name
    """, as_dict=True)
    
    return context
