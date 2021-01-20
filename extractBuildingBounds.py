import overpy
import geojson as gj
from geojson_rewind import rewind
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import os

api = overpy.Overpass()
geolocator = Nominatim(user_agent="api.openindoor.io 4.0.0 contact contact@openindoor.io", timeout=1)
find_address = RateLimiter(geolocator.reverse, min_delay_seconds=1)
result = api.query("""(
  way['building']['level'] (48.0770, -1.7261, 48.1497, -1.5603);
  relation['building']['level'] (48.0770, -1.7261, 48.1497, -1.5603);
);
(._;>;);
out;""")
features_list = []
way_ids = []
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
    location = find_address(f"{feature['geometry']['coordinates'][0][0][0]}, "
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
    dumps = gj.dumps(feature_collection, ensure_ascii=False)
    rewind_dumps = rewind(dumps)
    with open (f'way_{way_id}.geojson', 'w') as file:
        file.write(rewind_dumps)
    print(f'Bounds of way with id {way_id} has been stored in geojson file...')







