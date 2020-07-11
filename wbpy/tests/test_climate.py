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
from wbpy.tests.climate_data import (
    InstrumentalMonth,
    InstrumentalYear,
    InstrumentalDecade,
    ModelledVarMAVG,
    ModelledVarAANOM,
    ModelledStat,
)

@ddt
class TestClimateDataBasicAttrs(unittest.TestCase):
    """ Tests for the base ClimateDataset class. """

    @data(InstrumentalMonth(), InstrumentalYear(), InstrumentalDecade())
    def test_repr_fn(self, data):
        self.assertIn(data.data_type, repr(data.dataset))
        self.assertIn(data.data_stat, repr(data.dataset))

    @data(InstrumentalMonth(), InstrumentalYear(), InstrumentalDecade())
    def test_str_fn_doesnt_raise(self, data):
        str(data.dataset)

    @data(InstrumentalMonth(), InstrumentalYear(), InstrumentalDecade())
    def test_api_call_urls(self, data):
        expected_urls = [x["url"] for x in data.data]
        dataset_urls = [x["url"] for x in data.dataset.api_calls]
        self.assertEqual(sorted(expected_urls), sorted(dataset_urls))

    @data(InstrumentalMonth(), InstrumentalYear(), InstrumentalDecade())
    def test_api_call_responses(self, data):
        expected_resps = [x["resp"] for x in data.data]
        dataset_resps = [x["resp"] for x in data.dataset.api_calls]
        self.assertEqual(expected_resps, dataset_resps)

    @data(InstrumentalMonth(), InstrumentalYear(), InstrumentalDecade())
    def test_type_attr(self, data):
        self.assertIn(data.data_stat, data.dataset.data_type)

    @data(InstrumentalMonth(), InstrumentalYear(), InstrumentalDecade())
    def test_stat_attr(self, data):
        self.assertIn(data.data_type, data.dataset.interval)


@ddt
class TestInstrumentalModelBasicAttrs(unittest.TestCase):

    def test_api_call_regions_month(self):
        data = InstrumentalMonth()
        dataset_regions = [x["region"] for x in data.dataset.api_calls]
        expected = [("ES", "Spain"), ("GB", "United Kingdom")]
        self.assertEqual(sorted(dataset_regions), expected)

    def test_api_call_regions_year(self):
        data = InstrumentalYear()
        dataset_regions = [x["region"] for x in data.dataset.api_calls]
        expected = [("BR", "Brazil")]
        self.assertEqual(sorted(dataset_regions), expected)

    def test_api_call_regions_decade(self):
        data = InstrumentalDecade()
        dataset_regions = [x["region"][0] for x in data.dataset.api_calls]
        self.assertEqual(sorted(dataset_regions), ["300", "302"] )

    @data(InstrumentalMonth(), InstrumentalYear(), InstrumentalDecade())
    def test_api_call_date_attr(self, data):
        self.assertEqual(data.dataset.api_call_date, data.date)

    @data(InstrumentalMonth(), InstrumentalYear(), InstrumentalDecade())
    def test_dates_attr(self, data):
        self.assertIn("1901", data.dataset.dates)


@ddt
class TestInstrumentalModelDictFn(unittest.TestCase):

    @data(InstrumentalMonth(), InstrumentalYear(), InstrumentalDecade())
    def test_region_keys(self, data):
        dataset_regions = [x["region"][0] for x in data.dataset.api_calls]
        for key in data.dataset.as_dict():
            self.assertIn(key, dataset_regions)

    def test_month_keys(self):
        data = InstrumentalMonth()
        results = data.dataset.as_dict()
        for region in results.values():
            self.assertEqual(len(region), 12)

    @data(InstrumentalYear(), InstrumentalDecade())
    def test_year_keys(self, data):
        results = data.dataset.as_dict()
        for region in results.values():
            self.assertIn(str(2000), region)

    @data(InstrumentalYear(), InstrumentalDecade())
    def test_year_datetime_keys(self, data):
        results = data.dataset.as_dict(use_datetime=True)
        for region in results.values():
            self.assertIn(datetime.date(2000, 1, 1), region)

    def test_month_values(self):
        data = InstrumentalMonth()
        results = data.dataset.as_dict()
        self.assertEqual(results["GB"][3], 7.046495)

    def test_year_values(self):
        data = InstrumentalYear()
        results = data.dataset.as_dict()
        self.assertEqual(results["BR"]["1902"], 25.09181)

    def test_decade_values(self):
        data = InstrumentalDecade()
        results = data.dataset.as_dict()
        self.assertEqual(results["300"]["1990"], 13.437422)

