from datetime import datetime, date


DB2_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def extractTimeFromDB2DateTimeString(datetimeStr):
    """

    :param datetimeStr: DB2 datetime format. Example: 2020-12-28 15:45:00.000000
    :return: Time string. Format: HH:mm, Example: 15:45
    """
    timeStr = None
    try:
        parsedDate = datetime.strptime(datetimeStr, DB2_DATE_FORMAT)
        timeStr = parsedDate.strftime("%H:%M")
    except Exception as e:
        print(e)

    return timeStr


def extractDateFromDB2DateTimeString(datetimeStr):
    """

    :param datetimeStr: DB2 datetime format. Example: 2020-12-28 15:45:00.000000
    :return: Date string. Format: dd.MM.yyyy, Example: 28.12.2020
    """
    dateStr = None
    try:
        parsedDate = datetime.strptime(datetimeStr, DB2_DATE_FORMAT)
        dateStr = parsedDate.strftime("%d.%m.%Y")
    except Exception as e:
        print(e)

    return dateStr


def convertDateAndTimeToDB2DateTime(dateStr, timeStr):
    """

    :param dateStr: Date as string. Format dd.MM.yyyy, Example: 28.12.2020
    :param timeStr: Time as string. Format HH:mm, Example: 15:45
    :return: DB2 datetime format (e.g 2020-12-28 15:45:00.000000)
    """
    datetimeStr = None
    try:
        parsedDate = datetime.strptime(dateStr, "%d.%m.%Y")
        parsedTime = datetime.strptime(timeStr, "%H:%M")
        datetimeStr = parsedDate.strftime("%Y-%m-%d") + " " + parsedTime.strftime("%H:%M:%S.%f")
    except Exception as e:
        print(e)

    return datetimeStr


def html_date_time_2_DB2DateTime(html_date, time):
    datetimeStr = None
    try:
        parsedDate = datetime.strptime(html_date, "%Y-%m-%d")
        parsedTime = datetime.strptime(time, "%H:%M")
        datetimeStr = parsedDate.strftime("%Y-%m-%d") + " " + parsedTime.strftime("%H:%M:%S.%f")

    except Exception as e:
        print(e)

    return datetimeStr

def html_date_2_DB2DateTime(html_date):
    datetime_str = None
    try:
        parsed_date = datetime.strptime(html_date, "%Y-%m-%d")
        datetime_str = parsed_date.strftime("%Y-%m-%d %H:%M:%S.%f")
    except Exception as e:
        print(e)
    return datetime_str

def check_date_validity(d):
    parsed_date = datetime.strptime(d, "%Y-%m-%d").date()
    today = date.today()
    return parsed_date >= today



if __name__ == "__main__":
    print(extractDateFromDB2DateTimeString("2022-03-02 08:00:00.000000"))
    print(extractTimeFromDB2DateTimeString("2022-02-02 08:00:00.000000"))
    print(convertDateAndTimeToDB2DateTime("15.04.2022", "12:15"))
    print(html_date_time_2_DB2DateTime("2022-01-07","10:30"))
    print(check_date_validity("2022-01-06"))
    print(html_date_2_DB2DateTime("2022-01-06"))

