import os
from cbt_test import create_app, db

app = create_app()

with app.app_context():
    if not os.path.exists('site.db'):
        db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
