import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import shutil
import tempfile
import app
from config import Config

temp_dir = tempfile.mkdtemp()
print(f"Using temp dir: {temp_dir}")

class TempConfig(Config):
    INSTANCE_DIR = temp_dir
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(temp_dir, 'sops.db').replace(chr(92), '/')}"

application = app.create_app(TempConfig)
with application.app_context():
    from models import Item
    print(f"Items imported: {Item.query.count()}")

real_instance = os.path.join(Config.BASE_DIR, 'instance')
os.makedirs(real_instance, exist_ok=True)
db_src = os.path.join(temp_dir, 'sops.db')
db_dst = os.path.join(real_instance, 'sops.db')

if os.path.exists(db_dst):
    os.remove(db_dst)
if os.path.exists(db_src):
    shutil.copy2(db_src, db_dst)
    print(f"Moved DB to {db_dst}")
else:
    print("No DB created!")
