import requests
import re

# GET the build_bom page
response = requests.get('http://127.0.0.1:5000/sales-orders/5/build-bom')

# Extract UNIQUE line IDs from the HTML
line_ids = list(set(re.findall(r'name="line_role_(\d+)"', response.text)))
line_ids.sort(key=int)  # Sort numerically
print(f"Unique Line IDs found in form: {line_ids}")

if line_ids:
    # Build POST data with correct line IDs
    data = {}
    for i, line_id in enumerate(line_ids):
        if i == 0:
            data[f'line_role_{line_id}'] = 'fan'  # First line as fan
        else:
            data[f'line_role_{line_id}'] = 'stock'  # Rest as stock
    
    data['component_item_id[]'] = ['1290', '2']
    data['component_qty[]'] = ['1', '1']
    
    print(f"\nSending POST with {len(data)} fields")
    print(f"Fan line: line_role_{line_ids[0]}")
    
    # Send POST request
    post_response = requests.post('http://127.0.0.1:5000/sales-orders/5/build-bom', data=data, allow_redirects=True)
    
    print(f'\nStatus: {post_response.status_code}')
    print(f'Final URL: {post_response.url}')
    
    if post_response.status_code == 500:
        print('\n❌ SERVER ERROR (500)')
        # Try to find error details
        error_match = re.search(r'<title>([^<]+Error[^<]*)</title>', post_response.text, re.IGNORECASE)
        if error_match:
            print(f'Error title: {error_match.group(1)}')
    
    # Check result
    if 'Works Pack created successfully' in post_response.text:
        match = re.search(r'Works Pack created successfully[^<]*', post_response.text)
        if match:
            print('\n✅ SUCCESS:', match.group(0))
    elif 'Please select at least one Fan line' in post_response.text:
        print('\n❌ ERROR: Fan line validation failed')
    else:
        print('\n⚠️ Unknown outcome')
