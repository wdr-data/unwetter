from unwetter import dwd

from .assets import xmls, alert_1


def test_parse_xml_alert_simple():
    expected = alert_1.event

    assert dwd.parse_xml(xmls["alert_1"]) == expected
