
import frappe
import sys
import importlib

# Force reload
mod_name = 'masaje_app.masaje_app.report.daily_branch_sales.daily_branch_sales'
if mod_name in sys.modules:
    importlib.reload(sys.modules[mod_name])
else:
    importlib.import_module(mod_name)

mod_name_2 = 'masaje_app.masaje_app.report.therapist_utilization.therapist_utilization'
if mod_name_2 in sys.modules:
    importlib.reload(sys.modules[mod_name_2])
else:
    importlib.import_module(mod_name_2)

from masaje_app.masaje_app.report.daily_branch_sales.daily_branch_sales import execute as exec_sales
from masaje_app.masaje_app.report.therapist_utilization.therapist_utilization import execute as exec_util

def run():
    print("--- Testing Daily Branch Sales (Reloaded) ---")
    frappe.set_user("Administrator") 
    cols, data = exec_sales(filters={"branch": "Bohol Main"})
    print(f"Data Rows (Main): {len(data)}")
    if data:
        print(f"Row 1: {data[0]}")
    else:
        print("FAIL: No data for Bohol Main")

    cols, data = exec_sales(filters={"branch": "Panglao Branch"})
    print(f"Data Rows (Panglao): {len(data)}")
    
    print("\n--- Testing Therapist Utilization (Reloaded) ---")
    cols, data = exec_util(filters={})
    print(f"Data Rows: {len(data)}")
    if data:
        print(f"Row 1: {data[0]}")
