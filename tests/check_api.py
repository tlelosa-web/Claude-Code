import json
import urllib.request
import urllib.error

base = 'http://127.0.0.1:8000'
print('OPTIONS')
try:
    with urllib.request.urlopen(base + '/api/options') as r:
        print('options', r.status)
        print(r.read(200).decode('utf-8'))
except Exception as e:
    print('options error', e)

print('\nNAMEPLATE FROM EXCEL')
try:
    with urllib.request.urlopen(base + '/api/nameplate/from-excel') as r:
        print('status', r.status)
        data = json.load(r)
        print({k: data.get('nameplate', {}).get(k) for k in ['customer_name', 'series', 'size', 'op_speed', 'pole']})
except urllib.error.HTTPError as e:
    print('status', e.code, e.read().decode('utf-8'))
except Exception as e:
    print('error', e)

print('\nTEST SHEET FROM NAMEPLATE')
payload = {
    'customer_name': 'BREEZEAIR TECHNICAL SERVICES',
    'serial_no': 'FM4032',
    'series': 'MAXFLO',
    'class_pitch': '26',
    'imp_form': 'FORM B',
    'size': '560/250/12 P',
    'motor': '1.1',
    'pole': '4',
    'voltage': '380',
    'phase': '3',
    'date_of_manuf': '2026-05-06',
    'frequency': '50',
    'op_temp': '20',
    'op_speed': '1440',
    'fla': '2.5',
    'connection': 'STAR',
    'relube_interval': 'N/A',
    'manufacturer': 'ACTOM'
}
req = urllib.request.Request(base + '/api/reports/test-record-sheet/from-nameplate', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as r:
        print('status', r.status, 'content-type', r.getheader('Content-Type'))
        body = r.read(12)
        print('pdf bytes', len(body), body[:12])
except urllib.error.HTTPError as e:
    print('status', e.code, e.read().decode('utf-8'))
except Exception as e:
    print('error', e)
