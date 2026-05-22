from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    transactions  = db.relationship("Transaction", backref="user", lazy=True)


class Transaction(db.Model):
    __tablename__ = "transactions"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type        = db.Column(db.String(10), nullable=False)   # "income" | "expense"
    category    = db.Column(db.String(50), nullable=False)
    amount      = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), default="")
    date        = db.Column(db.Date, nullable=False)
