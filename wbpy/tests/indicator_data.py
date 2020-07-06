# -*- coding: utf-8 -*-
import datetime

import wbpy

class TestData(object):
    """ API response data for testing. """

    def __init__(self):
        self.dataset = wbpy.IndicatorDataset(self.response, self.url, self.date)

class Yearly(TestData):
    url = "api.worldbank.org/countries/GB;AR;SA;HK/indicators/SP.POP.TOTL?format=json&per_page=1000&mrv=2"
    date = datetime.date(2013, 9, 19)
    response = [

    {
        "page": 1,
        "pages": 1,
        "per_page": "1000",
        "total": 8
    },
    [
        {
            "indicator": {
                "id": "SP.POP.TOTL",
                "value": "Population, total"
            },
            "country": {
                "id": "AR",
                "value": "Argentina"
            },
            "value": "41086927",
            "decimal": "0",
            "date": "2012"
        },
        {
            "indicator": {
                "id": "SP.POP.TOTL",
                "value": "Population, total"
            },
            "country": {
                "id": "AR",
                "value": "Argentina"
            },
            "value": "40728738",
            "decimal": "0",
            "date": "2011"
        },
        {
            "indicator": {
                "id": "SP.POP.TOTL",
                "value": "Population, total"
            },
            "country": {
                "id": "GB",
                "value": "United Kingdom"
            },
            "value": "63227526",
            "decimal": "0",
            "date": "2012"
        },
        {
            "indicator": {
                "id": "SP.POP.TOTL",
                "value": "Population, total"
            },
            "country": {
                "id": "GB",
                "value": "United Kingdom"
            },
            "value": "62752472",
            "decimal": "0",
            "date": "2011"
        },
        {
            "indicator": {
                "id": "SP.POP.TOTL",
                "value": "Population, total"
            },
            "country": {
                "id": "HK",
                "value": "Hong Kong SAR, China"
            },
            "value": "7154600",
            "decimal": "0",
            "date": "2012"
        },
        {
            "indicator": {
                "id": "SP.POP.TOTL",
                "value": "Population, total"
            },
            "country": {
                "id": "HK",
                "value": "Hong Kong SAR, China"
            },
            "value": "7071600",
            "decimal": "0",
            "date": "2011"
        },
        {
            "indicator": {
                "id": "SP.POP.TOTL",
                "value": "Population, total"
            },
            "country": {
                "id": "SA",
                "value": "Saudi Arabia"
            },
            "value": "28287855",
            "decimal": "0",
            "date": "2012"
        },
        {
            "indicator": {
                "id": "SP.POP.TOTL",
                "value": "Population, total"
            },
            "country": {
                "id": "SA",
                "value": "Saudi Arabia"
            },
            "value": "27761728",
            "decimal": "0",
            "date": "2011"
        }
    ]

    ]

    indicator = {

    "id": "SP.POP.TOTL",
    "name": "Population, total",
    "source": {
        "id": "2",
        "value": "World Development Indicators"
    },
    "sourceNote": "Total population is based on the de facto definition of population, which counts all residents regardless of legal status or citizenship. The values shown are midyear estimates.",
    "sourceOrganization": "(1) United Nations Population Division. World Population Prospects: 2019 Revision. (2) Census reports and other statistical publications from national statistical offices, (3) Eurostat: Demographic Statistics, (4) United Nations Statistical Division. Population and Vital Statistics Reprot (various years), (5) U.S. Census Bureau: International Database, and (6) Secretariat of the Pacific Community: Statistics and Demography Programme.",
    "topics": [
        {
            "id": "8",
            "value": "Health "
        },
        {
            "id": "19",
            "value": "Climate Change"
        }
    ]

    }

    def __init__(self):
        self.dataset = wbpy.IndicatorDataset(self.response, self.url, self.date)


