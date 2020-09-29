# -*- coding: utf-8 -*-
"""
Created on Sun Sep 13 07:10:14 2020

@author: tobias
"""
# import requests
# import time
import datetime
import locale
# import threading
# from concurrent.futures import Future

# try:
#     from .GPSConverter import GPSConverter
# except ImportError: # for local testing
#     from GPSConverter import GPSConverter


STYLE = """
<style>

  .hut-info a:link, .hut-info a:visited {
    text-decoration: none;
    color: #31708f;
  }

  .hut-info a:hover {
    text-decoration: underline;
    color: #31708f;
  }


  #hut-icon-title {
    width: 30px;
  }
  .img-text {
    vertical-align: text-bottom;
  }

  .header-links {
    font-weight: 400;
    font-size: 11pt;
  }
  .hut-date-list {
    width: 100%;
    white-space: nowrap;
    overflow: auto;
    margin-left:1px;
    padding:2px;
  }
  .hut-date-list::-webkit-scrollbar {
      height: 6px;
    }

    .hut-date-list::-webkit-scrollbar-track {
      background: #ddd;
    }

    .hut-date-list::-webkit-scrollbar-thumb {
      background: #aaa;
    }
  .hut-date-element {
    border-radius: 20px;
    border: 1px solid #cccccc;
    /* background: #ddd; */
    padding: 1px  !important;
    margin: 0px;
    margin-bottom: 8px;
    margin-top: 3px;
    width: 118px;
  }

    .hut-date-element div {
        display: inline-block;
        vertical-align: middle;
    }
    .hut-date-element .icon {
        border: 0px solid red;
        width:21px;
    }
    .hut-date-element .icon img {
        height:20px;
    }
    .hut-date-element .date {
        width:37px;
        /* height:30px; */
        border: 0px solid red;
        line-height: 85%;
    }
    .hut-date-element .free {
        width:35px;
        /*height:30px; */
        border: 0px solid green;
        border-left: 2px solid #ccc;
        padding-left: 5px;
    }

  figure figcaption {
    padding: 0.5rem;
  }
  figure {
      /* padding: 1rem!important; */
    margin-bottom: 2rem!important;
    padding : 0;
    box-shadow: 0 .125rem .25rem rgba(0,0,0,.075)!important;
    border: 1px solid #ddd;
  }


</style>
"""

class HutDescription(object):


    def __init__(self, hut, host=None, add_style=True):
        if host is None:
            self.HOST_URL = "https://mtn-huts.oa.r.appspot.com"
        else:
            self.HOST_URL = host
        self._hut = hut
        self._add_style = True
        self._desc = self._generate()



    @property
    def description(self):
        return self._desc

    @property
    def icon(self):
        return self._icon

    @property
    def icon_days(self):
        return self._icon_days

    def _generate(self):
        """Generate hut description."""
        hut = self._hut
        capacity_list = hut.get_capacity()
        if capacity_list:
            free = capacity_list[0]['total_free_rooms']
            total_rooms = capacity_list[0]['total_rooms']
            occupied = capacity_list[0]['occupied_percent']
        else:
            free = 0
            total_rooms =0
            occupied = -1

        # start description variable
        if self._add_style:
            desc = STYLE
        else:
            desc = ""

        if hut.sac:
            file_name = "hut-sac"
        else:
            file_name = "hut-private"
        if hut.is_biwak:
            file_name = file_name.replace("hut", "biwak")

        if hut.url:
            url = hut.url

        else:
            url = hut.sac_url

        desc += """<div class="hut-info"><h4>
            <img id="hut-icon-title" class="img-text" src="{}/static/icons/default/{}.png">
            <a href={} target=_blank>{}</a>
            <small>{}</small></h4>""".format(self.HOST_URL, file_name, url, hut.name, hut.owner)

        desc += '<p  class="header-links">'

        # get correct translation
        if hut.online_reservation:
            res_text = "Online reservation"
            if hut.user_language == "de":
                res_text = "Online Reservierung"
            elif hut.user_language == "fr":
                res_text = "Réservation en ligne"
            elif hut.user_language == "it":
                res_text = "Prenotazione online"
            desc += """<img class="img-text" src="{}/static/icons/calendar.png" height="15px"> <a href={} target=_blank>{}</a> | """.format(self.HOST_URL, hut.reservation_url, res_text)

        sac_portal_text = "SAC route portal"
        if hut.user_language == "de":
            sac_portal_text = "SAC Tourenportal"
        elif hut.user_language == "fr":
            sac_portal_text = "Portail des courses du CAS"
        elif hut.user_language == "it":
            sac_portal_text = "Portale escursionistico del CAS"
        desc += """<img src="{}/static/external/sac.ico" height="17px" class="img-text"> <a href={} target=_blank>{}</a></p>""".format(self.HOST_URL, hut.sac_url, sac_portal_text)

        # get capacity icons if online reservation is possible
        if hut.online_reservation and capacity_list:
            percent_list = []
            desc += '<ul class="list-inline list-unstyled hut-date-list">'
            for capacity in capacity_list:
                res_date = datetime.datetime.strptime(capacity['reservation_date'], "%d.%m.%Y") # convert from string
                free = capacity['total_free_rooms']
                total = capacity['total_rooms']
                percent = capacity['occupied_percent']
                if capacity['closed']:
                    percent = -1

                # use correct translation
                if hut.user_language == "de":
                    user_loc = "de_DE.UTF8"
                if hut.user_language == "it":
                    user_loc = "it_IT.UTF8"
                if hut.user_language == "fr":
                    user_loc = "fr_FR.UTF8"
                if hut.user_language == "en":
                    user_loc = "en_GB.UTF8"
                try:
                    locale.setlocale(locale.LC_TIME, user_loc)
                except: # default english
                    locale.setlocale(locale.LC_TIME, "en_GB.UTF8")

                date_fmt = res_date.strftime("%d.%m.%y")
                day_short = res_date.strftime("%a")

                desc += """
                <li class="hut-date-element">
                  <div class="icon">
            		    <img src="{icon}">
                  </div>
                  <div class="date">
                    <b>{day}</b><br>
                    <small  class="text-muted">{date}</small>
                  </div>
                  <div class="free">
                    <strong style="font-size: 13px;">{free}</strong><small class="text-muted">/{total}</small>
                  </div>
               </li>
               """.format(icon=self.get_occupied_icon(percent),
                          day = day_short,
                          date=date_fmt,
                          free=int(free),
                          total=int(total))

                percent_list.append(percent)
            desc += "</ul>"
        else:
            percent_list = []

        self.get_occupied_days_icon(percent_list, name = file_name)

        desc += "<p>{}</p>".format(hut.description)
        if hut.photo:
            desc += """
            <figure class="figure" style="width:300px;">
              <img src="{}" class="figure-img img-fluid z-depth-1" alt="..." style="width: 100%">
              <figcaption class="figure-caption text-right text-muted">{} (&copy; {})</figcaption>
            </figure>
                """.format(hut.photo["M"], hut.photo["caption"], hut.photo["copyright"])

        desc += "</div>"

        return desc


    def round_percent(self, p):
        if p >= 99:
             percent = 100
        elif p >= 60:
             percent = 75
        elif p >= 30:
             percent = 50
        elif p >= 0:
             percent = 25
        else:
            percent = -1
        return percent


    def get_occupied_icon(self, percent):
        percent_rounded = self.round_percent(percent)
        icon = "{url}/static/icons/pie/{p}.png".format(url=self.HOST_URL, p=percent_rounded)

        return icon


    def get_occupied_days_icon(self, percent_list, name = "hut-sac"):
        self._icon = "{url}/static/icons/default/{name}.png".format(url=self.HOST_URL, name=name)
        if len(percent_list) < 3:
            icon = self._icon
        else:
            o0 = self.round_percent(percent_list[0])
            o1 = self.round_percent(percent_list[1])
            o2 = self.round_percent(percent_list[2])
            o3 = self.round_percent(percent_list[3])
            icon = "{}/static/icons/generated/{}-{}-{}-{}-{}.png".format(self.HOST_URL, name, o0, o1, o2, o3)
        self._icon_days = icon

        return icon


