"""Modify Atomic GeoJSON features."""

import utilities
import geojson


def remove_unused_properties(feature):
    """Return the feature without unused properties.

    :param feature: Identifier assigned to the object.
    :type feature: geojson.Feature
    """
    unused_props = [n for n, v in feature.properties.iteritems() if v == '']
    for property_name in unused_props:
        feature.properties.pop(property_name)
    return feature


def add_altitude_property(feature, height_offset=0.0):
    """Return the feature with updated elevation data.

    :param feature: Identifier assigned to the object.
    :type feature: geojson.Feature
    """
    if isinstance(feature.geometry, geojson.Point):
        lng, lat = feature.coordinates[0:2]
    elif isinstance(feature.geometry, geojson.LineString):
        coord1, coord2 = feature.coordinates[0:2]

        try:
            alt = utilities.get_altitude(lat, lng, height_offset)
            feature.geometry['coordinates'] = [lng, lat, alt]
        except:
            print('ERROR: Requesting altitude data')
    return feature


def normalize_precision(feature):
    """Return the feature with standardized precision coordinates.

    :param feature: Identifier assigned to the object.
    :type feature: geojson.Feature
    """
    def nomalized_precision(coordinates):
        """Normalize coordinates [x, y, z] to 10 to 11 cm of precision."""
        if len(coordinates) is 2:
            return [float('{:.6f}'.format(float(coordinates[0]))),
                    float('{:.6f}'.format(float(coordinates[1])))]

        elif len(coordinates) is 3:
            return [float('{:.6f}'.format(float(coordinates[0]))),
                    float('{:.6f}'.format(float(coordinates[1]))),
                    float('{:.1f}'.format(float(coordinates[2])))]

    if isinstance(feature.geometry, geojson.Point):
        coordinates = nomalized_precision(feature.geometry.coordinates)
        feature.geometry = geojson.Point(coordinates)

    elif isinstance(feature.geometry, geojson.LineString):
        coordinates0 = nomalized_precision(feature.geometry.coordinates[0])
        coordinates1 = nomalized_precision(feature.geometry.coordinates[1])
        feature.geometry = geojson.LineString((coordinates0, coordinates1))

    return feature


def add_length_property(feature):
    """Add a length to a feature if applicable"""
    if isinstance(feature.geometry, geojson.LineString):
        try:
            coords1, coords2 = feature.geometry.coordinates
        except:
            coords1, coords2 = '0.0,0.0', '0.0,0.0'

        length = utilities.distance(coords1, coords2)
        feature.properties['length'] = length
    return feature
