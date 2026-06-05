import app
import os
from config import Config
from services.item_importer import import_items_from_csv
from models import Item

application = app.create_app()
