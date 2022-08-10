import main


def test_parse_date():
    assert "15:05" == main.parse_time(date_time_str='2020-01-12 15:05')


def test_parse_time():
    assert "12-01-2020" == main.parse_date(date_time_str='2020-01-12 15:05')
