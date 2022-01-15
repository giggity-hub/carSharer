import csv


def csv_reader(path):
    with open(path, "r") as csvfile:
        tmp = {}
        reader = csv.reader(csvfile, delimiter='=')
        for line in reader:
            tmp[line[0]] = line[1]
    return tmp


def clob2string(clob):
    if clob:
        return clob.getSubString(1, clob.length())
    else:
        return ""

def tuple2dict(tupel, columns):
    return dict(zip(columns, tupel))

def tupleList2dictList(tupelList, columns):
    return map(lambda t: tuple2dict(t, columns), tupelList)