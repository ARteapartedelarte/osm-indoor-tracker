import overpy
from geojson_rewind import rewind
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import os
import json


def find_bounds_of_buildings(small_lat, small_lon, big_lat, big_lon):
    api = overpy.Overpass()
    geolocator = Nominatim(user_agent="api.openindoor.io 4.0.0 contact contact@openindoor.io", timeout=2)
    rate_limiter = RateLimiter(geolocator.reverse, min_delay_seconds=1)
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

    for feature in features_list:
        way_id = feature['properties']['id']
        location = rate_limiter(f"{feature['geometry']['coordinates'][0][0][0]}, "
                                f"{feature['geometry']['coordinates'][0][0][1]}")
        address_items = list(location.raw['address'].items())
        name = address_items[0][1] + ' - ' + address_items[0][0] + ', ' + address_items[1][1] + ' - ' + address_items[1][0]
        if 'city' in location.raw['address']:
            city = location.raw['address']['city']
        elif 'town' in location.raw['address']:
            city = location.raw['address']['town']
        else:
            city = location.raw['address']['municipality']
        country = location.raw['address']['country']
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

find_bounds_of_buildings(coor_box_2[0], coor_box_2[1], coor_box_2[2], coor_box_2[3])



