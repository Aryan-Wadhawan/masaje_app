
import shutil
import os
import frappe

def run():
    # Source: The outer directory where I've been working (apps/masaje_app/masaje_app/report)
    src_base = frappe.get_app_path("masaje_app", "report")
    
    # Target: The nested directory (apps/masaje_app/masaje_app/masaje_app/report)
    # frappe.get_app_path("masaje_app") returns .../apps/masaje_app/masaje_app
    tgt_base = os.path.join(frappe.get_app_path("masaje_app"), "masaje_app", "report")
    
    print(f"Source: {src_base}")
    print(f"Target: {tgt_base}")
    
    reports = ["daily_branch_sales", "therapist_utilization"]
    
    for r in reports:
        s_dir = os.path.join(src_base, r)
        t_dir = os.path.join(tgt_base, r)
        
        if os.path.exists(s_dir) and os.path.exists(t_dir):
            print(f"Syncing {r}...")
            # Copy py, js, json from Source to Target
            for ext in [".py", ".js", ".json"]:
                f = f"{r}{ext}"
                shutil.copy2(os.path.join(s_dir, f), os.path.join(t_dir, f))
                print(f"  Copied {f}")
                
            # Copy __init__.py if missing
            if not os.path.exists(os.path.join(t_dir, "__init__.py")):
                open(os.path.join(t_dir, "__init__.py"), 'a').close()
                print("  Created __init__.py")
                
    print("Sync Complete. Please restart bench.")