@ddt
class TestModelledModelBasicAttrs(unittest.TestCase):

    @data(ModelledVarMAVG(), ModelledVarAANOM())
    def test_gcm_attr(self, data):
        self.assertIn("bccr_bcm2_0", data.dataset.gcms)

    def test_gcm_attr_ensemble(self):
        data = ModelledStat()
        self.assertIn("ensemble_10", data.dataset.gcms)

    @data(ModelledVarMAVG(), ModelledVarAANOM(), ModelledStat())
    def test_scenario_attr(self, data):
        self.assertIn("a2", data.dataset.sres)
        self.assertIn("b1", data.dataset.sres)


class TestModelledModelDatesFn(unittest.TestCase):

    def test_mavg(self):
        data = ModelledVarMAVG()
        expected = [("2020", "2039"), ("2040", "2059")]
        self.assertEqual(data.dataset.dates(), expected)

    def test_mavg_datetime(self):
        data = ModelledVarMAVG()
        dt = lambda x: datetime.date(x, 1, 1)
        expected = [(dt(2020), dt(2039)), (dt(2040), dt(2059))]
        self.assertEqual(data.dataset.dates(use_datetime=True), expected)

    def test_aanom(self):
        data = ModelledVarAANOM()
        expected = [("2020", "2039"), ("2060", "2079")]
        self.assertEqual(data.dataset.dates(), expected)

    def test_aanom_datetime(self):
        data = ModelledVarAANOM()
        dt = lambda x: datetime.date(x, 1, 1)
        expected = [(dt(2020), dt(2039)), (dt(2060), dt(2079))]
        self.assertEqual(data.dataset.dates(use_datetime=True), expected)

    def test_stat(self):
        data = ModelledStat()
        expected = [("2046", "2065")]
        self.assertEqual(data.dataset.dates(), expected)

    def test_stat_datetime(self):
        data = ModelledStat()
        dt = lambda x: datetime.date(x, 1, 1)
        expected = [(dt(2046), dt(2065))]
        self.assertEqual(data.dataset.dates(use_datetime=True), expected)

@ddt
class TestModelledModelDictFn(unittest.TestCase):

    @data(ModelledVarMAVG(), ModelledVarAANOM())
    def test_gcm_key(self, data):
        self.assertIn("ingv_echam4", data.dataset.as_dict())

    def test_gcm_key_ensemble(self):
        data = ModelledStat()
        self.assertIn("ensemble_90", data.dataset.as_dict())

    @data([ModelledVarMAVG(), ("BR",)],
        [ModelledVarAANOM(), ("JP",)],
        [ModelledStat(), ("AU", "NZ")],
        )
    def test_region_key(self, foo):
        data, expected_regions = foo
        for gcm_dict in data.dataset.as_dict().values():
            for region in expected_regions:
                self.assertIn(region, gcm_dict)

    @data([ModelledVarMAVG(), "2039"], [ModelledStat(), "2065"])
    def test_date_key_monthly(self, foo):
        data, year = foo
        res = data.dataset.as_dict()
        for gcm_dict in res.values():
            for region_dict in gcm_dict.values():
                self.assertEqual(len(region_dict[year]), 12)

    def test_date_key_yearly(self):
        data = ModelledVarAANOM()
        res = data.dataset.as_dict()
        for gcm_dict in res.values():
            for region_dict in gcm_dict.values():
                # Just check one date
                self.assertIn("2079", region_dict)

    def test_date_key_yearly_datetime(self):
        data = ModelledVarAANOM()
        res = data.dataset.as_dict(use_datetime=True)
        for gcm_dict in res.values():
            for region_dict in gcm_dict.values():
                # Just check one date
                self.assertIn(datetime.date(2079, 1, 1), region_dict)

    def test_value(self):
        data = ModelledStat()
        res = data.dataset.as_dict()["ensemble_90"]["NZ"]["2065"][10]
        self.assertEqual(res, 12.763983215594646)

    def test_value_b1_scenario_kwarg(self):
        data = ModelledStat()
        res = data.dataset.as_dict(sres="b1")["ensemble_90"]["NZ"]["2065"][10]
        self.assertEqual(res, 12.463586228230714)


