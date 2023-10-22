# -*- coding: utf-8 -*-
"""
Created on Sun Sep 13 07:10:14 2020

@author: tobias
"""
import datetime
from typing import Union

import requests
import simplekml
import xmltodict
from rich import print

try:
    from .Hut import Hut
    from .HutDescription import HutDescription
except ImportError:
    from Hut import Hut
    from HutDescription import HutDescription


class Huts(object):
    def __init__(
        self,
        start_date: Union[int, str, None] = "now",
        days_from_start_date=0,
        show_future_days=9,
        lang="de",
        limit: Union[int, None] = 2000,
        offset=0,
        _start_hut_id=1,
        _stop_hut_id=380,
        _async=True,
        _sleep_time=1.5,
    ):
        assert show_future_days > 0, "future days need to be at least 1"
        self._limit = limit if limit else 2000
        self._filter = filter
        if isinstance(start_date, str):
            if start_date == "now":
                start_datetime = datetime.datetime.now()
            else:
                try:
                    start_datetime = datetime.datetime.strptime(start_date, "%d.%m.%Y")
                except ValueError:
                    start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            self._start_date = (start_datetime).strftime("%d.%m.%Y")
        else:
            self._start_date = None  # do not get any information
        # print("Start date: {}".format(self._start_date))
        self._days_from_start_date = days_from_start_date
        self._show_future_days = show_future_days

        self._lang = self._language_check(lang)

        # self._hut_list = {}

    def get_huts(self, limit=None, **kwargs):
        if limit is None:
            limit = self._limit
        # key = "limit{}kwargs{}".format(limit, str(kwargs).replace(" ", ""))
        # if key not in self._hut_list:
        with requests.Session() as s:  # SAC
            url = "https://www.suissealpine.sac-cas.ch/api/1/poi/search"
            params = {
                "lang": self.user_language,
                "order_by": "display_name",
                "type": "hut",
                "disciplines": "",
                "hut_type": "all",
                "limit": limit,
            }

            params.update(kwargs)

            r = s.get(url, params=params)
            # print(r.url)
            huts = r.json().get("results", {})
            r.close()

        if self._start_date:  # only get info from alpsonline if startedate is given
            hrs_start_datetime = datetime.datetime.strptime(self._start_date, "%d.%m.%Y")
            hrs_end_datetime = hrs_start_datetime + datetime.timedelta(days=self._show_future_days - 1)
            hrs_start_datetime_str = (hrs_start_datetime).strftime("%Y-%m-%d")
            hrs_end_datetime_str = (hrs_end_datetime).strftime("%Y-%m-%d")
            with requests.Session() as s:  # alpsonline
                url = "https://www.alpsonline.org/hut-web-service?wsdl"
                post = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:alp="http://www.alpsonline.org/">
    <soapenv:Header/>
    <soapenv:Body>
        <alp:getHutAvailability>
            <arg0>
            <alp:startDate>{start}</alp:startDate>
            <alp:tenant>SAC</alp:tenant>
            <alp:includeOnlyHutsWithContingent>false</alp:includeOnlyHutsWithContingent>
            <alp:numberOfPersons>{persons}</alp:numberOfPersons>
            <alp:endDate>{end}</alp:endDate>
            <alp:detailsIncluded>true</alp:detailsIncluded>
            </arg0>
        </alp:getHutAvailability>
    </soapenv:Body>
