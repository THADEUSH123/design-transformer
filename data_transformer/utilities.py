"""Simple utilities to manipulate geospatial data."""

from math import radians, cos, sin, atan2, sqrt
from time import sleep
import urllib
from simplejson import load
from collections import defaultdict


def get_altitude(lattitude, longitude, offset=0.0):
    """
    Convert a latitude and longitude into a list of x, y, z coordinates.

    NOTE: the geojson spec of x, y, z order (easting, northing,
    altitude for coordinates) and not lat, lng, alt.
    """
    coordinates = '{},{}'.format(lattitude, longitude)
    BASE_URL = 'http://maps.google.com/maps/api/elevation/json'
    url = BASE_URL + '?' + urllib.urlencode({'locations': coordinates})
    response = load(urllib.urlopen(url))['results'][0]['elevation']
    print('At {}, the altitude is {}'.format(coordinates, response))
    sleep(1)  # Play nice with the api and wait
    return float('{:.1f}'.format(offset + float(response)))


def distance(source_coordinates, destination_coordinates):
    """
    Return the distance in meters between two points.

    Accept coordinates in [x, y, z] or [lng, lat, alt]. Ignore altitude due to
    common accuracy issues.
    """
    lat1, long1 = (float(x) for x in source_coordinates[0:2])
    lat2, long2 = (float(x) for x in destination_coordinates[0:2])
    radius = 6371 * 1000  # radius of earth in meters
    dlat = radians(lat2 - lat1)
    dlon = radians(long2 - long1)
    a = sin(dlat / 2) * sin(dlat / 2) \
        + cos(radians(lat1)) * cos(radians(lat2)) \
        * sin(dlon / 2) * sin(dlon / 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    d = radius * c
    return float('{:.1f}'.format(d))


def calc_azimuth_elevation(source, destination):
    """Calculate the magnetic azimuth between two points."""
    pass


def normalize_edge_id(edge_name):
    """Normalize edge name based on naming convention."""
    edge_name = edge_name.strip('"')
    edge_name = edge_name.upper()
    return edge_name


def normalize_node_id(node_name):
    """Normalize node name based on naming convention."""
    node_name = node_name.strip('"')
    node_name = node_name.upper()
    return node_name


def get_adjacencies_by_proximity(edges, nodes):
    """Return a dict relationship of a graph.

    Based on the assumption that any node proximity( < 2m) of an
    edge endpoint is likely connected to the node / vertex.
    """

    prox_graph = defaultdict(list)
    for node in nodes:
        node_coords = node.geometry.coordinates
        for edge in edges:
            edge_coords1, edge_coords2 = edge.geometry.coordinates
            dist1 = distance(node_coords, edge_coords1)
            dist2 = distance(node_coords, edge_coords2)
            if (dist1 < 2) or (dist2 < 2):
                prox_graph[node.id].append(edge.id)

    return prox_graph


def get_adjacencies_by_ref(edges, nodes):
    """Return a dict relationship of a graph.

    Based on the assumption that all edge have stored reference to the
    connecting sites, return an adjacency list.
    """
    adjacency_list = defaultdict(list)
    for edge in edges:
        adjacency_list[edge.properties['source_id']].append(edge.id)
        adjacency_list[edge.properties['destination_id']].append(edge.id)

    return adjacency_list


def get_adjacencies(edges, nodes):
    """Wrap the two adjacency identification functions.

    Under normal insertions, all edges will contain a reference to the source
    and destination of the edge. This will be faster to calc than the proximity
    method, which calculates the distance to all sites.
    """
    try:
        return get_adjacencies_by_ref(edges, nodes)

    except:
        print('Fast adjacency identification method failed. This may take some'
              'time.')
        return get_adjacencies_by_proximity(edges, nodes)


def hash_location(coordinates):
    """Unique hash to identify a 1m by 1m by 1m space on the earth.

    Any lat, long, height combination with the given precision will be a
    unique hash.
    """
    if len(coordinates) == 3:
        lat, lng, height = coordinates
    elif len(coordinates) == 2:
        lat, lng = coordinates
        height = 0.0

    return '{:.5f}_{:.5f}_{:.0f}'.format(lat, lng, height)


def find_close_nodes(nodes):
    """Identify nodes that are within ~1m distance of each other.

    Useful for identifying locations that may represent the same physical
    location.
    """
    location_map = defaultdict(list)
    close_nodes = []
    for node in nodes:
        location_map[hash_location(node.geometry.coordinates)].append(node.id)

    for (loc, ids) in location_map.iteritems():
        if len(ids) >= 2:
            close_nodes.append(tuple(ids))

    return close_nodes


def get_missing_fields(edges, nodes):
    """Find missing fields in the data."""
    expected_node_fields = ['bill_of_materials', 'status']
    expected_edge_fields = ['length']
    data_gaps = {}
    for node in nodes:
        missing_node_data = [key for key in expected_node_fields
                             if key not in node.properties.keys()]
        data_gaps[node.id] = missing_node_data

    for edge in edges:
        missing_edge_data = [key for key in expected_edge_fields
                             if key not in edge.properties.keys()]
        data_gaps[edge.id] = missing_edge_data

    return data_gaps


def get_edges_per_node(edges, nodes):
    """Get edges attatched to a node in the graph."""
    edges_per_node = defaultdict(int)
    adjacency_list = get_adjacencies(edges=edges, nodes=nodes)
    for adjacentcies in adjacency_list.values():
        edges_per_node[len(adjacentcies)] += 1
    return edges_per_node
