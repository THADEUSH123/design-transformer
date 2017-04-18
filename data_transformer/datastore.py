"""
Working data storage.

Load and export serialized data in text documents from python objects and vic
versa. Also provides helper functions to manage Feature objects.
"""
import csv
import geojson
import utilities
import os
import pydot


class Datastore(dict):
    """
    Manage data from local files and online files in a pythonic way.

    The Datastore class manages deployment data and exposes the data in
    native python objects thatgeojson. The class could be extended to
    support database repositories.

    """

    def __init__(self):
        """Initilize the the Datastore class."""
        super(Datastore, self).__init__()

    @property
    def sites(self):
        """Return all sites in the datastore."""
        return [f for f in self.values() if isinstance(f, Site)]

    @property
    def links(self):
        """Return all links in the datastore."""
        return [f for f in self.values() if isinstance(f, Link)]

    @property
    def all(self):
        """Return all sites and links in the datastore."""
        return [f for f in self.values()]

    @property
    def all_connected(self):
        """Return only sites and links in the datastore that are associated."""
        adjacencies = utilities.get_adjacencies(
            edges=[l.as_geojson() for l in self.links],
            nodes=[s.as_geojson() for s in self.sites])
        return [s for s in self.sites if s.id in adjacencies]

    def add(self, raw_data):
        """Validate and add raw_data to the Datastore set.

        This performs input validation of raw data. The dictionary should never
        be accessed directly because it cannot manage data wights during time
        of input.
        :param raw_data: raw_data to add to the store
        :type raw_data: a dict of keys
        :returns: 1 if successful and 0 if unsuccessful
        """
        if raw_data['data_type'] == 'site':
            site = self.get(raw_data.get('site_id', 'unknown').upper(), Site())
            self[site.id] = site.update_raw_data(raw_data)
            return 1
        elif raw_data['data_type'] is 'link':
            # TODO: Implement better handeling of weighted link data.
            try:
                source_site = self[Site.normalize_id(raw_data['source_id'])]
            except:
                print('  Source Error:{} is not defined within the data set'
                      ''.format(raw_data['source_id']))
                return 0
            try:
                destination_site = self[raw_data['destination_id']]

            except:
                print('  Destination Error: {} is not defined within the data '
                      'set'.format(raw_data['destination_id']))
                return 0

            link = Link(source_site=source_site,
                        destination_site=destination_site)
            self[link.id] = link.update_raw_data(raw_data)
            return 1
        return 0

    def update_all_properties(self):
        """Traverse the DataStore and add/update properties."""
        adjacencies = utilities.get_adjacencies(
            edges=[l.as_geojson() for l in self.links],
            nodes=[s.as_geojson() for s in self.sites])

        for site in self.all_connected:
            updates = {'connected_links': ', '.join(adjacencies[site.id])}
            self[site.id] = site.update_raw_data(updates)

        for link in self.links:
            try:
                coords1, coords2 = link.as_geojson().geometry.coordinates
            except:
                coords1, coords2 = '0.0,0.0', '0.0,0.0'

            updates = {'link_id': link.id,
                       'length': utilities.distance(coords1, coords2)}
            self[link.id] = link.update_raw_data(updates)

    def load_geojson_file(self, file_path):
        """Load a FeatureCollection from a single geojson document."""
        loads = 0
        file_name = os.path.basename(file_path)
        with open(file_path, 'r') as f:
            features1 = geojson.loads(f.read())
            if geojson.is_valid(features1)['valid'] == 'yes':
                for feature in features1:
                    loads += self.add(feature)
        print('  Loaded {} sites from {}'.format(loads, file_name))
        print('  Failed to load json file. Def not complete.')

    def load_csv_file(self, file_path):
        """Load features from single csv document."""
        loads = 0
        file_name = os.path.basename(file_path)
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row_data in reader:
                row_data['data_source'] = file_name
                row_data['data_type'] = 'site'
                loads += self.add(row_data)

        print('  Loaded {} sites from {}'.format(loads, file_name))

    def load_gv_file(self, file_path):
        """Load features from single gv document."""
        edge_loads = 0
        node_loads = 0
        try:
            graphs = pydot.graph_from_dot_file(file_path)
        except:
            print('  Error: Unable to interpret .gv file. Please review.')

        graph = graphs[0]  # TODO: Implement multiple graphs in one file.
        file_name = os.path.basename(file_path)
        for node in graph.get_node_list():
            node_loads += 1
            # TODO: Implement passing site info via graphvis format.

        for edge in graph.get_edge_list():
            data = {
                'data_type': 'link',
                'data_source': file_name,
                'source_id': Site.normalize_id(edge.get_source()),
                'destination_id': Site.normalize_id(edge.get_destination())}

            edge_loads += self.add(data)
        print('  Loaded {} links from {}'.format(edge_loads, file_name))

    def import_all_files(self, folder, files_names):
        """Wrapper function to import all provided files."""
        files_names.sort(key=lambda f: os.path.splitext(f)[1])
        for f in files_names:
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


