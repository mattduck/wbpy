# -*- coding: utf-8 -*-
import datetime
try:
    # py2.6
    import unittest2 as unittest
except ImportError:
    # py2.7+
    import unittest

from ddt import ddt, data

import wbpy
from wbpy.tests.indicator_data import Yearly, Monthly, Quarterly

@ddt
class TestIndicatorDatasetBasicAttrs(unittest.TestCase):

        @data(Yearly())
        def test_repr_fn(self, data):
            self.assertIn(data.indicator["id"], repr(data.dataset))
            self.assertIn(data.indicator["name"], repr(data.dataset))

        @data(Yearly())
        def test_str_fn_doesnt_raise(self, data):
            str(data.dataset)

        @data(Yearly())
        def test_api_url_attr(self, data):
            self.assertEqual(data.dataset.api_url, data.url)

        @data(Yearly())
        def test_api_call_date_attr(self, data):
            self.assertEqual(data.dataset.api_call_date, data.date)

        @data(Yearly())
        def test_api_response_attr(self, data):
            self.assertEqual(data.dataset.api_response, data.response)

        @data(Yearly())
        def test_countries_attr(self, data):
            for row in data.response[1]:
                country = row["country"]
                self.assertEqual(data.dataset.countries[country["id"]],
                    country["value"])

        @data(Yearly(), Monthly(), Quarterly())
        def test_indicator_code_attr(self, data):
            self.assertEqual(data.dataset.indicator_code,
                data.response[1][0]["indicator"]["id"])

        @data(Yearly(), Monthly(), Quarterly())
        def test_indicator_name_attr(self, data):
            self.assertEqual(data.dataset.indicator_name,
                data.response[1][0]["indicator"]["value"])

        @data(Yearly(), Monthly(), Quarterly())
        def test_indicator_source_attr(self, data):
            self.assertEqual(data.dataset.indicator_source,
                data.indicator["source"])

        @data(Yearly(), Monthly(), Quarterly())
        def test_indicator_source_note_attr(self, data):
            self.assertEqual(data.dataset.indicator_source_note,
                data.indicator["sourceNote"])

        @data(Yearly(), Monthly(), Quarterly())
        def test_indicator_source_org_attr(self, data):
            # Strip whitespace to avoid comparison issues
            expected = "".join(data.indicator["sourceOrganization"].split())
            result = "".join(data.dataset.indicator_source_org.split())
            self.assertEqual(result, expected)

        @data(Yearly(), Monthly(), Quarterly())
        def test_indicator_topics_attr(self, data):
            expected = data.indicator["topics"]
            result = data.dataset.indicator_topics
            self.assertEqual(
                sorted(result, key=lambda i: i.get('id')),
                sorted(expected, key=lambda i: i.get('id')))



@ddt
class TestIndicatorDatasetDataDatesFn(unittest.TestCase):

    @data(Yearly(), Monthly(), Quarterly())
    def test_dates_are_strings(self, data):
        exp_dates = sorted(list(set(row["date"] for row in data.response[1])))
        self.assertEqual(data.dataset.dates(), exp_dates)

    def test_datetime_param_yearly(self):
        data = Yearly()
        results = data.dataset.dates(use_datetime=True)
        expected = [datetime.date(2011, 1, 1), datetime.date(2012, 1, 1)]
        self.assertEqual(results, expected)

    def test_datetime_param_monthly(self):
        data = Monthly()
        results = data.dataset.dates(use_datetime=True)
        self.assertEqual(results[0], datetime.date(2013, 2, 1))
        self.assertEqual(results[-1], datetime.date(2013, 8, 1))

    def test_datetime_param_quarterly(self):
        data = Quarterly()
        results = data.dataset.dates(use_datetime=True)
        self.assertEqual(results[0], datetime.date(2011, 4, 1))
        self.assertEqual(results[-1], datetime.date(2013, 7, 1))


