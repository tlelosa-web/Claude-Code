import requests
import re

# Build form data
data = {
    'line_role_1': 'fan',
    'line_role_2': 'stock',
    'line_role_3': 'stock',
    'line_role_4': 'stock',
    'line_role_5': 'stock',
    'line_role_6': 'stock',
    'line_role_7': 'stock',
    'line_role_8': 'stock',
    'line_role_9': 'stock'
}
data['component_item_id[]'] = ['1290', '2']
data['component_qty[]'] = ['1', '1']

# Send POST request
response = requests.post('http://127.0.0.1:5000/sales-orders/5/build-bom', data=data, allow_redirects=True)

print(f'Status: {response.status_code}')
print(f'Final URL: {response.url}')

# Check for success or error messages
if 'Works Pack created successfully' in response.text:
    match = re.search(r'Works Pack created successfully[^<]*', response.text)
    if match:
        print('SUCCESS:', match.group(0))
elif 'Please select at least one Fan line' in response.text:
    print('ERROR: Fan line validation failed')
else:
    print('Unknown outcome - checking flash messages...')
    # Try to find any flash message
    matches = re.findall(r'<div class="flash-message[^"]*">([^<]+)</div>', response.text)
    if matches:
        for msg in matches:
            print(f'Flash: {msg}')
    else:
        print('No flash messages found')
