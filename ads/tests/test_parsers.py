from .. import parser as parse

def test_date_parser():

    assert parse.dates(2002)                == " year:[2002 TO 2002]"
    assert parse.dates(2002.)               == " year:[2002 TO 2002]"
    assert parse.dates("2002")              == " year:[2002 TO 2002]"
    assert parse.dates("2002-07")           == " year:[2002-07 TO 2002-07]"
    assert parse.dates("2002-07-15")        == " year:[2002-07 TO 2002-07]"
    assert parse.dates("2002/07")           == " year:[2002-07 TO 2002-07]"
    assert parse.dates("2002..2005")        == " year:[2002-01 TO 2005-12]"
    assert parse.dates("2002..05")          == " year:[2002-01 TO 2005-12]"
    assert parse.dates("2002-01..2006/07")  == " year:[2002-01 TO 2006-07]"
    assert parse.dates((2002, 2005))        == " year:[2002-01 TO 2005-12]"
    assert parse.dates((2002, 2005))        == " year:[2002-01 TO 2005-12]"
    assert parse.dates((2002, ))            == " year:[2002-01 TO *]"
    assert parse.dates((None, 2002))        == " year:[* TO 2002-12]"
    assert parse.dates(2002.02)             == " year:[2002-02 TO 2002-02]"
    assert parse.dates("2002/05..08")       == " year:[2002-05 TO 2008-12]"
    assert parse.dates("2002-")             == " year:[2002-01 TO *]"
    assert parse.dates("2002..")            == " year:[2002-01 TO *]"
    assert parse.dates("..2002")            == " year:[* TO 2002-12]"
    assert parse.dates("-2002")             == " year:[* TO 2002-12]"
