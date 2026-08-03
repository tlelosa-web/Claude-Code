from pathlib import Path
import sys
sys.path.insert(0, str(Path('4_Scripts/backend').resolve()))
from excel_source import read_nameplate_from_excel

p = Path('2_Source_Data/raw_sources/NAME PLATE PROCEDURE.xlsx')
print('exists', p.exists())
result = read_nameplate_from_excel(str(p))
print('read result:')
for k, v in result.items():
    print(f'{k}: {v}')