class TestClimateAPI(unittest.TestCase):
    def setUp(self):
        self.api = wbpy.ClimateAPI()

class TestInstumentalFn(TestClimateAPI):
    def test_precip_type(self):
        locs = ["US", "GB"]
        dataset = self.api.get_instrumental("pr", "year", locs)
        self.assertTrue(dataset.api_call_date)

    def test_temp_type(self):
        locs = ["GBR"]
        dataset = self.api.get_instrumental("tas", "month", locs)
        self.assertEqual(dataset.as_dict()["GB"][0], 3.548619)

    def test_basin_location(self):
        locs = [302, "301"]
        dataset = self.api.get_instrumental("pr", "decade", locs)
        self.assertTrue(dataset.api_call_date)

    def test_multiple_locations(self):
        locs = ["GB", 302]
        dataset = self.api.get_instrumental("pr", "decade", locs)
        regions = [resp["region"][0] for resp in dataset.api_calls]
        self.assertIn("GB", regions)
        self.assertIn("302", regions)

@ddt
class TestModelledFn(TestClimateAPI):
    def test_precip_type(self):
        locs = ["US"]
        dataset = self.api.get_modelled("pr", "mavg", locs)
        self.assertTrue(dataset.as_dict())

    def test_temp_type(self):
        locs = ["AF"]
        dataset = self.api.get_modelled("tas", "mavg", locs)
        self.assertIn("tas", dataset.data_type)

    @data("ppt_days", "tmin_means", "ppt_days90th")
    def test_derived_statistic_type(self, stat):
        locs = ["AF", 303]
        dataset = self.api.get_modelled(stat, "mavg", locs)
        self.assertTrue(dataset.as_dict())

    def test_aavg_interval(self):
        locs = ["AF"]
        dataset = self.api.get_modelled("tas", "aavg", locs)
        self.assertTrue(dataset.as_dict())

    def test_manom_interval(self):
        locs = [302]
        dataset = self.api.get_modelled("tas", "manom", locs)
        self.assertTrue(dataset.as_dict())

    def test_aanom_interval(self):
        locs = ["AF"]
        dataset = self.api.get_modelled("tas", "aanom", locs)
        self.assertTrue(dataset.as_dict())

    def test_value(self):
        locs = ["nzl"]
        dataset = self.api.get_modelled("tmin_means", "mavg", locs)
        res = dataset.as_dict(sres="b1")
        self.assertEqual(res["ensemble_90"]["NZ"]["2065"][11],
            14.541015999650355)

    def test_bad_request_raises_exc(self):
        def bad_req():
            locs = ["GB", "303"]
            dataset = self.api.get_modelled("prr", "mavg", locs)

        self.assertRaises(AssertionError, bad_req)

    def test_multiple_locations(self):
        locs = ["GB", 302]
        dataset = self.api.get_modelled("pr", "aanom", locs)
        regions = [resp["region"][0] for resp in dataset.api_calls]
        self.assertIn("GB", regions)
        self.assertIn("302", regions)


class TestLocationCodes(TestClimateAPI):
    def test_alpha2_codes_work_as_location_arg(self):
        locs = ["GB"]
        dataset = self.api.get_modelled("tas", "aanom", locs)
        self.assertTrue(dataset.as_dict())

    def test_alpha3_codes_work_as_location_arg(self):
        locs = ["GBR"]
        dataset = self.api.get_modelled("tas", "aanom", locs)
        self.assertTrue(dataset.as_dict())

@ddt
class TestHasMetadata(TestClimateAPI):

    @data("instrumental_types", "modelled_types", "instrumental_intervals",
        "modelled_intervals")
    def test_metadata_attrs(self, attr_name):
        self.assertTrue(attr_name in self.api.ARG_DEFINITIONS)