@ddt
class TestIndicatorDatasetDictFn(unittest.TestCase):

        @data(Yearly(), Monthly(), Quarterly())
        def test_country_keys(self, data):
            resp = data.response[1]
            expected = sorted(list(set([row["country"]["id"] for row in resp])))
            self.assertEqual(sorted(data.dataset.as_dict().keys()),
                expected)

        def test_yearly_keys(self):
            data = Yearly()
            for country_data in data.dataset.as_dict().values():
                self.assertEqual(sorted(country_data.keys()),
                    ["2011", "2012"])

        def test_monthly_keys(self):
            data = Monthly()
            first_country = list(data.dataset.as_dict().values())[0]
            self.assertIn("2013M07", first_country.keys())

        def test_quarterly_keys(self):
            data = Quarterly()
            first_country = list(data.dataset.as_dict().values())[0]
            self.assertIn("2013Q2", first_country.keys())

        def test_yearly_datetime_param(self):
            data = Yearly()
            results = data.dataset.as_dict(use_datetime=True).values()
            for country_data in results:
                self.assertEqual(sorted(country_data.keys()),
                    [datetime.date(2011, 1, 1), datetime.date(2012, 1, 1)])

        def test_monthly_datetime_param(self):
            data = Monthly()
            results = list(data.dataset.as_dict(use_datetime=True).values())
            first_country = results[0]
            self.assertIn(datetime.date(2013, 8, 1), first_country.keys())

        def test_quarterly_datetime_param(self):
            data = Quarterly()
            results = list(data.dataset.as_dict(use_datetime=True).values())
            first_country = results[0]
            self.assertIn(datetime.date(2013, 4, 1), first_country.keys())

        def test_yearly_values(self):
            data = Yearly()
            self.assertEqual(data.dataset.as_dict()["AR"]["2011"], 40728738)
            self.assertEqual(data.dataset.as_dict()["GB"]["2012"], 63227526)
            self.assertEqual(data.dataset.as_dict()["HK"]["2012"], 7154600)

        def test_monthly_values(self):
            data = Monthly()
            self.assertEqual(data.dataset.as_dict()["IN"]["2013M04"],
                54.38226363636)

        def test_quarterly_values(self):
            data = Quarterly()
            self.assertEqual(data.dataset.as_dict()["ES"]["2012Q4"],
                100.18916509029)


class TestIndicatorAPI(unittest.TestCase):
    def setUp(self):
        self.api = wbpy.IndicatorAPI()


class TestTopics(TestIndicatorAPI):
    def test_returns_topics(self):
        data = self.api.get_topics()
        topic = list(data.values())[1]
        self.assertTrue('value' in topic)
        self.assertTrue('sourceNote' in topic)


class TestSources(TestIndicatorAPI):
    def test_returns_sources(self):
        data = self.api.get_sources()
        source = list(data.values())[1]
        self.assertTrue('name' in source)


class TestCountries(TestIndicatorAPI):
    def test_returns_countries(self):
        test_keys = ['GB', 'AF', 'FR', 'IT', 'BR']
        data = self.api.get_countries(test_keys)
        self.assertTrue(all([key in data for key in test_keys]))

    def test_income_level_param(self):
        results = self.api.get_countries(incomeLevel="UMC")
        income_levels = set()
        for country in results.values():
            income_levels.add(country["incomeLevel"]["id"])
        self.assertEqual(list(income_levels), ["UMC"])

    def test_lending_type_param(self):
        results = self.api.get_countries(lendingType="IBD")
        lending_types = set()
        for country in results.values():
            lending_types.add(country["lendingType"]["id"])
        self.assertEqual(list(lending_types), ["IBD"])

    def test_region_param(self):
        results = self.api.get_countries(region="LCN")
        regions = set()
        for country in results.values():
            regions.add(country["region"]["id"])
        self.assertEqual(list(regions), ["LCN"])


