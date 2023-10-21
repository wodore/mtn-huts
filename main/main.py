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
import urllib

from flask import Flask, render_template, request, Response, redirect, url_for, session
import werkzeug

from flask_babel import Babel
from flask_babel import _



from huts.Huts import Huts
from huts.Hut import Hut
from huts.HutDescription import HutDescription
from config import Config

app = Flask(__name__)

app.config.from_object(Config)

babel = Babel(app)


@babel.localeselector
def get_locale():
    return get_user_language()

def get_user_language():
    # return "it"
    # if not g.get('lang_code', None):
    #     g.lang_code = request.accept_languages.best_match(app.config['LANGUAGES'])
    lang = request.args.get('lang', default = "", type = str)
    if lang:
        if lang in Config.LANGUAGES:
            session['language'] = lang
            return lang
    try:
        language = session['language']
    except KeyError:
        language = None
    if language is not None:
        return language

    lang =  werkzeug.datastructures.LanguageAccept([(al[0][0:2], al[1]) for al in request.accept_languages]).best_match(Config.LANGUAGES)
    if not lang:
        lang = 'en'
    return lang


@app.context_processor
def inject_conf_var():
    lang = get_user_language()
    return dict(
           CURRENT_LANGUAGE = lang,
           lang = lang)

@app.route('/en')
def root_en():
    session['language'] = "en"
    return  redirect("/", code=302)

@app.route('/de')
def root_de():
    session['language'] = "de"
    return  redirect("/", code=302)

@app.route('/fr')
def root_fr():
    session['language'] = "fr"
    return  redirect("/", code=302)

@app.route('/it')
def root_it():
    session['language'] = "it"
    return  redirect("/", code=302)

@app.route('/')
def root():
    start_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
    #start_datetime = datetime.datetime.now().strftime("%d.%m.%Y")
    show_huts_text = _("show only huts")
    return render_template('index.html', date=start_datetime, show_huts_text=show_huts_text)

@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/map')
def map():
    """/map?date=<dd.mm.yyyy|0>&[redirect=<0|1>]&[_show_link=<0|1>]"""
    start_date = request.args.get('date', default = 'now', type = str)
    days_from_start = request.args.get('plus', default = 0, type = int)
    show_link = request.args.get('_show_link', default = 0, type = int)
    _redirect = request.args.get('redirect', default = 0, type = int)
    url_root = request.url_root
    if "127.0.0.1" in url_root or "0.0.0.0" in url_root or "localhost" in url_root:
        url_root="https://huts.wodore.com"
    url_root = url_root.replace("/","%2F").replace("http","https")
    #link = "https://map.geo.admin.ch/?topic=schneesport&lang={lang}&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.bafu.wrz-jagdbanngebiete_select,ch.bafu.wrz-wildruhezonen_portal,ch.swisstopo.hangneigung-ueber_30,ch.swisstopo-karto.schneeschuhrouten,ch.swisstopo-karto.skitouren,ch.bav.haltestellen-oev,ch.swisstopo.swisstlm3d-wanderwege,KML%7C%7Chttps:%2F%2Fhuts.wodore.com%2Fhuts.kml%3Fhas_hrsid%3D0%26date%3D0%26lang%3D{lang},KML%7C%7Chttps:%2F%2Fhuts.wodore.com%2Fhuts.kml%3Fhas_hrsid%3D1%26date%3D{date}%26lang%3D{lang}&layers_visibility=false,false,false,false,false,false,false,true,true&layers_opacity=0.6,0.6,0.3,0.8,0.55,0.7,0.5,0.85,0.9&E=2669094.02&N=1156288.37&zoom=2"
    link = "https://map.geo.admin.ch/?topic=schneesport&lang={lang}&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.bafu.wrz-jagdbanngebiete_select,ch.bafu.wrz-wildruhezonen_portal,ch.swisstopo.hangneigung-ueber_30,ch.swisstopo-karto.schneeschuhrouten,ch.swisstopo-karto.skitouren,ch.bav.haltestellen-oev,ch.swisstopo.swisstlm3d-wanderwege,KML%7C%7C{url_root}%2Fhuts.kml%3Fhas_hrsid%3D0%26date%3D0%26lang%3D{lang},KML%7C%7C{url_root}%2Fhuts.kml%3Fhas_hrsid%3D1%26date%3D{date}%26lang%3D{lang}&layers_visibility=false,false,false,false,false,false,false,true,true&layers_opacity=0.6,0.6,0.3,0.8,0.55,0.7,0.5,0.85,0.9&E=2669094.02&N=1156288.37&zoom=2"
    link_fmt = link.format(days=days_from_start, date=start_date, lang= get_user_language(), url_root=url_root)

    try:
        start_datetime = int(start_date)
    except ValueError:
        pass
    if start_date == 'now':
        start_datetime = datetime.datetime.now()
    else:
        try:
            start_datetime = datetime.datetime.strptime(start_date, "%d.%m.%Y")
        except:
            start_datetime = None
        if start_datetime is None:
            try:
                start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            except:
                start_datetime = None
    if start_datetime:
        formatted_date = (start_datetime).strftime("%d.%m.%Y")
    else:
        formatted_date = "dd.mm.yyyy" # do not get any information
    if show_link:
        return "<a href={link}>{link}</a>".format(link=link_fmt)
    if _redirect:
        return redirect(link_fmt)
    return render_template('map.html', url=link_fmt, date=formatted_date)


# /huts.kml?date=now&plus=5&[has_hrsid=1|0|]
@app.route('/huts.kml')
def huts_kml():
    start_date = request.args.get('date', default = 'now', type = str)
    has_hrsid = request.args.get('has_hrsid', default = "", type = str)
    try:
        start_date = int(start_date)
    except ValueError:
        pass # date string assigned
    if start_date == "":
        start_date = "now"
    days_from_start_date = request.args.get('plus', default = 0, type = int)
    _limit = request.args.get('_limit', default = 2000, type = int)
    download = request.args.get('download', default = 1, type = int)
    huts = Huts(start_date = start_date, days_from_start_date = days_from_start_date,
                show_future_days = 12, limit=_limit, lang=get_user_language())

    kml = huts.generate_kml(has_hrsid = has_hrsid)
    if download:
        return Response(kml.kml(format=False), mimetype='application/vnd.google-earth.kml+xml')
    else:
        return Response(kml.kml(format=True), mimetype='text/xml')

@app.route('/hut/<int:hut_id>')
def hut(hut_id):
    """get detailed hut information"""
    start_date = request.args.get('date', default = 'now', type = str)
    hut = Hut(hut_id, lang=get_user_language(), start_date=start_date)
    hut_desc = HutDescription(hut, add_style=False, add_legend_link=False)
    #return hut.name
    return render_template('hut.html', hut=hut, description=hut_desc.description, date=start_date)

@app.route('/legend')
def legend():
    """/map?date=<dd.mm.yyyy|0>&[redirect=<0|1>]&[_show_link=<0|1>]"""
   # lang = get_user_language()
    #return hut.name
    return render_template('legend.html')



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
