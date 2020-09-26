# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python38_render_template]
import datetime

from flask import Flask, render_template, request, Response, redirect


from huts.Huts import Huts

app = Flask(__name__)


@app.route('/')
def root():
    start_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
    #start_datetime = datetime.datetime.now().strftime("%d.%m.%Y")
    return render_template('index.html', date=start_datetime)

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/map')
def map():
    start_date = request.args.get('date', default = 'now', type = str)
    days_from_start = request.args.get('plus', default = 0, type = int)
    sleep = request.args.get('sleep', default = 0, type = float)
    link = "https://map.geo.admin.ch/?topic=ech&lang=en&bgLayer=ch.swisstopo.pixelkarte-farbe&zoom=2&layers_opacity=0.65,0.75,1&E=2662509.24&N=1172513.90&layers_visibility=false,false,true&layers=ch.bav.haltestellen-oev,ch.swisstopo.swisstlm3d-wanderwege,KML%7C%7Chttps:%2F%2Fmtn-huts.oa.r.appspot.com%2Fhuts.kml%3Fdate%3D{date}%26plus%3D{days}"   
    return  redirect(link.format(days=days_from_start, date=start_date), code=302)


# /huts.kml?date=now&plus=5
@app.route('/huts.kml')
def huts_kml():
    start_date = request.args.get('date', default = 'now', type = str)
    days_from_start_date = request.args.get('plus', default = 0, type = int)
    _limit = request.args.get('_limit', default = 2000, type = int)
    #sleep = request.args.get('sleep', default = 0, type = float)
        
    huts = Huts(start_date = start_date, days_from_start_date = days_from_start_date, show_future_days = 9, limit=_limit)
    kml = huts.generate_kml()
    return Response(kml.kml(), mimetype='application/vnd.google-earth.kml+xml')


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python38_render_template]
