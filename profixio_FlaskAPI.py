#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
import os, sys
import urllib2
import json
from bs4 import BeautifulSoup
from flask import request, url_for, jsonify
from flask_api import FlaskAPI, status, exceptions
#from collections import OrderedDict
from collections import OrderedDict

app = FlaskAPI(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["JSON_AS_ASCII"] = True

#base_app_route = '/api/profixio/divisions'
base_app_route = '/api/profixio'

# Index-service
@app.route('/')
def index():
    return {"api" : base_app_route + "/<division>", "mock" : "/mockapi/profixio/[girlz|boyz]" }

#Mock-service for endpoint-User
@app.route('/mockapi/profixio/<division>', methods=['GET'])
def mock_standings(division):
    print "Mock division: " + str(division)
    if division == 'girlz':
        mock_file = 'examples/girlz_Stockholm-Korpen_2017_standings.json'
    elif division == 'boyz':
        mock_file  = 'examples/boyz_Stockholm-Korpen_2017_standings.json'
    else:
        mock_file =  'examples/valid_mocks.json'

    with open(mock_file, 'r') as file:
        json_data = file.read()

    print json_data
    response = json.loads(json_data, object_pairs_hook=OrderedDict)
    print response
    #response = OrderedDict()

    return jsonify(response)

#Main API-path. Find your division (t=(.*)) exploring profixio.com and add as parameter to API-call
   #https://www.profixio.com/fx/serieoppsett.php?t=Korpen_SERIE_AVD8015&k=LS8015&p=1
      # ==> Korpen_SERIE_AVD8015&k=LS8015&p=1
      # ./api/profixio/Korpen_SERIE_AVD8015&k=LS8015&p=1


@app.route(base_app_route, methods=['GET'])
def get_divisions():
    return {"implemented" : "not"}


@app.route(base_app_route + '/<division>', methods=['GET'])
def get_division(division):
    division_page = get_profixio_page(division)
    for element in division_page:
        division_header = element.find('h3').get_text().encode('utf-8')
    return jsonify({'name' : division_header})


@app.route(base_app_route + '/<division>/standings', methods=['GET'])
def get_standings(division):
    #print request.get_json()
    division_page = get_profixio_page(division)
    division_table_html = get_division_table_html(division_page)
    division_table_json = html_to_json_table(division_table_html)
    return jsonify(division_table_json)

@app.route(base_app_route + '/<division>/fixtures', methods=['GET'])
def get_omgangar(division):
    return {"implemented" : "not"}



def get_profixio_page(division):
    req = urllib2.Request('https://www.profixio.com/fx/serieoppsett.php?t=' + division, headers={ 'User-Agent': 'Mozilla/5.0' })
    division_soup = BeautifulSoup(urllib2.urlopen(req).read(), "html.parser")
    return  division_soup


def get_division_table_html(division_page):
    main_div = division_page.find_all("div", class_="col-sm-9 col-lg-10")
    return main_div


def html_to_json_table(html_table):
    for element in html_table:
        json_table = get_standings(element.find('table', id='tabell_std'))

    return json_table

def get_standings(html_table):
    #print "\n\nhtml_table\n"

    #Order på önskad output. rank saknas, adderas senare.
    order = ["team", "rank", "gamesPlayed", "wins", "draws", "losses", "goals", "points"]
    table_header_values = "Lag", 0, "S", "V", "O", "F", "Mål", "P"
    print table_header_values
    standings_table_header = OrderedDict(zip(order, table_header_values))
    standings_table = [standings_table_header]

    order.remove("rank")
    table_data = [[cell.text for cell in row("td")]
        for i, row in enumerate(html_table("tr")) if i > 0]

    for lag in table_data:
        print "lag = " + str(lag)
        has_expired = True
        lag_thingy = OrderedDict()
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