class Monthly(TestData):
    url = "api.worldbank.org/en/countries/ind;chn/indicators/DPANUSSPF?MRV=7&frequency=M&format=json"
    date = datetime.date(2013, 9, 19)
    response = [

    {
        "page": 1,
        "pages": 1,
        "per_page": "50",
        "total": 14
    },
    [
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "CN",
                "value": "China"
            },
            "value": "6.12179545455",
            "decimal": "0",
            "date": "2013M08"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "CN",
                "value": "China"
            },
            "value": "6.13418695652",
            "decimal": "0",
            "date": "2013M07"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "CN",
                "value": "China"
            },
            "value": "6.13445",
            "decimal": "0",
            "date": "2013M06"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "CN",
                "value": "China"
            },
            "value": "6.14102173913",
            "decimal": "0",
            "date": "2013M05"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "CN",
                "value": "China"
            },
            "value": "6.18657272727",
            "decimal": "0",
            "date": "2013M04"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "CN",
                "value": "China"
            },
            "value": "6.2159",
            "decimal": "0",
            "date": "2013M03"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "CN",
                "value": "China"
            },
            "value": "6.233015",
            "decimal": "0",
            "date": "2013M02"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "IN",
                "value": "India"
            },
            "value": "62.91897727273",
            "decimal": "0",
            "date": "2013M08"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "IN",
                "value": "India"
            },
            "value": "59.8094",
            "decimal": "0",
            "date": "2013M07"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "IN",
                "value": "India"
            },
            "value": "58.3845",
            "decimal": "0",
            "date": "2013M06"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "IN",
                "value": "India"
            },
            "value": "54.99103043478",
            "decimal": "0",
            "date": "2013M05"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "IN",
                "value": "India"
            },
            "value": "54.38226363636",
            "decimal": "0",
            "date": "2013M04"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "IN",
                "value": "India"
            },
            "value": "54.42345238095",
            "decimal": "0",
            "date": "2013M03"
        },
        {
            "indicator": {
                "id": "DPANUSSPF",
                "value": "Exchange rate, old LCU per USD extended forward, period average"
            },
            "country": {
                "id": "IN",
                "value": "India"
            },
            "value": "53.841375",
            "decimal": "0",
            "date": "2013M02"
        }
    ]

    ]

    indicator = {

    "id": "DPANUSSPF",
    "name": "Exchange rate, old LCU per USD extended forward, period average",
    "source": {
        "id": "15",
        "value": "Global Economic Monitor"
    },
    "sourceNote": "Local currency units (LCU) per U.S. dollar, with values after a new currency's introduction presented in the old currency's terms",
    "sourceOrganization": "World Bank staff calculations based on Datastream and IMF International Finance Statistics data.",
    "topics": [
        { }
    ]

    }


class Quarterly(TestData):
    url = "api.worldbank.org/en/countries/es/indicators/NEER?MRV=10&frequency=Q"
    date = datetime.date(2013, 9, 19)
    response = [

    {
        "page": 1,
        "pages": 1,
        "per_page": "50",
        "total": 10
    },
    [
        {
            "indicator": {
                "id": "NEER",
                "value": "Nominal Effecive Exchange Rate"
            },
            "country": {
                "id": "ES",
                "value": "Spain"
            },
            "value": "101.96915025708",
            "decimal": "0",
            "date": "2013Q3"
        },
        {
            "indicator": {
                "id": "NEER",
                "value": "Nominal Effecive Exchange Rate"
            },
            "country": {
                "id": "ES",
                "value": "Spain"
            },
            "value": "101.63248639595",
            "decimal": "0",
            "date": "2013Q2"
        },
        {
            "indicator": {
                "id": "NEER",
                "value": "Nominal Effecive Exchange Rate"
            },
            "country": {
                "id": "ES",
                "value": "Spain"
            },
            "value": "101.52582061816",
            "decimal": "0",
            "date": "2013Q1"
        },
        {
            "indicator": {
                "id": "NEER",
                "value": "Nominal Effecive Exchange Rate"
            },
            "country": {
                "id": "ES",
                "value": "Spain"
            },
            "value": "100.18916509029",
            "decimal": "0",
            "date": "2012Q4"
        },
        {
            "indicator": {
                "id": "NEER",
                "value": "Nominal Effecive Exchange Rate"
            },
            "country": {
                "id": "ES",
                "value": "Spain"
            },
            "value": "99.16917359022",
            "decimal": "0",
            "date": "2012Q3"
        },
        {
            "indicator": {
                "id": "NEER",
                "value": "Nominal Effecive Exchange Rate"
            },
            "country": {
                "id": "ES",
                "value": "Spain"
            },
            "value": "100.11249906251",
            "decimal": "0",
            "date": "2012Q2"
        },
        {
            "indicator": {
                "id": "NEER",
                "value": "Nominal Effecive Exchange Rate"
            },
            "country": {
                "id": "ES",
                "value": "Spain"
            },
            "value": "100.78249347922",
            "decimal": "0",
            "date": "2012Q1"
        },
        {
            "indicator": {
                "id": "NEER",
                "value": "Nominal Effecive Exchange Rate"
            },
            "country": {
                "id": "ES",
                "value": "Spain"
            },
            "value": "101.79581836818",
            "decimal": "0",
            "date": "2011Q4"
        },
        {
            "indicator": {
                "id": "NEER",
                "value": "Nominal Effecive Exchange Rate"
            },
            "country": {
                "id": "ES",
                "value": "Spain"
            },
            "value": "102.65581120157",
            "decimal": "0",
            "date": "2011Q3"
        },
        {
            "indicator": {
                "id": "NEER",
                "value": "Nominal Effecive Exchange Rate"
            },
            "country": {
                "id": "ES",
                "value": "Spain"
            },
            "value": "103.22580645161",
            "decimal": "0",
            "date": "2011Q2"
        }
    ]

    ]

    indicator = {

    "id": "NEER",
    "name": "Nominal Effecive Exchange Rate",
    "source": {
        "id": "15",
        "value": "Global Economic Monitor"
    },
    "sourceNote": "A measure of the value of a currency against a weighted average of several foreign currencies",
    "sourceOrganization": "World Bank staff calculations based on Datastream and IMF International Finance Statistics data.",
    "topics": [
        { }
    ]

    }
