from flask import Flask
from flask_restful import Api, Resource, reqparse, request
import overpy
import json
from geojson_rewind import rewind

app = Flask(__name__)
api = Api(app)


class GeoJson_API(Resource):

    def get_all_data_inside_bounds(self, bounds):
        api = overpy.Overpass()
        features_list = []
        ids = []
        feature_collection = {
            'type': 'FeatureCollection',
            'features': [],
        }
        result = api.query(f"""(
        node(poly:"{bounds.strip()}");
        way(poly:"{bounds.strip()}");>;
        relation(poly:"{bounds.strip()}");>;
        );
        out;""")

        for way in result.ways:
            coordinates = []
            for node in way.nodes:
                coordinates.append([float(node.lon), float(node.lat)])
            if coordinates[0] == coordinates[-1]:
                _type = "Polygon"
            else:
                _type = "LineString"
            geometry = {
                "type": _type,
                "coordinates": [coordinates],
            }
            feature = {
                "type": "Feature",
                "properties": way.tags,
                "geometry": geometry,
                "id": way.id,
            }
            features_list.append(feature)
            ids.append(way.id)

        for node in result.nodes:
            coordinates = [float(node.lon), float(node.lat)]
            geometry = {
                "type": "Point",
                "coordinates": coordinates,
            }
            feature = {
                "type": "Feature",
                "properties": node.tags,
                "geometry": geometry,
                "id": node.id,
            }
            features_list.append(feature)
            ids.append(node.id)

        for rel in result.relations:
            relation_tags = rel.tags
            for member in rel.members:
                resolved_member = member.resolve()
                if isinstance(member, overpy.RelationWay):
                    coordinates = []
                    nodes = resolved_member.nodes
                    for node in nodes:
                        coordinates.append([float(node.lon), float(node.lat)])
                    if coordinates[0] == coordinates[-1]:
                        _type = "Polygon"
                    else:
                        _type = "LineString"
                    geometry = {
                        "type": _type,
                        "coordinates": [coordinates],
                    }
                elif isinstance(member, overpy.RelationNode):
                    coordinates = [float(resolved_member.lon), float(resolved_member.lat)]
                    geometry = {
                        "type": "Point",
                        "coordinates": coordinates
                    }
                feature = {
                    "type": "Feature",
                    "properties": {**relation_tags, **resolved_member.tags},
                    "geometry": geometry,
                    "id": resolved_member.id,
                }
                features_list.append(feature)
                ids.append(resolved_member.id)

        for feature in features_list:
            feature_collection['features'].append(feature)

        #feature_collection_str = json.dumps(rewind(feature_collection))
        return feature_collection


    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("coordinates", type=list, action='append', required=True, help="Please define coordinates")
        args = parser.parse_args()
        coordinates_str = ""
        for coord in args['coordinates']:
            coordinates_str += str(coord[0]) + " " + str(coord[1]) + " "
        coordinates_str.strip()
        geojson_out = self.get_all_data_inside_bounds(coordinates_str)
        return geojson_out, 200

api.add_resource(GeoJson_API, '/get-data')

if __name__ == '__main__':
    app.run(debug=True)