class TestIncome(TestIndicatorAPI):
    def test_returns_income_levels(self):
        test_keys = ['LMC', 'UMC']
        data = self.api.get_income_levels(test_keys)
        self.assertTrue(all([key in test_keys for key in data]))


class TestRegions(TestIndicatorAPI):
    def test_returns_regions(self):
        data = self.api.get_regions(search="Latin")
        self.assertTrue(all(['latin' in v['name'].lower() for v in data.values()]))


class TestIndicators(TestIndicatorAPI):
    def test_returns_indicators(self):
        data = self.api.get_indicators()
        self.assertTrue(len(data) > 7500)

    def test_common_only_flag_filters_out_codes(self):
        data = self.api.get_indicators(common_only=True)
        self.assertGreater(len(data), 5)
        self.assertLess(len(data), 2000)

    def test_topic_kwarg(self):
        results = self.api.get_indicators(topic=4)
        # Every indicator should at least belong to topic 4.
        matches = []
        for v in results.values():
            matches.append('4' in [topic['id'] for topic in v['topics']])
        self.assertTrue(all(matches))

    def test_source_kwargs(self):
        results = self.api.get_indicators(source=15)
        result_sources = set()
        for row in results.values():
            result_sources.add(row["source"]["id"])
        self.assertEqual(list(result_sources), ["15"])

    def test_bad_request_raises_exception(self):
        def bad_request():
            codes = ["SP,lkjsdf"]
            self.api.get_indicators(codes)

        self.assertRaises(ValueError, bad_request)


@ddt
class TestGetDatasetFn(TestIndicatorAPI):
    def test_get_dataset_returns_dataset(self):
        results = self.api.get_dataset("SP.POP.GROW")
        self.assertEqual(results.indicator_code, "SP.POP.GROW")

    def test_country_list(self):
        countries = ["GB"]
        results = self.api.get_dataset("SP.POP.TOTL", countries)
        self.assertEqual(list(results.countries.keys()), ["GB"])

    def test_language_kwarg(self):
        results = self.api.get_dataset("SP.POP.TOTL", language="FR")
        self.assertIn("Royaume-Uni", results.countries.values())

    def test_date_kwarg(self):
        results = self.api.get_dataset("SP.POP.GROW", date="2003")
        self.assertEqual(results.dates(), ["2003"])

    def test_mrv_kwarg(self):
        results = self.api.get_dataset("SP.POP.GROW", mrv=6)
        self.assertEqual(len(results.dates()), 6)

    @data(True, "y")
    def test_gapfill_kwarg(self, gapfill):
        countries = ["BR"]
        results = self.api.get_dataset("SP.POP.GROW", countries, mrv=5,
            gapfill=gapfill)
        self.assertEqual(len(results.dates()), 5)

    def test_frequency_kwarg(self):
        results = self.api.get_dataset("DPANUSSPF", date="2009:2010",
                mrv="2", frequency="M")
        self.assertIn("2010M12", results.dates())

    def test_banned_kwarg(self):
        results = self.api.get_dataset("SP.POP.TOTL", per_page=5)
        self.assertNotIn("per_page=5", results.api_url.lower())
        self.assertIn("per_page=1000", results.api_url.lower())

    def test_bad_request_raises_exception(self):
        def bad_request():
            self.api.get_dataset("SP,lkjsdf")

        self.assertRaises(ValueError, bad_request)

    def test_another_bad_request_raises_exception(self):
        # This one slipped through _raise_if_response_contains_error()
        def request_with_no_data():
            results = self.api.get_dataset("DPANUSIFS", date="2009:2010",
                mrv="2", frequency="M")
        self.assertRaises(ValueError, request_with_no_data)

class TestInit(TestIndicatorAPI):
    def test_can_pass_own_cache_object(self):
        from six.moves.urllib import request
        def test_fetch(url):
            return request.urlopen(url).read()

        data = self.api.get_topics()
        self.assertTrue("sourceNote" in list(data.values())[1])