if __name__ == '__main__':
    from Hut import Hut
    import requests
    import os
    s = requests.Session()

    LANG = "de"
    HUT_INDEX = 30
    # 0: biwak
    # 1: SAC, no online reservation
    # 2: Almagellerhütte SAC, massenlager, online reservation
    # 3: private, no online reservation
    # 11:biwak, no reservation
    # 30: Berglihütte SAC, biwak  with reservation
    # 35: Binntalhütte SAC, online reservation, different rooms
    url = "https://www.suissealpine.sac-cas.ch/api/1/poi/search"
    params = {'lang': "de",
              "order_by" : "display_name",
              "type" : "hut",
              "disciplines" : "",
              "hut_type" : "all",
              "limit" : HUT_INDEX + 2}

    r = s.get(url, params=params)
    huts = r.json().get("results", {})
    #df = pd.json_normalize(huts)




    hut = Hut.create(huts[HUT_INDEX], lang=LANG)

    hut_desc = HutDescription(hut, "../main")

    desc = hut_desc.description

    TEMPLATE = """
    <!DOCTYPE html><html><head>
<link rel="stylesheet" href="https://map.geo.admin.ch/97abc53/style/app.css">
</head><body>
<div class="ga-tooltip ga-popup-mobile-bottom ng-scope ng-isolate-scope popover ga-draggable" style="position: absolute; left: 20px; top: 40px; transform: translate3d(0px, 0px, 0px); display: block; z-index: 2502;">
  <div id="KML||https://mtn-huts.oa.r.appspot.com/huts.kml?date=2020-09-27&amp;plus=0#1083" class="htmlpopup-container">
    <div class="htmlpopup-header"><span>Hut Vacancy 27.09.2020 &nbsp;</span></div><div class="htmlpopup-content">
      <!-- START CUSTOM CONTENT -->
      {DESC}
      <!-- END CUSTOM CONTENT -->
    </div></div></div>
<!-- ngIf: html.showVectorInfos --><div ng-if="html.showVectorInfos" class="ga-vector-tools ng-scope"><div ga-measure="html.feature" ga-coordinate-precision="3" class="ng-isolate-scope"><!-- ngIf: coord --><div ng-if="coord" class="ga-coord ng-binding ng-scope"><i class="fa fa-ga-marker"></i> 2'695'500.036, 1'198'999.442, 0.0 </div><!-- end ngIf: coord --><!-- ngIf: distance && !surface --><!-- ngIf: surface --><!--p class="pull-right">{{azimuth | measure:'angle':['&deg']}}</p--> </div><!-- ngIf: html.showProfile --><div ng-if="html.showProfile" ga-profile-bt="html.feature" class="ng-scope ng-isolate-scope"><!-- ngIf: feature && isValid(feature) --> </div><!-- end ngIf: html.showProfile --></div><!-- end ngIf: html.showVectorInfos --><div class="ga-tooltip-separator ng-hide" ng-show="!$last"></div></div><!-- end ngRepeat: html in options.htmls track by $index --></div></div>
</body>
"""
    rendered = TEMPLATE.format(DESC=desc)
    output = '../../tmp/hut-description.html'
    with open(output,'w') as f:
        f.write(rendered)
        f.close()
        print("File written to '{}'".format(os.path.abspath(output)))