</soapenv:Envelope>
    """.format(
                    start=hrs_start_datetime_str,
                    end=hrs_end_datetime_str,
                    persons=1,
                )
                r = s.post(url, data=post)
            alps_res = (
                xmltodict.parse(r.text)
                .get("S:Envelope", {})
                .get("S:Body", {})
                .get("ns2:getHutAvailabilityResponse", {})
                .get("return", {})
                .get("ns2:hutAvailabilityWebResponsePerHutId", [])
            )
            huts_alps_vac = {}
            # print(alps_res)
            for ar in alps_res:
                # huts_vac[o.get("ns2:hutId")] = o.get("ns2:bookingAvailability")
                per_date = {}
                book_avail = ar.get("ns2:bookingAvailability")
                if isinstance(book_avail, dict):
                    per_date[book_avail.get("ns2:date")] = book_avail
                else:
                    for d in ar.get("ns2:bookingAvailability"):
                        per_date[d.get("ns2:date")] = d
                huts_alps_vac[int(ar.get("ns2:hutId"))] = per_date

            for idx, hut in enumerate(huts):
                if hut.get("hrs_id") in huts_alps_vac:
                    # print("ID: {}, HRS_ID: {}".format(hut.get("id"), hut.get("hrs_id")))
                    orig = huts_alps_vac[hut.get("hrs_id")]
                    if orig is None:
                        orig = {}
                    huts[idx]["hrs_original"] = orig

        # hut_list = list(map(Hut.create, huts))
        hut_list = [
            Hut(hut, start_date=self._start_date, show_future_days=self._show_future_days, lang=self.user_language)
            for hut in huts
        ]
        # self._hut_list[key] = hut_list

        return hut_list
        # return self._hut_list[key]
        # df = pd.json_normalize(huts)

    def generate_kml(self, **filter):
        all_huts = self.get_huts(**filter)
        # main_url = self.MAIN_URL + '/calendar'
        kml = simplekml.Kml()
        hut_name = {"de": "Berghütten", "it": "Capanne di Montagna", "fr": "Cabanes de Montagne", "en": "Mountain Huts"}
        if self._start_date:
            kml.document.name = "{} {}".format(hut_name[self.user_language], self._start_date)
            icon_scale = 0.46
        else:
            kml.document.name = "{}".format(hut_name[self.user_language])
            icon_scale = 0.33
        if filter.get("has_hrsid", "").lower() in ["0", 0, "false", "f", "none"]:
            icon_scale = 0.42

        # generate GPX file
        # print("Generate KML file.")
        # for index, hut in df_huts.iterrows():
        for hut in all_huts:
            coords = hut.get_coordinates(system="wsg84", include_altitude=True)

            hut_desc = HutDescription(hut, add_style=True)
            if __name__ == "__main__":
                print("#{} - {}".format(hut.sac_id, hut.name))
            pnt = kml.newpoint(coords=[coords])  # lng, lat
            pnt.description = hut_desc.description
            pnt.style.iconstyle.icon.href = hut_desc.icon_days
            pnt.style.iconstyle.scale = icon_scale

        return kml
        # kml.save('free_huts.kml')

    @property
    def user_language(self):
        """Returns language used by user (not hut)"""
        return self._lang

    def _language_check(self, lang):
        if lang.lower() not in ["de", "fr", "it", "en"]:
            raise ValueError("Language '{}' not supported. Use either 'de', 'fr', 'it' or 'en'.".format(lang))
        return lang.lower()


if __name__ == "__main__":
    #     url = "https://www.alpsonline.org/hut-web-service?wsdl"
    #     post = """
    # <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:alp="http://www.alpsonline.org/">
    #    <soapenv:Header/>
    #    <soapenv:Body>
    #       <alp:getHutAvailability>
    #          <arg0>
    #             <alp:startDate>2023-02-17</alp:startDate>
    #             <alp:tenant>SAC</alp:tenant>
    #             <alp:includeOnlyHutsWithContingent>false</alp:includeOnlyHutsWithContingent>
    #             <alp:numberOfPersons>1</alp:numberOfPersons>
    #          	<alp:endDate>2023-02-23</alp:endDate>
    #          	<alp:detailsIncluded>true</alp:detailsIncluded>
    #          </arg0>
    #       </alp:getHutAvailability>
    #    </soapenv:Body>
    # </soapenv:Envelope>
    #     """
    #     import xmltodict

    #     with requests.Session() as s:
    #         r = s.post(url, data=post)
    #     out = xmltodict.parse(r.text).get("S:Envelope", {}).get("S:Body", {}).get("ns2:getHutAvailabilityResponse", {}).get("return", {}).get("ns2:hutAvailabilityWebResponsePerHutId", [])
    #     huts_vac = {}
    #     for o in out:
    #         #huts_vac[o.get("ns2:hutId")] = o.get("ns2:bookingAvailability")
    #         per_date = {}
    #         for d in o.get("ns2:bookingAvailability"):
    #             per_date[d.get("ns2:date")] = d
    #         huts_vac[o.get("ns2:hutId")] = per_date

    huts = Huts("20.10.2023", show_future_days=2, limit=None)

    hut_list = huts.get_huts()

    HUT_IDX = 19
    hut = hut_list[HUT_IDX]
    print(hut)
    capacity = hut_list[HUT_IDX].get_capacity()
    hrs_original = hut_list[HUT_IDX]._hut_dict.get("hrs_original")
    hrs_id = hut_list[HUT_IDX]._hut_dict.get("hrs_id")
    # print(hrs_id)
    # print(hrs_original)
    # for i, h in enumerate(hut_list):
    # print("{}: ".format(i), end="")
    # print(h)
    # print("---")
    # print("Hut index {} booking: ".format(i), end="")
    # if h.get_capacity():
    #     print(str(h.get_capacity()[0].get("booking_enabled")).upper())
    # else:
    #     print("-")
    # print(capacity)
    #
    # kml = huts.generate_kml(limit=None)

    # kml.save("all_huts.kml")

    # # try filters
    # print([h.name for h in huts.get_huts(limit=3, has_hrsid = True)])
    # print([h.name for h in huts.get_huts(limit=3, has_hrsid = False)])
    # print([h.name for h in huts.get_huts(limit=3)])
