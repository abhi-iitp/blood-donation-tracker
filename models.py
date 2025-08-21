from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class BloodStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blood_group = db.Column(db.String(5), unique=True, nullable=False)
    units = db.Column(db.Integer, default=0)
    threshold = db.Column(db.Integer, default=5)   # 👈 new column

    def is_low(self):
        return self.units < self.threshold
