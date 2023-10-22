# -*- coding: utf-8 -*-
"""
Created on Sun Sep 13 07:10:14 2020

@author: tobias
"""
import datetime
import threading
import time
from concurrent.futures import Future
from concurrent.futures._base import TimeoutError as futureTimeoutError
from typing import Union

import requests
from rich import print

try:
    from .GPSConverter import GPSConverter

    # from .HutDescription import HutDescription
except ImportError:  # for local testing
    from GPSConverter import GPSConverter

    # from HutDescription import HutDescription


class Hut(object):
    HRS_URL = "https://www.alpsonline.org/reservation"
    ONLINE_RESERVATION_URL = HRS_URL + "/calendar?hut_id={id}&lang={lang}"

    SAC_ROUTE_PORTAL_URL = {
        "de": "https://www.sac-cas.ch/de/huetten-und-touren/sac-tourenportal/{id}",
        "fr": "https://www.sac-cas.ch/fr/cabanes-et-courses/portail-des-courses-du-cas/{id}",
        "it": "https://www.sac-cas.ch/it/capanne-e-escursioni/portale-escursionistico-del-cas/{id}",
        "en": "https://www.sac-cas.ch/en/huts-and-tours/sac-route-portal/{id}",
    }

    def __init__(
        self, hut_dict_or_id, start_date: Union[str, int, None] = "now", show_future_days=9, lang="de", _async=False
    ):
        self._hut_dict = {}
        self._lang = self._language_check(lang)
        try:
            _id = int(hut_dict_or_id)
            with requests.Session() as s:
                url = "https://www.suissealpine.sac-cas.ch/api/1/poi/search"
                params = {"lang": self.user_language, "id": _id}

                r = s.get(url, params=params)
                huts = r.json().get("results", {})
                r.close()

                if len(huts) > 0:
                    self._hut_dict = huts[0]
        except TypeError:
            self._hut_dict = hut_dict_or_id

        self._show_future_days = show_future_days

        self._async = _async

        if start_date:
            if start_date == "now":
                start_datetime = datetime.datetime.now()
            else:
                try:
                    start_datetime = datetime.datetime.strptime(start_date, "%d.%m.%Y")  # type: ignore
                except ValueError:
                    start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")  # type: ignore
            self._start_date = (start_datetime).strftime("%d.%m.%Y")
        else:
            self._start_date = None  # do not get any information

        self._capacity_loading_p = False
        # if self._async:
        #    self.load_capacity_async()

    @classmethod
    def create(cls, hut_dict_or_id, lang="de"):
        return cls(hut_dict_or_id, lang=lang)

    @property
    def start_date(self):
        """Returns start date from reservation requests"""
        return self._start_date

    @property
    def show_future_days(self):
        """Number of future days to so (occupation)"""
        return self._show_future_days

    @property
    def user_language(self):
        """Returns language used by user (not hut)"""
        return self._lang

    @property
    def sac_id(self):
        """SAC tour id"""
        return int(self._hut_dict.get("id", -1))

    @property
    def hrs_id(self):
        """HRS id (reservation system.

        https://www.alpsonline.org/reservation/calendar?hut_id=ID.
        """
        try:
            return int(self._hut_dict.get("hrs_id", 0))
        except TypeError:
            return 0

    @property
    def name(self):
        """Returns hut name"""
        return self.get_field_by_lang("display_name", "Unknown Name")

    @property
    def description(self):
        """Returns hut description"""
        return self.get_field_by_lang("description", "")

    @property
    def opentext(self):
        """Returns hut opentext"""
        return self.get_field_by_lang("opentext", "")

    @property
    def comment(self):
        """Returns hut general comment"""
        return self.get_field_by_lang("hut_comment", "")

    @property
    def owner(self):
        """Returns hut owner"""
        owner = self._hut_dict.get("owner", "")
        if not owner:
            owner = ""
        return owner

    @property
    def sac(self):
        """Is it an SAC hut"""
        return not self._hut_dict.get("is_private", True)

    @property
    def is_biwak(self):
        """If catering is offered it is no biwak"""
        # check special case sleeps < emergency shelters:
        if self.sleeps < self.emergency_shelter:
            return True
        # check if catering is offered at least in two months
        return not ((self.catering.count(0) + self.catering.count(1)) >= 2)
        # return self.sleeps <= self.emergency_shelter

    @property
    def category(self):
        """Category name:

        - biwak-sac
        - biwak-private
        - hut-sac
        - hut-private
        """
        cat = "biwak" if self.is_biwak else "hut"
        cat += "-sac" if self.sac else "-private"
        return cat

    @property
    def language(self):
        """Returns hut main language"""
        return self._hut_dict.get("main_lang", "de")

    @property
    def catering(self):
        """Returns a catering list (idx0: january, 11: december)

        0: fully catered
        1: sometimes
        2: no catering
        """
        catering = list(self._hut_dict.get("catering", []).values())
        return catering

    @property
    def opening(self):
        """Returns a catering list (idx0: january, 11: december)

        0: open
        1: sometimes
        2: closed
        """
        opening = list(self._hut_dict.get("opening", []).values())
        return opening

    @property
    def altitude(self):
        """Returns hut altitude in meter above sea level"""
        return int(self._hut_dict.get("altitude", 0))

    @property
    def email(self):
        """Returns hut information email address"""
        return self._hut_dict.get("email", "")

    @property
    def url(self):
        """Returns hut url"""
        return self._hut_dict.get("url", "")

    @property
    def capacity(self):
        """Returns hut information email address"""
        return {"emergency": self.emergency_shelter, "sleeps": self.sleeps}

    @property
    def emergency_shelter(self):
        """Returns number of emergency shelter beds (Schutzraum)"""
        return int(self._hut_dict.get("emergency_shelter", 0))

    @property
    def sleeps(self):
        """Returns number of beds (Schlafplaetze)"""
        return int(self._hut_dict.get("sleeps", 0))

    @property
    def photos(self):
        """Returns all photos as a list of dictionaries. See `get_photos()`"""
        return [self.get_photo(i) for i in range(0, self.photos_count)]

    @property
    def photo(self):
        """Returns first photo. See `get_photos()`"""
        if self.photos_count > 0:
            return self.get_photo(0)
        else:
            return {}

    @property
    def thumbnail(self):
        """Returns thumbnail url"""
        return self.photo.get("M")

    @property
    def photos_count(self):
        """Returns number of available photos"""
        return len(self._hut_dict.get("photos", []))

    @property
    def online_reservation(self):
        """Is online reservation possible?"""
        return self.hrs_id > 0

    @property
    def reservation_url(self):
        """Online reservation link"""
        lang = self.user_language
        if lang == "de":
            lang = "de_CH"
        if self.online_reservation:
            return self.ONLINE_RESERVATION_URL.format(id=self.hrs_id, lang=lang)
        else:
            return ""

    @property
    def sac_url(self):
        """SAC route portal link"""
        return self.SAC_ROUTE_PORTAL_URL[self.user_language].format(id=self.sac_id)

    def get_coordinates(self, system="wsg84", include_altitude=False):
        """
        Returns coordinates wither as WSG84, LV03 or LV95 (newest).
        More information:
            https://en.wikipedia.org/wiki/Swiss_coordinate_system

        Parameters
        ----------
        system : str, optional
            Coordinateion system. Allowed values are 'wsg84', 'lv03', or 'lv95'.
            The default is "wsg84".
        include_altitude : bool, optional
            Return altitude as third element. The default is False.

        Returns
        -------
        list
            List with two coordinates (A, B)
            A: Longitude (WSG84) or east coordinate.
            B: Latitue (WSG84) or north coordinate.
            If `include_altitude` is True a third element with the altitude is
            added (A,B, H)
            H: Altitude
        """
        system = system.lower()
        if system not in ["wsg84", "lv03", "lv95"]:
            raise ValueError("Coordinate system '{}' is not supported.".format(system))
        (east, north) = self._hut_dict.get("geom", {}).get(
            "coordinates",
            [0.0, 0.0],
        )

        if system in ["wsg84", "lv03"]:
            if east > 2000000:
                east -= 2000000
            if north > 1000000:
                north -= 1000000

        H = self.altitude
        if system == "wsg84":
            converter = GPSConverter()
            (lat, lng, H) = converter.LV03toWGS84(east, north, self.altitude)
            out = (lng, lat)
        else:
            out = (east, north)
        if include_altitude:
            out += (H,)
        return out

    def get_photo(self, index=0):
        """Returns photo dicitonary based on the index.

        Output format:

            {
                'caption'   : 'Photo caption.',
                 'season'   : 'summer|winter|both|...',
                 'copyright': 'Name',
                 'photo'    : 'https://static.suissealpine.sac-cas.ch/nameL.jpg',
                 'S'        : 'https://static.suissealpine.sac-cas.ch/nameS.jpg',
                 'M'        : 'https://static.suissealpine.sac-cas.ch/name7Mb.jpg',
                 'L'        : 'https://static.suissealpine.sac-cas.ch/nameL.jpg',
                 'XL'       : 'https://static.suissealpine.sac-cas.ch/namemaster.jpg',
                 'original' : 'https://static.suissealpine.sac-cas.ch/name.jpg'
             }
        """
        photos = self._hut_dict.get("photos", [])
        if self.photos_count > index:
            photo = photos[index]
        else:
            raise IndexError("Photo index '{}' not available (max {} photos)".format(index, self.photos_count))

        caption = self.get_field_by_lang("caption", custom_dict=photo)
        copyright = photo.get("photo", {}).get("copyright", "")
        season = photo.get("photo", {}).get("season", "")
        thumb_orig = photo.get("photo", {}).get("thumbnails", {})

        thumb = {
            "S": thumb_orig["160x100"],
            "M": thumb_orig["500x313"],
            "L": thumb_orig["1800x1125"],
            "XL": thumb_orig["4000x2500"],
            "original": photo.get("photo", {}).get("url", ""),
        }
        out = {
            "caption": caption,
            "season": season,
            "copyright": copyright,
            "photo": thumb.get("L", ""),
        }
        out.update(thumb)
        return out

    def get_field_by_lang(self, field, default="", lang=None, custom_dict=None):
        """
        Returns field by language, if current language does not exist it tries
        another one.

        Parameters
        ----------
        field : str
            Field name (eg. 'display_name').
        default : any, optional
            Default value which is returned if not value is found.
            The default is ''.
        lang : ('de', 'fr', 'it', 'en'), optional
            Language used. The default is 'Hut.language'.
        custom_dict : dict, optional
            Dictionary instead of hut dictionary.

        Returns
        -------
        str
            The field value depending on the language.

        """
        if lang is None:
            lang = self.user_language
        else:
            lang = self._language_check(lang)

        if custom_dict is None:
            custom_dict = self._hut_dict
        if custom_dict is None:
            return default
        # print("Field '{}': id: '{}'".format(field, self.sac_id))
        languages = [lang, self.language, "en", "de", "fr", "it"]
        # check if any of these languages has a result
        for lang in languages:
            field_res = custom_dict.get(field, {})
            if field_res is None:
                return default
            res = field_res.get(lang, None)
            if res:
                return res
        return default

    def load_capacity_async(self):
        if not self._capacity_loading_p and not self._hut_dict.get("hrs_original"):
            self._future_capacity = Future()
            self._capacity_loading_p = threading.Thread(target=self._get_capacity_async, args=[self._future_capacity])
            self._capacity_loading_p.start()

    def get_capacity(self):
        if self._hut_dict.get("hrs_original", None) is not None:
            return self._get_capacity_from_hrs_dict()
        return []

        if not self._capacity_loading_p:
            self.load_capacity_async()
        # wait until it is done (max 10 s)
        try:
            capacity_dict = self._future_capacity.result(10)
        except (TimeoutError, futureTimeoutError):
            print("ERROR: capacitiy request for '{}' failed (timeout)".format(self.name))
            return []
        else:
            return capacity_dict

    def _get_capacity_from_hrs_dict(self):
        hrs_dict = self._hut_dict.get("hrs_original", {})

        rooms_over_time = []
        for _date_key, date_vac in hrs_dict.items():
            room_dict = {}
            rooms = date_vac.get(
                "ns2:bookingAvailabilityPerCategory",
                {},
            )
            # print("Check room '{}'".format(date_key))
            total_free_rooms = 0
            total_rooms = 0
            reservation_date = ""
            if not rooms:
                # print("No rooms.")
                # print(rooms)
                break

            if not isinstance(rooms, list):
                rooms = [rooms]
            for room_json in rooms:
                free_room = int(room_json.get("ns2:freePlaces"))
                total_room = int(room_json.get("ns2:totalPlaces"))
                hrs_res_datetime = datetime.datetime.strptime(date_vac.get("ns2:date"), "%Y-%m-%d")
                reservation_date = (hrs_res_datetime).strftime("%d.%m.%Y")
                total_free_rooms += free_room
                total_rooms += total_room
            # TODO multiple rooms (for loop)

            room_dict["raw"] = rooms
            room_dict["total_free_rooms"] = int(total_free_rooms)
            room_dict["total_rooms"] = int(total_rooms)
            room_dict["occupied_percent"] = int(
                round(100 * (1 - total_free_rooms / float(total_rooms))) if total_rooms != 0 else 0
            )
            room_dict["reservation_date"] = reservation_date
            room_dict["booking_enabled"] = date_vac["ns2:status"] in [
                "ReservationPossible",
                "ReservationNotPossibleOnline",
                "InsufficientContingent",
            ]
            room_dict["closed"] = not room_dict["booking_enabled"]
            room_dict["commment"] = ""
            # if rooms[0].get("contingentText", "") is None else rooms[0].get("contingentText", "")
            rooms_over_time.append(dict(room_dict))
        # return_dict[str(hut_id)] = hut_dict
        return rooms_over_time

    def _get_capacity_async(self, future, _retries=0):
        start_date = self.start_date
        max_days = self._show_future_days
        # date format: dd.mm.yyyy
        if not self.online_reservation or not self.start_date:
            future.set_result([])
            return False

        params = {"hut_id": str(self.hrs_id)}
        calendar_url = self.HRS_URL + "/calendar"
        select_date_url = f"{self.HRS_URL}/selectDate?date={start_date}"
        with requests.Session() as s:
            try:
                calendar_req = s.get(calendar_url, params=params)
                # print(calendar_req.url)
                date_req = s.get(select_date_url)
                # print(date_req.url)
            except requests.ConnectionError:
                time.sleep(0.2)
                # sleep and try again.
                if _retries < 5:  # try it max 5 times
                    __tries = _retries + 1
                    print(
                        "WARN: Connection error for '#{} - {}', {} {}".format(
                            self.hrs_id,
                            self.name,
                            __tries,
                            "tries" if __tries > 1 else "try",
                        )
                    )
                    self._get_capacity_async(future, _retries + 1)
                else:
                    print("ERROR: Connection error for '#{} - {}'. Abort.".format(self.hrs_id, self.name))
                    future.set_result([])
                    return False
                return True

            vacancy = dict(date_req.json())
            keys = sorted([int(k) for k in vacancy.keys()])
            calendar_req.close()
            date_req.close()
        rooms_over_time = []
        for date_key in keys[: max_days + 1]:  # range(0, max_days):
            room_dict = {}
            rooms = vacancy.get(str(date_key))
            # print("Check room '{}'".format(date_key))
            total_free_rooms = 0
            total_rooms = 0
            reservation_date = ""
            if not rooms:
                # print("No rooms.")
                # print(rooms)
                break
            for room_json in rooms:
                if room_json.get("hutBedCategoryId") is None:
                    print("        No hut information")
                    break
                # ratio = room_json.get('reservedRoomsRatio')
                free_room = room_json.get("freeRoom")
                total_room = room_json.get("totalRoom")
                reservation_date = room_json.get("reservationDate")
                total_free_rooms += free_room
                total_rooms += total_room
            room_dict["raw"] = rooms
            room_dict["total_free_rooms"] = int(total_free_rooms)
            room_dict["total_rooms"] = int(total_rooms)
            room_dict["occupied_percent"] = int(
                round(100 * (1 - total_free_rooms / float(total_rooms))) if total_rooms != 0 else 0
            )
            room_dict["reservation_date"] = reservation_date
            room_dict["closed"] = rooms[0]["closed"]
            room_dict["booking_enabled"] = rooms[0]["bookingEnabled"]
            room_dict["commment"] = (
                "" if rooms[0].get("contingentText", "") is None else rooms[0].get("contingentText", "")
            )
            rooms_over_time.append(room_dict)
        # return_dict[str(hut_id)] = hut_dict
        if _retries > 0:
            print(
                "INFO: Connection successful for '#{} - {}' after {} tries.".format(
                    self.hrs_id, self.name, _retries + 1
                )
            )
        future.set_result(rooms_over_time)
        return True

    def __repr__(self):
        out = "#{} - {}\n".format(self.sac_id, self.name)
        out += "{}".format(self.sac_url)
        if self.hrs_id:
            out += "\nhrs-id: {}\n".format(self.hrs_id)
            out += "{}\n".format(self.reservation_url)
        if self.get_capacity():
            capacity = self.get_capacity()[0]
            out += "free: {}, total: {} (booking {})".format(
                capacity.get("total_free_rooms"),
                capacity.get("total_rooms"),
                "enabled" if capacity.get("booking_enabled") else "disabled",
            )
        return out

    def __getitem__(self, key):
        return getattr(self, key, None)

    def _language_check(self, lang):
        if lang.lower() not in ["de", "fr", "it", "en"]:
            raise ValueError("Language '{}' not supported. Use either 'de', 'fr', 'it' or 'en'.".format(lang))
        return lang.lower()


