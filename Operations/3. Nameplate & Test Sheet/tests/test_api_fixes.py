import time
import urllib.request
import json

time.sleep(2)  # Give server time to be fully ready

print('=' * 60)
print('TESTING ALL API ENDPOINTS')
print('=' * 60)

# Test 1: /api/fla (FIXED)
print('\n[1] GET /api/fla (CORRECTED PARAMETERS)')
try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/api/fla?motor=1.5&pole=4&voltage=380')
    data = json.loads(response.read().decode('utf-8'))
    print(f'✓ Status: {response.status}')
    print(f'✓ Response: {data}')
except Exception as e:
    print(f'✗ Error: {e}')

# Test 2: /api/connection (FIXED)
print('\n[2] GET /api/connection (CORRECTED PARAMETERS)')
try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/api/connection?voltage=380&pole=4&motor=1.5')
    data = json.loads(response.read().decode('utf-8'))
    print(f'✓ Status: {response.status}')
    print(f'✓ Response: {data}')
except Exception as e:
    print(f'✗ Error: {e}')

# Test 3: /api/options
print('\n[3] GET /api/options')
try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/api/options')
    data = json.loads(response.read().decode('utf-8'))
    print(f'✓ Status: {response.status}')
    print(f'✓ Got {len(data)} options')
except Exception as e:
    print(f'✗ Error: {e}')

# Test 4: /api/nameplate/from-excel (FIXED)
print('\n[4] GET /api/nameplate/from-excel (FIXED EXCEL HANDLING)')
try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/api/nameplate/from-excel')
    data = json.loads(response.read().decode('utf-8'))
    status = 'Error' if data.get('error') else 'Success'
    print(f'✓ Status: {response.status}')
    print(f'✓ Result: {status}')
    if data.get('error'):
        print(f'  Error: {data.get("error")}')
    else:
        nameplate_keys = list(data.get('nameplate', {}).keys())
        print(f'  Nameplate keys loaded: {nameplate_keys[:5]}...')
except Exception as e:
    print(f'✗ Error: {e}')

print('\n' + '=' * 60)
