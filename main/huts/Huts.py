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
  
            
            
            #print("{} (LV03: {} | WGS84: {}) - {} free".format(name, hut["coords_lv03"], coords, int(free)))
    
    #        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lng))
            # kml.newpoint(name=name.decode(errors='replace'), coords=[(coords[1], coords[0])])
            #.decode(errors='replace')
            reservation_url = hut.reservation_url #main_url + "?hut_id=" + str(int(hut_id))
            if url:
                desc = "<h4><a href={} target=_blank>{}</a></h4>".format(url, name)
            else:
                desc = "<h4>{}</h4>".format(name)
            if hut.online_reservation:
                desc += "<p><a href={} target=_blank>Reservation</a></p>".format(reservation_url)
            
#             desc += """
#             <!-- SAC TOURENPORTAL START -->
# <script src="https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.1.1/iframeResizer.min.js"></script>
# <iframe src="https://www.sac-cas.ch/{lang}/destinationlistiframe.html?ids={sac_id}" style="width: calc(100% + 60px); border: 0; margin: -30px;" onload="iFrameResize()"></iframe>
# <!-- SAC TOURENPORTAL END -->
# """.format(sac_id=hut.sac_id, lang=self.user_language)


            desc += "<p>{}</p>".format(hut.description)
            
            desc += "<p><img src=\"{}\" width=300></p>".format(hut.thumbnail)
            
            if hut.online_reservation:
                occupied_list = []
                desc += "<ul style=\"list-style-type:none;\">"
                for over_time in capacity:
                    res_date = over_time['reservation_date']
                    free = over_time['total_free_rooms']
                    total = over_time['total_rooms']
                    oc = over_time['occupied_percent']
                    desc += "<li><img src=\"{}\"  width=\"9\" height=\"9\">".format(self.get_occupied_icon(oc, total))
                    desc += " <i>{}:</i> <b>{}</b>/{}</li>".format(res_date, int(free), int(total))
                    occupied_list.append(oc)
                desc += "</ul>"
            else:
                occupied_list = []
                


    #        if occupied > 99:
    #            title += "  FULL"
            pnt = kml.newpoint(coords=[coords]) # lng, lat
            #pnt.description = unicode(desc, 'utf-8')
            pnt.description = desc

            icon = self.get_occupied_days_icon(occupied_list, total_rooms)
            pnt.style.iconstyle.icon.href = icon
            pnt.style.iconstyle.scale = 0.4
        
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


    def get_occupied_icon(self, occupied, total = 1):
        icon = "{url}/static/pie-1.png".format(url=self.HOST_URL)
        if occupied > 45:
            icon = "{url}/static/pie-2.png".format(url=self.HOST_URL)
        if occupied > 70:
            icon = "{url}/static/pie-3.png".format(url=self.HOST_URL)
        if occupied >= 99:
            icon = "{url}/static/pie-4.png".format(url=self.HOST_URL)
        if total == 0:
            icon = "{url}/static/pie-0.png".format(url=self.HOST_URL)
        return icon
    
    def get_occupied_days_icon(self, occupied_list, total = 1):
        if total == 0 or len(occupied_list) < 3:
            icon = "{url}/static/status/0.png".format(url=self.HOST_URL)
            return icon
        first = 1
        if occupied_list[0] > 45:
            first = 2
        if occupied_list[0] > 70:
            first = 3
        if occupied_list[0] >= 99:
            first = 4
        second = 1
        if occupied_list[1] >= 99:
            second = 2
        third = 1
        if occupied_list[2] >= 99:
            third = 2
                
        icon = "{}/static/status/{}{}{}.png".format(self.HOST_URL, first, second, third)    
            
        #icon = "http://frei.wodore.com/static/status/status.svg"
        return icon
    
   

    
if __name__ == '__main__':
    
    huts = Huts(show_future_days = 9, limit = 30)
    
    hut_list = huts.get_huts()
    kml = huts.generate_kml()
    
    kml.save('all_huts.kml')
