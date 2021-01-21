import overpy
from geojson_rewind import rewind
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import os
import json
import requests

def find_bounds_of_buildings(small_lat, small_lon, big_lat, big_lon):
    api = overpy.Overpass()
    API_KEY = 'test_Sk3dJIAbXvw7c7SwGzKpdP92nbZapEnScwMioWZK'
    headers = {
        'X-NTK-KEY': API_KEY,
    }
    url = 'https://api.nettoolkit.com/v1/geo/reverse-geocodes?'
    features_list = []
    way_ids = []
    result = api.query(f"""(
      way['building']['level']({small_lat}, {small_lon}, {big_lat}, {big_lon});
      relation['building']['level']({small_lat}, {small_lon}, {big_lat}, {big_lon});
    );
    (._;>;);
    out;""")

    for rel in result.relations:
        for member in rel.members:
            if isinstance(member, overpy.RelationWay):
                way = member.resolve()
                coordinates = []
                for node in way.nodes:
                    coordinates.append([float(node.lat), float(node.lon)])
                geometry = {
                        'type': 'Polygon',
                        'coordinates': [coordinates],
                }
                feature = {'type': 'Feature',
                           'properties': {
                               'id': way.id,
                               'country': '',
                               'city': '',
                               'name': '',
                           },
                           'geometry': geometry,
                           }
                features_list.append(feature)
                way_ids.append(way.id)

    for way in result.ways:
        if way.id in way_ids:
            continue
        else:
            coordinates = []
            for node in way.nodes:
                coordinates.append([float(node.lat), float(node.lon)])
            geometry = {
                'type': 'Polygon',
                'coordinates': [coordinates],
            }
            feature = {'type': 'Feature',
                       'properties': {
                           'id': way.id,
                           'country': '',
                           'city': '',
                           'name': '',
                       },
                       'geometry': geometry,
                       }
            features_list.append(feature)

    if 'out_files' not in os.listdir():
        os.mkdir('out_files')
    os.chdir('out_files')

    nodes_with_info = {}

    for feature in features_list:
        way_id = feature['properties']['id']
        for node in feature['geometry']['coordinates'][0]:
            lat = node[0]
            lon = node[1]
            if f'{lat}{lon}' in nodes_with_info:
                city = nodes_with_info[f'{lat}{lon}']['city']
                country = nodes_with_info[f'{lat}{lon}']['country']
                name = nodes_with_info[f'{lat}{lon}']['name']
            else:
                geocode_results = requests.get(url + f'latitude={lat}&longitude={lon}', headers=headers)
                jsson = json.loads(geocode_results.text)
                try:
                    city = jsson['results'][0]['city']
                    country = jsson['results'][0]['country']
                    name = f"Street: {jsson['results'][0]['street']}, house_number: {jsson['results'][0]['house_number']}"
                    node_info = {'city': city, 'country': country, 'name': name}
                    nodes_with_info[f'{lat}{lon}'] = node_info
                    break
                except:
                    continue
        feature['properties']['city'] = city
        feature['properties']['country'] = country
        feature['properties']['name'] = name
        feature_collection = {
            'type': 'FeatureCollection',
            'features': [feature],
        }
        rewinded_feature_collection = rewind(feature_collection)
        dump = json.dumps(rewinded_feature_collection, ensure_ascii=False)
        with open(f'way_{way_id}.geojson', 'w', encoding='utf-8') as file:
            file.write(dump)
        print(f'Bounds of way with id {way_id} has been stored in geojson file...')


coor_box_1 = ('40.6994', '-74.0241', '40.7445', '-73.9653') # New York, USA
coor_box_2 = ('48.0770', '-1.7261', '48.1497', '-1.5603') # Rennes, France

find_bounds_of_buildings(coor_box_1[0], coor_box_1[1], coor_box_1[2], coor_box_1[3])