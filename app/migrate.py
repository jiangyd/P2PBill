import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import db,app

from flask_migrate import Migrate,MigrateCommand

migrate=Migrate(app,db)


from flask_script import Manager


manager=Manager(app)
manager.add_command('db',MigrateCommand)

if __name__=="__main__":
    manager.run()
