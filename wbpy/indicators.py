# -*- coding: utf-8 -*-
from wbpy import Indicators

import utils




class IndicatorDataset(object):
    """ A single World Bank Indicator model. Includes the raw JSON response,
    various metadata, and methods to convert the data into useful objects.

    """

    def __init__(self, json_resp, url=None, date_of_call=None):

        self.api_url = url
        self.api_call_date = date_of_call
        self.api_response = json_resp

        # The country codes and names
        self.data_countries = {}
        for country_data in self.api_response[1]:
            country_id = country_data["country"]["id"]
            country_val = country_data["country"]["value"]
            if country_id not in self.data_countries:
                self.data_countries[country_id] = country_val



        # Information on the indicator
        self.indicator_code = self.api_response[1][0]["indicator"]["id"]
        self.indicator_name = self.api_response[1][0]["indicator"]["value"]

        # For some use cases, it's nice to have direct access to all the
        # `get_indicator()` metadata (eg. the sources, full description). 
        # It won't always be wanted, so it's requested lazily. 
        self._metadata_response = None

    def __repr__(self):
        s = "<%s.%s(%r, %r) with id: %r>"
        return s % (
            self.__class__.__module__,
            self.__class__.__name__,
            self.indicator_code,
            self.indicator_name,
            id(self),
            )

    def __str__(self):
        return str(self.data_as_dict())

    def data_dates(self, use_datetime=False):
        """ The dates used for this dataset.
        """
        dates = []
        for country_data in self.data_as_dict().values():
            for date in country_data.keys():
                if date not in dates:
                    dates.append(date)

        if use_datetime:
            dates = [utils.worldbank_date_to_datetime(d) for d in dates]

        return sorted(dates)

    def _get_metadata_response(self):
        api = Indicators()
        indicators = api.get_indicators([self.indicator_code])
        self._metadata_response = indicators[self.indicator_code]

    @property
    def indicator_source(self):
        if not self._metadata_response:
            self._get_metadata_response()
        return self._metadata_response["source"]

    @property
    def indicator_source_note(self):
        if not self._metadata_response:
            self._get_metadata_response()
        return self._metadata_response["sourceNote"]

    @property
    def indicator_source_org(self):
        if not self._metadata_response:
            self._get_metadata_response()
        return self._metadata_response["sourceOrganization"]

    @property
    def indicator_topics(self):
        if not self._metadata_response:
            self._get_metadata_response()
        return self._metadata_response["topics"]


    def data_as_dict(self, use_datetime=False):
        clean_dict = {}
        response_data = self.api_response[1]
        for row in response_data:
            country_id = row["country"]["id"]
            date = row["date"]
            if use_datetime:
                date = utils.worldbank_date_to_datetime(date)

            if country_id not in clean_dict:
                clean_dict[country_id] = {}
            if date not in clean_dict[country_id]:
                clean_dict[country_id][date] = float(row["value"])

        return clean_dict




