import requests
from bs4 import BeautifulSoup
import re
import csv
import time
import random

base = 'https://www.techpowerup.com'
fieldnames = ['model', 'TDP', 'core_units', 'manufacturer',
              'family', 'manufacture_date', 'process', 'die_size', 'source']


def write_csv(path, dicts):
    with open(path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dicts)


def compute_die_size(string):
    # this is to account for die sizes found in the form 4x 78 mm²
    m = re.match("(?:(\d)+x )?(\d+)", string)
    base = float(m[2])
    if m[1]:
        return float(m[1]) * base
    return base


def find_die_size(body):
    return sum(compute_die_size(n.parent.find_next_sibling().string)
               for n in body.find_all(string=re.compile("Die Size:")))


def cpu_info(a):
    siblings = a.parent.find_next_siblings()
    manufacturer = "Intel" if a.parent.find_previous(string="Intel") else "AMD"
    family = siblings[0].string
    core_units = re.match("\d+", siblings[1].string)[0]
    process = re.match("\d+", siblings[4].string)[0]
    TDP = re.match("\d+", siblings[6].string)[0]
    date = re.search("(\d+)$", siblings[7].string)[1]
    return (base + a["href"], a.string.strip(), manufacturer, family, core_units, process, TDP, date)


def get_tuples():
    page = requests.get(
        base + '/cpu-specs/?mobile=No&sort=name')

    soup = BeautifulSoup(page.content, 'html.parser')

    return [cpu_info(a) for a in soup.body.find(
        class_="page").find(id="list").table.find_all("a")]


def get_cpus():
    tuples = get_tuples()
    dicts = []
    for (link, name, manufacturer, family, core_units, process, TDP, date) in tuples:
        page = requests.get(link)
        soup = BeautifulSoup(page.content, 'html.parser')
        print(link)
        test = soup.body.find(class_="page")
        if test:
            physical = test.div.find(
                string="Physical").parent.find_next_sibling()
            die_size = find_die_size(physical)
            dicts.append({'model': name, 'TDP': TDP, 'core_units': core_units, 'manufacturer': manufacturer, 'family': family, 'manufacture_date': date,
                          'process': process, 'die_size': die_size, 'source': link})
            time.sleep(random.uniform(4, 6))

    write_csv('boaviztapi/data/components/cpu_infos.csv', dicts)


# get_cpus()

tuples = get_tuples()
dicts = [{'model': name, 'TDP': TDP, 'core_units': core_units, 'manufacturer': manufacturer, 'family': family, 'manufacture_date': date,
          'process': process, 'die_size': -1, 'source': link} for (link, name, manufacturer, family, core_units, process, TDP, date) in tuples]
write_csv('boaviztapi/data/components/cpu_infos.csv', dicts)
