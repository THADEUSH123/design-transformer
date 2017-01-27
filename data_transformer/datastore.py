"""
Working data storage.

Load and export serialized data in text documents from python objects and vic
versa. Also provides helper functions to manage Feature objects.
"""
import csv
import geojson
import features
import utilities
import os
import pydot


class Datastore(object):
    """
    Manage data from local files and online files in a pythonic way.

    The Datastore class manages deployment data and exposes the data in
    native python objects(geojson.Features). The class can be extended to
    support various file types and repositories.

    """

    def __init__(self):
        """init geojson.Features that are stored in the Datastore class."""
        self._data = {}
        self._weighting = {}

    def __getattr__(self, name):
        """Return geospatial data in the Datastore class.

        Perform simple filtering of object types for easy manipultion.
        Always return a list of data of the specific type.
        """
        if name is 'sites':
            return [f for f in self._data.values()
                    if f.properties['subtype'] == 'site']
        elif name is 'mountpoints':
            return [f for f in self._data.values()
                    if f.properties['subtype'] == 'mountpoint']
        elif name is 'links':
            return [f for f in self._data.values()
                    if f.properties['subtype'] == 'link']
        elif name is 'all':
            return [f for f in self._data.values()]
        else:
            raise AttributeError

    def get(self, key, default=None):
        """Dict get method.

        Return data requests by wrapping the internal dict.
        """
        return self._data.get(key, default)

    def add(self, data):
        """Validate and add data to the Datastore set.

        This performs input validation of raw data. self._data should never be
        accessed directly because it cannot manage data wights during time of
        input.
        :param data: data to add to the store
        :type data: a dict of keys
        :returns: 1 if successful and 0 if unsuccessful
        """

        if 'site_id' in data:
            try:
                lng = float(data.get('longitude', '0.0'))
            except:
                lng = 0.0
            try:
                lat = float(data.get('latitude', '0.0'))
            except:
                lat = 0.0
            new_site = geojson.Feature(
                id=utilities.normalize_node_id(data['site_id']),
                geometry=geojson.Point((lng, lat)),
                properties=data)
            feature = new_site
        else:
            feature = data

        identitifier = feature.get('id', 'unknown_id')
        if not isinstance(feature, geojson.Feature):
            print('  Failed to load {}: not properly formated'
                  .format(identitifier))
            return 0

        if feature.properties.get('subtype', None) not in ['site', 'link']:
            print('  Failed to load {}: subtype is undefined'
                  .format(identitifier))
            return 0
        data_weight = int(feature.properties.get('data_weight', 0))
        exsisting_feature = self._data.get(identitifier, None)
        if exsisting_feature is None:
            self._data[identitifier] = feature
            self._weighting[identitifier] = \
                {f: data_weight for f in feature.properties.keys()}

            return 1

        else:
            updates = {}
            prop_weights = self._weighting[identitifier]
            for prop_name, prop_val in feature.properties.items():
                if prop_weights.get(prop_name, -100000) <= data_weight:
                    prop_weights[prop_name] = data_weight
                    updates[prop_name] = prop_val

            exsisting_feature.properties.update(updates)
            self._data[identitifier] = exsisting_feature
            return 1

    def update_all_properties(self):
        """Traverse the DataStore and add/update properties."""
        adjacencies = utilities.get_adjacencies(edges=self.links,
                                                nodes=self.sites)

        for feature in self.all:
            feature = features.add_length_property(feature)
            feature = features.remove_unused_properties(feature)
            feature = features.normalize_precision(feature)
            if isinstance(feature.geometry, geojson.Point):
                updates = {'connected_links': ', '.join(
                    adjacencies[feature.id])}
                feature.properties.update(updates)
            self.add(feature)

    def load_geojson_file(self, file_path):
        """Load a FeatureCollection from a single geojson document."""
        loads = 0
        file_name = os.path.basename(file_path)
        with open(file_path, 'r') as f:
            features = geojson.loads(f.read())
            if geojson.is_valid(features)['valid'] == 'yes':
                for feature in features:
                    loads += self.add(feature)
        print('  Loaded {} sites from {}'.format(loads, file_name))
        print('  Failed to load json file. Def not complete.')

    def load_csv_file(self, file_path):
        """Load features from single csv document."""
        loads = 0
        file_name = os.path.basename(file_path)
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['data_source'] = file_name
                row['data_type'] = 'site'
                row['subtype'] = 'site'
                if 'data_weight' not in row:
                    row['data_weight'] = '0'
                loads += self.add(row)

            print('  Loaded {} sites from {}'.format(loads, file_name))

    def load_gv_file(self, file_path, weight=None):
        """Load features from single gv document."""
        edge_loads = 0
        node_loads = 0
        try:
            graphs = pydot.graph_from_dot_file(file_path)
        except:
            print('  Error: Unable to interpret gv file.')
        graph = graphs[0]

        file_name = os.path.basename(file_path)

        for node in graph.get_node_list():
            node_loads += 1
            pass  # TODO: Implement passing site info via graphvis format.

        for edge in graph.get_edge_list():
            source_id = utilities.normalize_node_id(edge.get_source())
            destination_id = utilities.normalize_node_id(
                edge.get_destination())
            source = self.get(source_id, None)
            destination = self.get(destination_id, None)

            if (source is not None) and (destination is not None):
                line_string = geojson.LineString(
                    (source.geometry.coordinates,
                     destination.geometry.coordinates))
                new_link = geojson.Feature(
                    id='_'.join(sorted([source.id, destination.id])),
                    geometry=line_string,
                    properties={'data_source': file_name,
                                'subtype': 'link',
                                'source_id': source_id,
                                'destination_id': destination_id})

                edge_loads += self.add(new_link)

            else:
                if source is None:
                    print('  Source Error:{} is not defined as a site within '
                          'the data set'.format(source_id))
                if destination is None:
                    print('  Destination Error: {} is not defined as a site '
                          'within the data set'.format(destination_id))
        print('  Loaded {} links from {}'.format(edge_loads, file_name))

    def import_all_files(self, folder, files_names):
        """Wrapper function to import all provided files."""
        for f in sorted(files_names, key=lambda x: x.split("."))[::-1]:
            path = os.path.join(folder, f)
            if path.endswith('.csv'):
                self.load_csv_file(path)
            elif path.endswith(('.json', '.geojson')):
                self.load_geojson_file(path)
            elif path.endswith('.gv'):
                self.load_gv_file(path)
            else:
                print('File format not supported for {}'.format(f))
        print('\nImports complete!')
