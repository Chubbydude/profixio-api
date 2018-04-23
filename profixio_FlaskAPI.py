#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
import os, sys
import urllib2
import json
from bs4 import BeautifulSoup
from flask import request, url_for, jsonify
from flask_api import FlaskAPI, status, exceptions
#from collections import OrderedDict
import collections

app = FlaskAPI(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["JSON_AS_ASCII"] = True

@app.route('/')
def index():
    return {"goto" : "/api/profixio/<division>"}

#Mock-service for test usage
@app.route('/mockapi/profixio/<division>', methods=['GET'])
def mock_standings(division):
    with open('examples/girlz-standing-2017-WP-formated.json', 'r') as file:
        json_data = file.read()
        response = json.loads(json_data)

    return jsonify(response)

#Main API-path. Find your division (t=(.*)) exploring profixio.com and add as parameter to API-call
   #https://www.profixio.com/fx/serieoppsett.php?t=Korpen_SERIE_AVD8015&k=LS8015&p=1
      # ==> Korpen_SERIE_AVD8015&k=LS8015&p=1
      # ./api/profixio/Korpen_SERIE_AVD8015&k=LS8015&p=1
@app.route('/api/profixio/<division>', methods=['GET'])
def get_standings(division):
    #print request.get_json()
    response = get_table(division)
    print response
    return jsonify(response)

def get_table(division):
    req = urllib2.Request('https://www.profixio.com/fx/serieoppsett.php?t=' + division, headers={ 'User-Agent': 'Mozilla/5.0' })

    #req = urllib2.Request('https://www.profixio.com/fx/serieoppsett.php?t=Korpen_SERIE_AVD8015&k=LS8015&p=1', headers={ 'User-Agent': 'Mozilla/5.0' })
    soup = BeautifulSoup(urllib2.urlopen(req).read(), "html.parser")

    main_div = soup.find_all("div", class_="col-sm-9 col-lg-10")
    #print type(maindiv)
    #print "\n\nmaindiv\n" + str(maindiv)

    for element in main_div:
        division = element.find('h3').get_text().encode('utf-8')
        tabell_std_json = table_to_json(element.find('table', id='tabell_std'))

    return tabell_std_json

def table_to_json(html_table):
    #print "\n\nhtml_table\n"
    #print type(html_table)
    order = ["team", "rank", "gamesPlayed", "wins", "draws", "losses", "goals", "points"]
    table_header_values = "Lag", 0, "Spelade", "Vinster", "Oavgjorda", "Förluster", "Mål", "Poäng"
    print table_header_values
    standings_table_header = collections.OrderedDict(zip(order, table_header_values))
    standings_table = [standings_table_header]



    order.remove("rank")
    table_data = [[cell.text for cell in row("td")]
        for i, row in enumerate(html_table("tr")) if i > 0]

    for lag in table_data:
        print "lag = " + str(lag)
        has_expired = True
        lag_thingy = collections.OrderedDict()
        if len(lag) < len(order):
            has_expired = True
        for i, thing in enumerate(order):
            try:
                #print "i = " + str(i) +" thing = " + str(thing)
                if i == 0:
                    rank, team = lag[i].split(" ", 1)
                    lag_thingy['team'] = team
                    lag_thingy['rank'] = int(rank.replace(".", ""))
                else:
                    lag_thingy[thing] = lag[i]
            except Exception as e:
                print e
                if has_expired:
                    lag_thingy[thing] = "-"
        #print lag_thingy
        standings_table.append(lag_thingy)
        #print standings_table
    #[x.encode('utf-8') for x in standings_table]
    return standings_table

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    if port == 5000:
        app.debug = True

    app.run(host='0.0.0.0', port=port)
