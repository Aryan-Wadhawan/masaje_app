"""
Update Masaje Reception workspace to include new reports
Run: bench --site erpnext.localhost execute masaje_app.scripts.update_workspace_reports.setup
"""
import frappe
import json


def setup():
    """Update the Masaje Reception workspace with new reports"""
    print("Updating Masaje Reception workspace with reports...")
    
    workspace_name = "Masaje Reception"
    
    if not frappe.db.exists("Workspace", workspace_name):
        print(f"Workspace '{workspace_name}' not found")
        return
    
    workspace = frappe.get_doc("Workspace", workspace_name)
    
    # New reports to add
    new_reports = [
        {
            "label": "Therapist Commission",
            "link_to": "Therapist Commission",
            "link_type": "Report",
            "type": "Link",
            "is_query_report": 1
        },
        {
            "label": "Popular Services",
            "link_to": "Popular Services",
            "link_type": "Report",
            "type": "Link",
            "is_query_report": 1
        },
        {
            "label": "Peak Hours",
            "link_to": "Peak Hours",
            "link_type": "Report",
            "type": "Link",
            "is_query_report": 1
        }
    ]
    
    # Get existing link labels
    existing_links = {link.label for link in workspace.links}
    
    # Find the Reports card break to insert after
    insert_idx = len(workspace.links)
    for i, link in enumerate(workspace.links):
        if link.label == "Reports" and link.type == "Card Break":
            insert_idx = i + 1
            break
    
    # Insert new reports after the Reports card break
    added = 0
    for report in new_reports:
        if report["label"] not in existing_links:
            workspace.append("links", report)
            added += 1
            print(f"  + Added: {report['label']}")
    
    if added:
        workspace.save()
        frappe.db.commit()
    
    print(f"✓ Workspace updated with {added} new reports!")


if __name__ == "__main__":
    setup()
