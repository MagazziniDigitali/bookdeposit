#!/usr/bin/env python

import os
import tempfile
import time
import datetime
from functools import wraps

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify, send_from_directory
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from werkzeug.utils import secure_filename

from bookdeposit.config import config
from bookdeposit.process import validate
from bookdeposit.db import db, Deposit, DepositSchema
from bookdeposit.user import User

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=90)

app.config['UPLOAD_FOLDER'] = config.get('server', 'incoming_dir')
app.config['PROCESSED_FOLDER'] = config.get('server', 'processed_dir')


jwt = JWTManager(app)

ALLOWED_EXTENSIONS = set(['zip'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

#
# WEB
#


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = User(request.form['username'], request.form['password'])
        login = user.login()
        # print(login['status'])
        if login['status'] == "OK":
            session['logged_in'] = True
            session['user_id'] = login['user_id']

            jwt_token = create_access_token(identity=login['user_id'])
            session['jwt_token'] = jwt_token
            flash('You were logged in')
            return redirect(url_for('list'))
        else:
            error = login['error']
    return render_template('login.html', error=error)


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    flash('You were logged out')
    return redirect(url_for('index'))


@app.route('/list', methods=['GET'])
@login_required
def list():
    return render_template("list.html")


@app.route('/upload', methods=['GET'])
@login_required
def upload():
    return render_template("upload.html")


@app.route('/status/<uuid>', methods=['GET'])
@login_required
def status(uuid):
    return render_template("status.html", uuid=uuid)


@app.route('/documentation', methods=['GET'])
def documentation():
    return render_template("documentation.html")


#
# API
#

@app.route('/api/v1/auth', methods=['POST'])
def v1login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    u = User(username, password)
    login = u.login()

    if (login['status'] == "OK"):
        ret = {'access_token': create_access_token(identity=u.id)}
        return jsonify(ret), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401


@app.route('/api/v1/list', methods=['GET'])
@jwt_required
def v1list():
    current_user = get_jwt_identity()
    deposits = Deposit.query.filter_by(
        user_id=current_user).order_by(desc(Deposit.date)).all()
    deposit_schema = DepositSchema(many=True)
    return jsonify(deposit_schema.dump(deposits).data)


@app.route('/api/v1/status/<uuid>', methods=['GET'])
def v1status(uuid):
    deposits = Deposit.query.filter_by(bag_uuid=uuid).first_or_404()
    deposit_schema = DepositSchema()
    return jsonify(deposit_schema.dump(deposits).data)


@app.route('/api/v1/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'],
                               filename, as_attachment=True)


@app.route('/api/v1/upload', methods=['POST'])
@jwt_required
def v1upload():
    current_user = get_jwt_identity()

    if request.method == 'POST':
        if 'bag' not in request.files:
            return "ERROR: missing bag."

        bag = request.files['bag']
        if bag and allowed_file(bag.filename):
            tmpdir = tempfile.mkdtemp(
                dir=app.config['UPLOAD_FOLDER'],
                suffix="_1",
                prefix=None)
            destination_file = (os.path.join(
                tmpdir, secure_filename(bag.filename)))
            bag.save(destination_file)

            # destination_file = full path of zipped bag into
            # config.incoming_dir
            job = validate.delay(destination_file, current_user)

            bag_name = os.path.basename(os.path.splitext(destination_file)[0])
            new_deposit = Deposit(job.id, bag_name, current_user)
            new_deposit.status = "QUEUE"
            db.session.add(new_deposit)
            db.session.commit()

            return jsonify(status="queued", job=job.id, bag_name=bag.filename)
    return "bag upload"

if __name__ == '__main__':
    app.run(debug=True)
