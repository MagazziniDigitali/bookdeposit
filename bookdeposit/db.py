#!/usr/bin/env python

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

from flask_marshmallow import Marshmallow
import datetime

from bookdeposit.config import config

app = Flask(__name__)

dburi = "sqlite:///{}".format(config.get('server', 'db'))
app.config['SQLALCHEMY_DATABASE_URI'] = dburi
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)


class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bag_uuid = db.Column(db.String(50), index=True, unique=True)
    bag_name = db.Column(db.String(255))
    user_id = db.Column(db.String(50), index=True)
    date = db.Column(db.DateTime(), default=datetime.datetime.now)
    status = db.Column(db.Enum('SUCCESS', 'FAILURE', 'QUEUE', 'LONG-TERM'))
    errors = db.Column(db.Text())

    def __init__(self, bag_uuid, bag_name, user_id):
        self.bag_uuid = bag_uuid
        self.bag_name = bag_name
        self.user_id = user_id

    def __repr__(self):
        return '<Deposit %r>' % self.bag_uuid


class DepositSchema(ma.ModelSchema):
    class Meta:
        model = Deposit
