from unwetter.generate import title

from ..assets import events


def test_title_alert_simple():
    assert title(events['alert_1']) == '🚨 Neue Meldung: Amtliche WARNUNG vor GLÄTTE'


def test_title_alert_simple_wina():
    assert (title(events['alert_1'], variant='wina_headline')
            == 'DETAILS zur amtlichen UNWETTERWARNUNG für NORDRHEIN-WESTFALEN des DWD')
