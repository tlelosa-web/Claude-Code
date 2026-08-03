import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[0] / '4_Scripts' / 'backend'))
from pdf_generator import generate_test_record_sheet
from pdf_generator_backup import make_nameplate_pdf

payload = {
    'nameplate': {
        'customer_name': 'Fan Movement',
        'series': 'MAXFLO - BIFURCATED',
        'size': '500/165/9 A',
        'serial_no': 'FM4055',
        'class_pitch': '25',
        'voltage': '380',
        'op_speed': '1440',
        'phase': '3',
        'connection': 'STAR',
        'fla': '1.37',
        'manufacturer': 'ACTOM',
        'date_of_manuf': '17/05/2026',
        'relube_interval': 'N/A',
    },
    'derived': {
        'date': '17/05/2026',
        'motor_description': '0.55 kW motor',
        'procedure_used': 'QC-WI-05',
        'imp_form': 'FORM B',
        'fan_speed': '1440',
        'motor_current': '1.37',
        'connection': 'STAR',
        'motor_serial_number': 'FM4055',
        'blade_pitch_deg': '25',
        'tacho_clamp_serial_no': 'N/A',
        'speed_actual': '1440',
        'current_ph1': '',
        'current_ph2': '',
        'current_ph3': '',
        'voltage_ph1': '380',
        'voltage_ph2': '380',
        'voltage_ph3': '380',
    },
}

out_dir = str(Path(__file__).resolve().parents[0] / '3_Live_Reports' / 'output')

try:
    p = generate_test_record_sheet(payload, out_dir=out_dir)
    print('Test sheet generated:', p)
except Exception as e:
    import traceback
    traceback.print_exc()

# Generate nameplate
try:
    sample = {
        'series': 'MAXFLO',
        'class_pitch': '34',
        'motor': '2.2',
        'voltage': '380',
        'fla': '4.84',
        'op_temp': '20',
        'serial_no': 'FM5107',
        'size': '630',
        'op_speed': '1440',
        'max_speed': '1440',
        'phase': '3',
        'frequency': '50',
        'connection': 'STAR',
        'date_of_manuf': 'DEC 2025',
        'relube_interval': 'N/A',
    }
    outp = Path(out_dir).parent.parent / '3_Live_Reports' / 'output' / 'nameplate_test.pdf'
    make_nameplate_pdf(sample, str(outp))
    print('Nameplate generated:', outp)
except Exception:
    import traceback
    traceback.print_exc()