@ddt
class TestPrintCodes(TestIndicatorAPI):
    @data(
        "get_countries",
        "get_income_levels",
        "get_indicators",
        "get_sources",
        "get_topics",
        "get_regions",
        "get_lending_types",

        )
    def test_can_handle_all_api_funcs_without_error(self, fn_name):
        results = getattr(self.api, fn_name)()
        self.api.print_codes(results)
        assert True

    def test_search_param_doesnt_raise(self):
        results = self.api.get_countries()
        self.api.print_codes(results, search="United")
        assert True

    def test_search_param_can_handle_search_key_arg(self):
        results = self.api.get_countries()
        self.api.print_codes(results, search="United", search_key=["name"])
        assert True


class TestSearch(TestIndicatorAPI):
    def test_that_default_search_is_of_keys_and_not_values(self):
        data = self.api.get_sources(search="11") # 11 is a key, and not in the value

        self.assertIn("11", data.keys())
        # Can find other things.
        # self.assertEqual(len(data), 1)

    def test_search_results_takes_regexp(self):
        # Check that case is ignored too
        data = dict(
            foo="I hope this one will MATCH",
            bar="This one will not match, I hope",
            )

        results = self.api.search_results("hope.+match", data)
        self.assertTrue("foo" in results.keys())
        self.assertFalse("bar" in results.keys())

    def test_search_results_takes_key(self):
        data = self.api.get_topics()

        results = self.api.search_results("poverty", data, key="value")
        self.assertTrue("11" in results) # Code for Poverty topic
        self.assertEqual(len(results.keys()), 1)

        results = self.api.search_results("poverty", data)
        self.assertGreater(len(results.keys()), 1)

    def test_search_full_flag_filters_descriptions(self):
        # By default, should only be searching the name of the country
        data = self.api.get_countries(search="america")
        for v in data.values():
            self.assertIn("america", v["name"].lower())
        default_len = len(data)

        # When full, should be searching the values too
        data = self.api.get_countries(search="america", search_full=True)
        for v in data.values():
            self.assertIn("america", str(v).lower())
        full_len = len(data)

        self.assertGreater(full_len, default_len)


class TestCountryCodes(TestIndicatorAPI):
    def test_ISO_2_standard_codes_supported(self):
        codes = ["US", "AF"]
        data = self.api.get_countries(codes)
        self.assertEqual(data["US"]["name"], "United States")
        self.assertEqual(data["AF"]["name"], "Afghanistan")

    def test_ISO_3_standard_codes_supported(self):
        codes = ["USA", "AFG"]
        data = self.api.get_countries(codes)
        self.assertEqual(data["US"]["name"], "United States")
        self.assertEqual(data["AF"]["name"], "Afghanistan")

    # There are various non-standard 2-digit and 3-digit codes used for
    # regions. Test a couple of them to make sure that they're getting
    # converted.
    #
    # The API docs claim that these codes are non-standard, but that doesn't
    # seem to be the case:
    #
    # ("andorra", "ad", "and"),
    # ("serbia", "rs", "srb"),
    # ("congo, dem", "cd", "cod"),
    # ("isle of man", "im", "imn"),
    # ("romania", "ro", "rou"),
    # ("timor-leste", "tl", "tls"),
    # ("gaza", "ps", "pse"),

    def test_alpha2_kosovo(self):
        codes = ["xk"]
        data = self.api.get_countries(codes)
        self.assertEqual(data["XK"]["name"], "Kosovo")

    def test_alpha3_kosovo(self):
        codes = ["xk"]
        data = self.api.get_countries(codes)
        self.assertEqual(data["XK"]["name"], "Kosovo")

    def test_alpha2_arab_world(self):
        codes = ["1a"]
        data = self.api.get_countries(codes)
        self.assertEqual(data["1A"]["name"], "Arab World")

    def test_alpha3_arab_world(self):
        codes = ["arb"]
        data = self.api.get_countries(codes)
        self.assertEqual(data["1A"]["name"], "Arab World")
