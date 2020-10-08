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
   from .HutDescription import HutDescription
except ImportError:
   from Hut import Hut
   from HutDescription import HutDescription




class Huts(object):


    def __init__(self, start_date='now', days_from_start_date=0,
                 show_future_days=9, lang='de',
                 limit=2000, offset=0,
                 _start_hut_id = 1, _stop_hut_id = 380, _async=True,
                 _sleep_time = 1.5):

        self._limit = limit
        self._filter = filter
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

        self._hut_list = {}

    def get_huts(self, limit = None, **kwargs):
        if limit is None:
            limit = self._limit
        key = "limit{}kwargs{}".format(limit, str(kwargs).replace(" ",""))
        if key not in self._hut_list:
            with requests.Session() as s:
                url = "https://www.suissealpine.sac-cas.ch/api/1/poi/search"
                params = {'lang': self.user_language,
                          "order_by" : "display_name",
                          "type" : "hut",
                          "disciplines" : "",
                          "hut_type" : "all",
                          "limit" : limit}

                params.update(kwargs)

                r = s.get(url, params=params)
                huts = r.json().get("results", {})
                r.close()

                #hut_list = list(map(Hut.create, huts))
                hut_list = [Hut(hut, start_date = self._start_date,
                                show_future_days = self._show_future_days,
                                lang = self.user_language) for hut in huts]
                self._hut_list[key] = hut_list

        return  self._hut_list[key]
        #df = pd.json_normalize(huts)

    def generate_kml(self, **filter):
        all_huts = self.get_huts(**filter)
        #main_url = self.MAIN_URL + '/calendar'
        kml=simplekml.Kml()
        hut_name = {"de": "Berghütten",
                    "it" : "Capanne di Montagna",
                    "fr" : "Cabanes de Montagne",
                    "en" : "Mountain Huts"}
        if self._start_date:
            kml.document.name = "{} {}".format(hut_name[self.user_language], self._start_date)
            icon_scale = 0.46
        else:
            kml.document.name = "{}".format(hut_name[self.user_language])
            icon_scale = 0.33
        if filter.get("has_hrsid", "") in ["0", 0, "false", "False", "f", "F"]:
            icon_scale = 0.42

        # generate GPX file
        #print("Generate KML file.")
        #for index, hut in df_huts.iterrows():
        for hut in all_huts:
            coords = hut.get_coordinates(system="wsg84",  include_altitude=True)

            hut_desc = HutDescription(hut, add_style=True)
            if __name__ == '__main__':
                print("#{} - {}".format(hut.sac_id, hut.name))
            pnt = kml.newpoint(coords=[coords]) # lng, lat
            pnt.description = hut_desc.description
            pnt.style.iconstyle.icon.href = hut_desc.icon_days
            pnt.style.iconstyle.scale = icon_scale

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




if __name__ == '__main__':

    huts = Huts(0, show_future_days = 9, limit = 30)

    hut_list = huts.get_huts()
    kml = huts.generate_kml(limit=3, has_hrsid = True)

    kml.save('all_huts.kml')

    # try filters
    print([h.name for h in huts.get_huts(limit=3, has_hrsid = True)])
    print([h.name for h in huts.get_huts(limit=3, has_hrsid = False)])
    print([h.name for h in huts.get_huts(limit=3)])