class Site(object):
    """Atomic object representing a physiscal site.

    A site is a physical place that is approximtly 5m X 5m.
    """

    _mandatory_properties = {'bill_of_materials': 'Unknown',
                             'status': 'Unknown',
                             'data_type': 'site'}

    def __init__(self):
        """Initilize the Site object."""
        self._data_weights = {}
        self._data = Site._mandatory_properties.copy()

    @staticmethod
    def normalize_id(site_name):
        """Normalize site name based on standard convention."""
        return site_name.upper().strip('"').strip()

    @property
    def id(self):
        """Normalized ID of the site.

        This method can be used to clean up eroneouse naming conventions of
        unique identifiers.
        """
        if 'id' in self._data:
            self._data['site_id'] = self._data['id']
            self._data.pop('id', None)
        if 'site_id' in self._data:
            return Site.normalize_id(self._data['site_id'])
        return 'unknown'

    @property
    def latitude(self):
        """Latitude of the center point of the site with 1m of precision."""
        try:
            return float('{:.6f}'.format(float(self._data['latitude'])))
        except:
            return 0.0

    @property
    def longitude(self):
        """Longitude of the center point of the site with 1m of precision."""
        try:
            return float('{:.6f}'.format(float(self._data['longitude'])))
        except:
            return 0.0

    def as_geojson(self):
        """Return the site data as a geoJSON feature object."""
        properties = {k: v for k, v in self._data.items()
                      if k not in ['longitude', 'latitude']}

        return geojson.Feature(id=self.id,
                               geometry=geojson.Point((self.longitude,
                                                       self.latitude)),
                               properties=properties)

    def update_raw_data(self, raw_data):
        """Update the site with the appropriate data.

        Take raw_data weight into consideration for which fields should be
        updated to new values.
        """
        input_data_weight = int(raw_data.get('data_weight', 0))
        raw_data = {k: v for k, v in raw_data.items() if v != ''}
        for (column_name, value) in raw_data.iteritems():
            # Normalize all input data fields.
            column_name = column_name.lower().replace(' ', '_').strip()

            if input_data_weight >= self._data_weights.get(column_name, 0):
                self._data_weights[column_name] = input_data_weight
                self._data.update({column_name: value})

        return self


class Link(object):
    """Atomic link object.

    This object represents a link between two sites.
    """
    _mandatory_properties = {'status': 'unknown',
                             'source_id': 'unknown',
                             'destination_id': 'unknown'}

    def __init__(self, source_site, destination_site):
        """Initilize the Link object."""
        self._data_weights = {}
        self._data = Link._mandatory_properties.copy()
        self._source_site, self._destination_site = \
            sorted([source_site, destination_site], key=lambda x: x.id)

    @property
    def id(self):
        return '{}_{}'.format(self._source_site.id, self._destination_site.id)

    def as_geojson(self):
        """Return the link data as a geoJSON feature object."""

        properties = {k: v for k, v in self._data.items()
                      if k not in ['longitude', 'latitude']}

        properties.update({'source_id': self._source_site.id,
                           'destination_id': self._destination_site.id})

        line = geojson.LineString(((self._source_site.longitude,
                                    self._source_site.latitude),
                                   (self._destination_site.longitude,
                                    self._destination_site.latitude)))

        return geojson.Feature(id=self.id,
                               geometry=line,
                               properties=properties)

    def update_raw_data(self, raw_data):
        """Update the link with the appropriate data.

        Take raw_data weight into consideration for which fields should be
        updated to new values.
        """
        input_data_weight = int(raw_data.get('data_weight', 0))
        raw_data = {k: v for k, v in raw_data.items() if v != ''}
        for (column_name, value) in raw_data.iteritems():
            # Normalize all input data fields.
            column_name = column_name.lower().replace(' ', '_').strip()

            if input_data_weight >= self._data_weights.get(column_name, 0):
                self._data_weights[column_name] = input_data_weight
                self._data.update({column_name: value})

        return self
