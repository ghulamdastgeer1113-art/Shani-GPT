#!/usr/bin/env python
"""Debug script to check admin blueprint registration."""

import sys
sys.path.insert(0, '.')

print("=" * 60)
print("DEBUGGING ADMIN ROUTES")
print("=" * 60)

try:
    print("\n1. Importing app...")
    from app import app
    print("   ✓ App imported successfully")
    
    print("\n2. Checking blueprints...")
    print(f"   Registered blueprints: {list(app.blueprints.keys())}")
    
    print("\n3. Checking admin routes...")
    admin_routes = [rule.rule for rule in app.url_map.iter_rules() if '/admin' in rule.rule]
    print(f"   Admin routes found: {len(admin_routes)}")
    for route in admin_routes:
        print(f"   - {route}")
    
    if not admin_routes:
        print("\n   ❌ NO ADMIN ROUTES FOUND!")
        print("   This means the blueprint is not registered.")
    else:
        print("\n   ✓ Admin routes are registered")
    
    print("\n4. Testing admin blueprint import...")
    from admin_routes import admin_bp
    print(f"   ✓ admin_bp imported: {admin_bp.name}")
    print(f"   URL prefix: {admin_bp.url_prefix}")
    
    print("\n5. Checking if admin_bp is in app.blueprints...")
    if 'admin' in app.blueprints:
        print("   ✓ admin blueprint is registered in app")
    else:
        print("   ❌ admin blueprint is NOT registered in app")
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)