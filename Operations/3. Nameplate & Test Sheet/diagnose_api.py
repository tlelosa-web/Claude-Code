"""
Diagnostic script to test API endpoints and identify issues
"""
import json
import urllib.request
import urllib.parse

BASE = "http://127.0.0.1:8000"

def test_endpoint(method, path, params=None):
    """Test an API endpoint"""
    url = f"{BASE}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            print(f"✓ {method} {path}")
            print(f"  Status: {resp.status}")
            print(f"  Response: {json.dumps(body, indent=2)[:500]}")
            return True, body
    except Exception as e:
        print(f"✗ {method} {path}")
        print(f"  Error: {str(e)}")
        return False, None

print("="*60)
print("DIAGNOSTIC TEST - Checking API Endpoints")
print("="*60)

# Test 1: Options endpoint (Voltage, Pole, Motor kW)
print("\n1. Testing /api/options (Voltage, Pole, Motor kW dropdowns)")
success, data = test_endpoint("GET", "/api/options")
if success and data:
    print(f"\n  Voltages available: {data.get('voltages', [])}")
    print(f"  Poles available: {data.get('poles', [])}")
    print(f"  Motors by pole: {list(data.get('motors_by_pole', {}).keys())}")
    if data.get('error'):
        print(f"  ⚠ ERROR: {data['error']}")
else:
    print("  Backend may not be running or options endpoint failed!")

# Test 2: FLA calculation
print("\n2. Testing /api/fla (Full Load Amps calculation)")
test_params = {"motor": "1.5", "pole": "4", "voltage": "380"}
success, data = test_endpoint("GET", "/api/fla", params=test_params)
if success and data:
    print(f"  FLA for 1.5kW, 4 pole, 380V: {data.get('fla', 'N/A')}")
    if data.get('error'):
        print(f"  ⚠ ERROR: {data['error']}")

# Test 3: Connection type
print("\n3. Testing /api/connection (STAR/DELTA)")
success, data = test_endpoint("GET", "/api/connection", params=test_params)
if success and data:
    print(f"  Connection for 1.5kW, 4 pole, 380V: {data.get('connection', 'N/A')}")
    if data.get('error'):
        print(f"  ⚠ ERROR: {data['error']}")

# Test 4: Excel loading
print("\n4. Testing /api/nameplate/from-excel")
success, data = test_endpoint("GET", "/api/nameplate/from-excel")
if success and data:
    if data.get('nameplate'):
        print(f"  ✓ Excel data loaded successfully")
        print(f"  Sample fields: {list(data['nameplate'].keys())[:5]}")
    if data.get('error'):
        print(f"  ⚠ ERROR: {data['error']}")

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)
print("\nIf you see errors above:")
print("1. Make sure backend is running: python -m uvicorn main:app --reload")
print("2. Check that PDF and Excel files exist in 2_Source_Data/raw_sources/")
print("3. Check backend logs for more details")
