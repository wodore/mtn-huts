# -*- coding: utf-8 -*-
"""
Created on Sun Sep 13 07:10:14 2020

@author: tobias
"""
import requests
import simplekml
 
try:
   from .Hut import Hut
except ImportError:
   from Hut import Hut 

class Huts(object):
    
    HOST_URL = "https://mtn-huts.oa.r.appspot.com"
    
    def __init__(self, start_date='now', days_from_start_date=0, 
                 show_future_days=9, lang='de', 
                 limit=2000, offset=0,
                 _start_hut_id = 1, _stop_hut_id = 380, _async=True,
                 _sleep_time = 1.5):
        
        self._limit = limit
        
        self._start_date = start_date
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
                                days_from_start_date = self._days_from_start_date,
                                show_future_days = self._show_future_days) for hut in huts]
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
  
            
            
            if url:
                desc = "<h4><a href={} target=_blank>{}</a></h4>".format(url, name)
            else:
                desc = "<h4>{}</h4>".format(name)
            desc += "<p>"
            if hut.online_reservation:
                desc += "<a href={} target=_blank>Reservation</a> | ".format(hut.reservation_url)
            desc += "<a href={} target=_blank>SAC</a></p>".format(hut.sac_url)


            
            if hut.online_reservation:
                occupied_list = []
                desc += "<ul style=\"list-style-type:none;\">"
                for over_time in capacity:
                    res_date = over_time['reservation_date']
                    free = over_time['total_free_rooms']
                    total = over_time['total_rooms']
                    oc = over_time['occupied_percent']
                    if over_time['closed']:
                        oc = -1
                    desc += "<li><img src=\"{}\"  width=\"9\" height=\"9\">".format(self.get_occupied_icon(oc, total))
                    desc += " <i>{}:</i> <b>{}</b>/{}</li>".format(res_date, int(free), int(total))
                    occupied_list.append(oc)
                desc += "</ul>"
            else:
                occupied_list = []
                
                
            desc += "<p>{}</p>".format(hut.description)
            desc += "<p><img src=\"{}\" width=250></p>".format(hut.thumbnail)

    #        if occupied > 99:
    #            title += "  FULL"
            pnt = kml.newpoint(coords=[coords]) # lng, lat
            #pnt.description = unicode(desc, 'utf-8')
            pnt.description = desc
            if hut.sac:
                file_name = "hut-sac"
            else:
                file_name = "hut-private"
            if hut.is_biwak:
                file_name = file_name.replace("hut", "biwak")
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
        icon = "{url}/static/pie/{}.png".format(url=self.HOST_URL, oc)
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
