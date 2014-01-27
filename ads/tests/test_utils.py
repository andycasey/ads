# coding: utf-8

""" Test ADS utilities """

from __future__ import division, print_function

__author__ = "Andy Casey <andy@astrowizici.st>"

import ads

def test_get_api_setting():

    settings = ads.utils.get_api_settings()
    assert settings
    assert len(settings["allowed_fields"]) > 0
    assert settings["max_rows"] >= 200


def test_unique_preserved_list():

    assert ads.utils.unique_preserved_list([1,2,3]) == [1,2,3]
    assert ads.utils.unique_preserved_list([1,2,3,4,'4']) == [1,2,3,4,'4']
    assert ads.utils.unique_preserved_list([1,2,3,3,4,5]) == [1,2,3,4,5]
    assert ads.utils.unique_preserved_list([2,1,2,2,2,3,2]) == [2,1,3]

    