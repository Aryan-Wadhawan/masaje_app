
import frappe
import json
import os

def run():
    workspace_name = "Masaje Reception"
    
    # Path to the JSON file we just wrote
    # Based on previous file explorations: apps/masaje_app/masaje_app/masaje_app/workspace/masaje_reception/masaje_reception.json
    file_path = frappe.get_app_path("masaje_app", "masaje_app", "workspace", "masaje_reception", "masaje_reception.json")
    
    if not os.path.exists(file_path):
        # Try alternative path just in case
        file_path = frappe.get_app_path("masaje_app", "workspace", "masaje_reception", "masaje_reception.json")
    
    if not os.path.exists(file_path):
        print(f"CRITICAL: Could not find workspace file at {file_path}")
        return

    print(f"Reading workspace config from: {file_path}")
    
    with open(file_path, "r") as f:
        data = json.load(f)
    
    # Update or Create the Workspace Doc
    if frappe.db.exists("Workspace", workspace_name):
        doc = frappe.get_doc("Workspace", workspace_name)
    else:
        doc = frappe.new_doc("Workspace")
        doc.name = workspace_name
        doc.label = workspace_name

    # Update fields
    doc.content = data.get("content")
    doc.public = 1
    doc.title = data.get("title")
    doc.module = data.get("module")
    
    # Clear and Reload Child Tables
    doc.set("links", [])
    doc.set("shortcuts", [])
    doc.set("roles", [])
    doc.set("charts", [])
    
    for link in data.get("links", []):
        doc.append("links", link)
        
    for shortcut in data.get("shortcuts", []):
        doc.append("shortcuts", shortcut)
        
    for role in data.get("roles", []):
        doc.append("roles", role)
        
    doc.save()
    frappe.db.commit()
    print(f"Successfully updated Workspace: {workspace_name}")
