# -*- coding: utf-8 -*-
"""
Created on Sun Sep 13 07:10:14 2020

@author: tobias
"""
import requests
import simplekml
import time
import datetime

try:
   from .Hut import Hut
except ImportError:
   from Hut import Hut


STYLE = """
<style>
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
    margin-bottom: 10px;
    margin-top: 5px;
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

class Huts(object):

    HOST_URL = "https://mtn-huts.oa.r.appspot.com"

    def __init__(self, start_date='now', days_from_start_date=0,
                 show_future_days=9, lang='de',
                 limit=2000, offset=0,
                 _start_hut_id = 1, _stop_hut_id = 380, _async=True,
                 _sleep_time = 1.5):

        self._limit = limit
        if start_date:
            if start_date == 'now':
                start_datetime = datetime.datetime.now()
            else:
                try:
                    start_datetime = datetime.datetime.strptime(start_date, "%d.%m.%Y")
                except ValueError:
                    start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            self._start_date = (start_datetime).strftime("%d.%m.%Y")
        else:
            self._start_date = None # do not get any information

        self._days_from_start_date = days_from_start_date
        self._show_future_days = show_future_days

        self._lang = self._language_check(lang)

        self._hut_list = False

    def get_huts(self, limit=None):
        if limit is None:
            limit = self._limit
        if not self._hut_list:
            with requests.Session() as s:
                url = "https://www.suissealpine.sac-cas.ch/api/1/poi/search"
                params = {'lang': self.user_language,
                          "order_by" : "display_name",
                          "type" : "hut",
                          "disciplines" : "",
                          "hut_type" : "all",
                          "limit" : limit}

                r = s.get(url, params=params)
                huts = r.json().get("results", {})
                r.close()

                #hut_list = list(map(Hut.create, huts))
                hut_list = [Hut(hut, start_date = self._start_date,
                                show_future_days = self._show_future_days,
                                lang = self.user_language) for hut in huts]
                self._hut_list = hut_list

        return  self._hut_list
        #df = pd.json_normalize(huts)

    def generate_kml(self):
        #df_huts = self.get_vacancies(1, self.MAX_HUTS, self.START_DATE, self.EXCLUDE_IDS, self.MAX_DAYS)

        #main_url = self.MAIN_URL + '/calendar'
        kml=simplekml.Kml()
        kml.document.name = "Hut Vacancy {}".format(self._start_date)

        # generate GPX file
        print("Generate KML file.")
        #for index, hut in df_huts.iterrows():
        for hut in self.get_huts():
            coords = hut.get_coordinates(system="wsg84")
            capacity = hut.get_capacity()
            name = hut["name"]
            print("#{} - {}".format(hut.sac_id, hut.name))
            if capacity:
                free = capacity[0]['total_free_rooms']
                total_rooms = capacity[0]['total_rooms']
                occupied = capacity[0]['occupied_percent']
            else:
                free = 0 #hut['total_free_rooms']
                total_rooms =0# hut['total_rooms']
                occupied = 0#hut['occupied_percent']
            url = hut['url']

            desc = STYLE

            if hut.sac:
                file_name = "hut-sac"
            else:
                file_name = "hut-private"
            if hut.is_biwak:
                file_name = file_name.replace("hut", "biwak")

            if url:
                desc += """<h4>
                <img id="hut-icon-title" class="img-text" src="https://mtn-huts.oa.r.appspot.com/static/icons/default/{}.png">
                <a href={} target=_blank>{}</a>
                <small>{}</small></h4>""".format(file_name, url, name, hut.owner)
            else:
                desc += """"<h4>
                <img id="hut-icon-title" class="img-text" src="https://mtn-huts.oa.r.appspot.com/static/icons/default/{}.png">
                {}
                <small>{}</small></h4>""".format(file_name, name, hut.owner)
            desc += '<p  class="header-links">'
            if hut.online_reservation:
                res_text = "Online reservation"
                if self.user_language == "de":
                    res_text = "Online Reservierung"
                elif self.user_language == "fr":
                    res_text = "Réservation en ligne"
                elif self.user_language == "it":
                    res_text = "Prenotazione online"
                desc += """<img class="img-text" src="https://api3.geo.admin.ch/1600183218/static/images/ico_extern.gif"> <a href={} target=_blank>{}</a> | """.format(hut.reservation_url, res_text)
            sac_protal_text = "SAC route portal"
            if self.user_language == "de":
                sac_protal_text = "SAC Tourenportal"
            elif self.user_language == "fr":
                sac_protal_text = "Portail des courses du CAS"
            elif self.user_language == "it":
                sac_protal_text = "Portale escursionistico del CAS"
            desc += """<img src="https://www.sac-cas.ch/typo3conf/ext/usersaccassite/Resources/Public/Icons/favicon.ico" height="15px" class="img-text"> <a href={} target=_blank>{}</a></p>""".format(hut.sac_url, sac_protal_text)


            if hut.online_reservation:
                occupied_list = []
                desc += '<ul class="list-inline list-unstyled hut-date-list">'
                for over_time in capacity:
                    res_date = over_time['reservation_date']
                    free = over_time['total_free_rooms']
                    total = over_time['total_rooms']
                    oc = over_time['occupied_percent']
                    if over_time['closed']:
                        oc = -1
                    # desc += "<li><img src=\"{}\"  width=\"10\" height=\"10\">".format(self.get_occupied_icon(oc, total))
                    # desc += " <i>{}:</i> <b>{}</b>/{}</li>".format(res_date, int(free), int(total))

                    # convert date
                    res_date = datetime.datetime.strptime(res_date, "%d.%m.%Y")
                    import locale
                    # for German locale
                    if self.user_language == "de":
                        user_loc = "de_DE.UTF8"
                    if self.user_language == "it":
                        user_loc = "it_IT.UTF8"
                    if self.user_language == "fr":
                        user_loc = "fr_FR.UTF8"
                    if self.user_language == "en":
                        user_loc = "en_GB.UTF8"
                    try:
                        locale.setlocale(locale.LC_TIME, user_loc)
                    except:
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
                   """.format(icon=self.get_occupied_icon(oc, total),
                              day = day_short,
                              date=date_fmt,
                              free=int(free),
                              total=int(total))
                    occupied_list.append(oc)
                desc += "</ul>"
            else:
                occupied_list = []


            desc += "<p>{}</p>".format(hut.description)
            if hut.photo:
                desc += """
                            <figure class="figure" style="width:300px;">
          <img src="{}"
                class="figure-img img-fluid z-depth-1" alt="..." style="width: 100%">
              <figcaption class="figure-caption text-right text-muted">{} (&copy; {})</figcaption>
            </figure>
            """.format(hut.photo["M"], hut.photo["caption"], hut.photo["copyright"])


    #        if occupied > 99:
    #            title += "  FULL"
            pnt = kml.newpoint(coords=[coords]) # lng, lat
            #pnt.description = unicode(desc, 'utf-8')
            pnt.description = desc

            icon = self.get_occupied_days_icon(occupied_list, file_name)
            pnt.style.iconstyle.icon.href = icon
            pnt.style.iconstyle.scale = 0.5

        return kml
        #kml.save('free_huts.kml')


    @property
    def user_language(self):
        """Returns language used by user (not hut)"""
        return self._lang

    def _language_check(self, lang):
         if lang.lower() not in ['de', 'fr', 'it', 'en']:
            raise ValueError("Language '{}' not supported. Use either 'de', 'fr', 'it' or 'en'.".format(lang))
         return lang.lower()

    def round_oc(self, v):
        if v >= 99:
             oc = 100
        elif v >= 60:
             oc = 75
        elif v >= 30:
             oc = 50
        elif v >= 0:
             oc = 25
        else:
            oc = -1
        return oc

    def get_occupied_icon(self, occupied, total = 1):
        if total == 0:
            occupied = -1
        oc = self.round_oc(occupied)
        icon = "{url}/static/icons/pie/{o}.png".format(url=self.HOST_URL, o=oc)
        return icon

    def get_occupied_days_icon(self, occupied_list, name = "hut-sac"):

        if len(occupied_list) < 3:
            icon = "{url}/static/icons/default/{name}.png".format(url=self.HOST_URL, name=name)
        # elif occupied_list[0] >= 99:
        #      icon = "{url}/static/icons/hut-sac-full.png".format(url=self.HOST_URL)
        # elif occupied_list[0] >= 0:
        #     icon = "{url}/static/icons/hut-sac-free.png".format(url=self.HOST_URL)
        else:
            o0 = self.round_oc(occupied_list[0])
            o1 = self.round_oc(occupied_list[1])
            o2 = self.round_oc(occupied_list[2])
            o3 = self.round_oc(occupied_list[3])
            icon = "{}/static/icons/generated/{}-{}-{}-{}-{}.png".format(self.HOST_URL, name, o0, o1, o2, o3)

        return icon




if __name__ == '__main__':

    huts = Huts(show_future_days = 9, limit = 30)

    hut_list = huts.get_huts()
    kml = huts.generate_kml()

    kml.save('all_huts.kml')
