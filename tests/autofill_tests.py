from pathlib import Path
import sys
import json

# Ensure backend modules are importable
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "4_Scripts" / "backend"
sys.path.insert(0, str(BACKEND))

print(f"Backend path: {BACKEND}")

try:
    from main import _speed_from_pole
    from connection_lookup import suggest_connection
    from motor_fla_lookup import lookup_fla_safe
except Exception as e:
    print("Failed to import backend helpers:", e)
    raise

print("\n== op_speed mapping ==")
for p in [2,4,6,8,10]:
    print(f"poles={p} -> speed={_speed_from_pole(p)}")

print("\n== suggest_connection tests ==")
tests = [
    (380, 2, 2.5),
    (380, 2, 5.0),
    (525, 4, 3.5),
    (220, 4, 2.0),
]
for v,p,m in tests:
    conn, err = suggest_connection(v, p, m)
    print(f"voltage={v}, pole={p}, motor={m}kW -> connection={conn} (err={err})")

print("\n== lookup_fla_safe tests (motor PDF may be missing) ==")
# Provide a non-existent pdf path to see the error handling
fla, err = lookup_fla_safe(1.5, 4, 400.0, str(BACKEND / "nonexistent_motor_table.pdf"))
print(f"lookup_fla_safe -> fla={fla}, err={err}")

print("\nAll tests complete.")