if __name__ == "__main__":
    s = requests.Session()

    LANG = "de"
    HUT_INDEX = 2

    # 0: Aarbiwak SAC, biwak
    # 1: Albert-Heim SAC, no online reservation
    # 2: Almagellerhütte SAC, massenlager, online reservation
    # 3: Alpage de la Peule, private, no online reservation
    # 4: Alpage La Grandsonnaz-Dessus, private, no reservation, no catering info
    # 11: Arbenbiwak SAC, biwak, no reservation
    # 30: Berglihütte SAC, biwak  with reservation
    # 35: Binntalhütte SAC, online reservation, different rooms
    # 252: Rifugio Andolla, no informations

    if HUT_INDEX < 1000:
        url = "https://www.suissealpine.sac-cas.ch/api/1/poi/search"
        params = {
            "lang": "de",
            "order_by": "display_name",
            "type": "hut",
            "disciplines": "",
            "hut_type": "all",
            "limit": HUT_INDEX + 2,
        }

        r = s.get(url, params=params)
        huts = r.json().get("results", {})
        hut_or_id = huts[HUT_INDEX]
    else:
        hut_or_id = HUT_INDEX
    # df = pd.json_normalize(huts)

    hut = Hut.create(hut_or_id, lang=LANG)

    # print("#{} - {}".format(hut.sac_id, hut.name))

    # free = hut.get_capacity("26.09.2020")
    capacity = hut.get_capacity()
