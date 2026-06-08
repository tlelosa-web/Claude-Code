import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app
from config import Config
from services.item_importer import import_items_from_csv
from models import Item

application = app.create_app()
