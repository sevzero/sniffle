from flask import Flask, request, redirect, jsonify, send_from_directory, render_template, make_response
from flask_sqlalchemy import SQLAlchemy
import time
import os
import re
import subprocess

app = Flask(__name__)

database_dir = '/data/db'
rules_dir = '/data/rules'
app.config['UPLOAD_FOLDER'] = "/data/pcaps"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s/uploads.db' % database_dir
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Pcap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pcap_name = db.Column(db.String(256), unique=True, nullable=False)
    original_filename = db.Column(db.String(256), unique=True, nullable=False)

def create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

create_dir(app.config['UPLOAD_FOLDER'])
create_dir(database_dir)
create_dir(rules_dir)
db.create_all()

def process_alerts(out):
    results = []
    alerts = out.split('\n\n')
    for alert_text in alerts:
        if not alert_text.strip():
            continue
        alert = {}
        alert_lines = alert_text.split('\n')
        alert['rule'] = alert_lines[0].split('[**]')[1].strip()
        alert['detail'] = alert_lines[2]
        results.append(alert)
    return results


def run_snort(rules, pcap):
    result = subprocess.Popen(["snort", "-c", "snort.conf", "--pcap-single=%s" % pcap], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = result.communicate()
    print (pcap)
    out = out.decode()
    err = err.decode()
    if 'ERROR:' in err:
        return "error", [line for line in err.split('\n') if line.startswith('ERROR:')][0], []
    else:
        alerts = process_alerts(out)
        return "success", "Fired %d alerts" % len(alerts), alerts

@app.route('/static/<path:path>')
def serve_static():
    return send_from_directory(path)

@app.route('/inc/<path:path>')
def serve_include(path):
    return render_template(path)

@app.route('/run_rules', methods=['POST'])
def run_rules():
    post_data = request.get_json(force=True) 
    rules = post_data['rules']
    pcap = post_data['pcap_id'].replace('/', '')
    with open('%s/rules.rules' % rules_dir, 'wb') as rules_file:
        rules_file.write(bytes(rules, encoding="utf-8"))
    status, msg, alerts = run_snort(rules='%s/rules.rules' % rules_file, pcap="%s/%s" % (app.config['UPLOAD_FOLDER'], pcap))
    return jsonify({"status":status, "msg":msg, "alerts":alerts})

def gen_session_id():
    return os.urandom(16).hex()

@app.route('/', methods=['GET', 'POST'])
def base():
    response = make_response(render_template('base.html'))
    if not request.cookies.get('sess_id'):
        response.set_cookie('sess_id', gen_session_id())
    return response

valid_extensions = ['.pcap', '.pcapng', '.cap']
session_id_regex = re.compile('^[a-fA-F0-9]{32}$')

@app.route('/upload_pcap', methods=["POST"])
def upload_pcap():
    if not session_id_regex.match(request.cookies['sess_id']):
        return jsonify({"status":"ERROR", "msg":"Invalid session ID"})
    if 'file' not in request.files:
        return jsonify({"status":"error", "msg":"File missing"})
    file = request.files['file']
    if not [i for i in valid_extensions if file.filename.endswith(i)]:
        return jsonify({"status":"error", "msg":"Invalid file extension"})
    filename = str(int(time.time()))
    remember = request.headers.get("X-Remember")
    if remember == 'true':
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        pcap = Pcap(pcap_name=filename, original_filename=file.filename)
        db.session.add(pcap)
        db.session.commit()
    else:
        filename = "tmp_" + request.cookies['sess_id']
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({"status":"success", "msg":"File uploaded successfully", "filename":file.filename, "id":filename})

@app.route('/get_pcaps')
def get_pcaps():
    pcaps = Pcap.query.all()
    pcap_list = []
    for pcap in pcaps:
        pcap_list.append({'name':pcap.original_filename, 'id':pcap.pcap_name})
    return jsonify(pcap_list)

if __name__ == '__main__':
    app.run(port=8080, host="0.0.0.0", debug=True)
