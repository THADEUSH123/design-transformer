"""Provide misc reports.

Export formats for various information.
"""

import csv
import lxml
import geojson
from pykml.parser import Schema
from pykml.factory import KML_ElementMaker as KML
import datetime
import collections
import utilities
import os


def export_all_files(to_folder, sites, links):
    """Wrap all other report functions for exporting files."""
    # TODO: Refactor the as_geojson to align with the new classes in datastore.
    sites = [s.as_geojson() for s in sites]
    links = [l.as_geojson() for l in links]
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    folder_path = os.path.join(to_folder, current_date)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    adjacencies = utilities.get_adjacencies(edges=links, nodes=sites)
    connected_sites = [site for site in sites if site.id in adjacencies.keys()]

    with open(os.path.join(folder_path, 'summary.txt'), 'w') as f:
        f.write(export_basic_report(sites=sites, links=links))

    with open(os.path.join(folder_path, 'data_issues.txt'), 'w') as f:
        f.write(export_data_issues_report(sites=sites, links=links))

    with open(os.path.join(folder_path, 'design_layout.geojson'), 'w') as f:
        f.write(export_to_geojson(sites=connected_sites, links=links))

    export_sites_to_csv(
        file_path=os.path.join(folder_path, 'aggregated_site_data.csv'),
        sites=sites)

    with open(os.path.join(folder_path, 'design_layout.kml'), 'w') as f:
            f.write(export_to_kml(sites=connected_sites, links=links))

    print('\nExports complete!')


def export_basic_report(sites, links):
    """Build a report based on sub reports."""
    adjacency_list = utilities.get_adjacencies(edges=links, nodes=sites)
    connected_sites = [site for site in sites
                       if site.id in adjacency_list.keys()]

    return (data_summary_report(sites=connected_sites, links=links) +
            design_analysis_report(sites=connected_sites, links=links) +
            material_requirements_report(sites=connected_sites))


def export_data_issues_report(sites, links):
    """Build a report based on sub reports."""
    adjacency_list = utilities.get_adjacencies(edges=links, nodes=sites)
    connected_sites = [site for site in sites
                       if site.id in adjacency_list.keys()]

    return (proximity_issue_report(sites=connected_sites, links=links) +
            missing_data_fields_report(sites=connected_sites, links=links))


def data_summary_report(sites, links):
    """Generate a report to communicate basic data imported."""
    return ('\n==Data Summary==\n'
            '  {total_num_sites} unique sites imported.\n'
            '  {total_num_links} unique links imported.\n'
            ''.format(total_num_sites=len(sites),
                      total_num_links=len(links)))


def design_analysis_report(sites, links):
    """Generate a report to communicate design related data."""
    links_per_pole = utilities.get_edges_per_node(edges=links, nodes=sites)

    link_count_display = ''
    for link_counts in links_per_pole.iteritems():
        link_count_display += '    {} link sites: {}\n'.format(*link_counts)

    avg_links_per_site = float(len(links))/float(len(sites)) * 2

    link_lengths = []
    for link in links:
        link_length = link.properties['length']
        link_lengths.append(link_length)

    num_short_links = len([l for l in link_lengths if l < 100 and l > 0])
    num_med_links = len([l for l in link_lengths if l < 175 and l > 100])
    num_long_links = len([l for l in link_lengths if l > 175])

    return ('\n==Design Analysis==\n'
            '  Average of {avg_links_per_site:.2f} links per site.\n'
            '  Breakdown of link connectivity per site:\n'
            '{link_connectivity_counts}\n'
            '  {longest_link} meters is the longest link.\n'
            '  {shortest_link} meters is the shortest link.\n'
            '  {num_short_links} links are shorter than 100 meters.\n'
            '  {num_med_links} links are 100 to 175 meters.\n'
            '  {num_long_links} links are longer than 175 meters.\n'
            ''.format(link_connectivity_counts=link_count_display,
                      avg_links_per_site=avg_links_per_site,
                      longest_link=max(link_lengths),
                      shortest_link=min(link_lengths),
                      num_short_links=num_short_links,
                      num_med_links=num_med_links,
                      num_long_links=num_long_links))


def proximity_issue_report(sites, links):
    """Generate a report to identify data issues"""
    site_proximity_warning = ('  The lat/long site data places sites within a '
                              'meter of each other:')
    for close_sites in utilities.find_close_nodes(nodes=sites):
        site_proximity_warning += '    {}\n'.format(', '.join(close_sites))

    return ('\n==Location Proximity Data Issues==\n'
            '{site_proximity_warning}'
            ''.format(site_proximity_warning=site_proximity_warning))


def missing_data_fields_report(sites, links):
    """Generate a report to identify data issues"""
    data_gaps = utilities.get_missing_fields(nodes=sites, edges=links)

    missing_data_report = ('  These objects are missing data fileds:\n')
    for item, missing_data in data_gaps.iteritems():
        missing_data_report += ('  {} is missing => {}\n'
                                ''.format(item, ', '.join(missing_data)))

    return ('\n==Missing Data Field Issues==\n'
            '{missing_data_report}'
            ''.format(missing_data_report=missing_data_report))


def material_requirements_report(sites):
    """Generate a report based on BOM properties associated with the site."""
    complete_bom = {'client_devices': 0,
                    'primary_devices': 0,
                    'secondary_devices': 0,
                    'odroid_devices': 0}
    sites_missing_data = []

    for site in sites:
        if 'bill_of_materials' not in site.properties:
            sites_missing_data.append(site.id)
            continue
        site_bom = site.properties['bill_of_materials'].lower()
        complete_bom['client_devices'] += site_bom.count('cn')
        complete_bom['odroid_devices'] += site_bom.count('odroid')
        if site_bom.count('dn') > 1:
            complete_bom['secondary_devices'] += site_bom.count('dn') - 1
            complete_bom['primary_devices'] += 1
        elif site_bom.count('dn') == 1:
            complete_bom['primary_devices'] += 1

    return ('\n==Material Requirements==\n'
            '{primary_devices} primary devices required.\n'
            '{secondary_devices} secondary devices required.\n'
            '{client_devices} client node devices required.\n'
            '{odroids} odroid devices required.\n\n'
            '**This report only includes information for sites with data '
            'included and the following sites do not have a "bill_of_materials"'
            ' field defining a hardware BOM.\n {num_sites_missing_data}'
            ' of {total_sites} sites are MISSING this data.'
            ''.format(primary_devices=complete_bom['primary_devices'],
                      secondary_devices=complete_bom['secondary_devices'],
                      client_devices=complete_bom['client_devices'],
                      odroids=complete_bom['odroid_devices'],
                      num_sites_missing_data=len(sites_missing_data),
                      total_sites=len(sites)))


def export_to_geojson(sites, links=None):
    """Convert geojson.Features to an ordered geojson txt string."""
    sites = sites + links
    if isinstance(sites, list):
        sites = [geojson.Feature(
            id=site.id,
            geometry=site.geometry,
            properties=site.properties
            ) for site in sites]

        sites.sort(lambda x, y: cmp(x['id'], y['id']))
        sites = geojson.FeatureCollection(sites)

    return geojson.dumps(sites, sort_keys=True, indent=4,
                         separators=(',', ': '))


def export_sites_to_csv(file_path, sites):
    """Export site data to csv format."""
    column_names = set()
    for site in sites:
        for property_name in site.properties:
                column_names.add(property_name)

    column_names = sorted(list(column_names))
    column_names.insert(0, 'site_id')
    column_names.insert(1, 'latitude')
    column_names.insert(2, 'longitude')

    with open(file_path, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_names)
        writer.writeheader()
        for site in sites:
            row = {}
            row['site_id'] = site.id
            row['longitude'], row['latitude'] = site.geometry.coordinates
            for name, value in site.properties.iteritems():
                row[name] = value

            writer.writerow(row)


def export_to_kml(sites, links):
    """Export site data to kml format."""

    def makeExtendedDataElements(datadict):
        """Convert a dictionary to ExtendedData/Data elements"""
        edata = KML.ExtendedData()
        for key, value in datadict.iteritems():
            edata.append(KML.Data(KML.value(value), name=key))
        return edata

    def makeFolder(name, placemarks):
        """Add a list of KML.placemarks into to a folder."""
        folder = KML.Folder(KML.name(name))
        for placemark in placemarks:
            folder.append(placemark)
        return folder

    site_folder = KML.Folder(KML.name("Sites"))
    link_folder = KML.Folder(KML.name("Links"))
    link_source_folders = collections.defaultdict(list)

    site_style = KML.Style(
        KML.IconStyle(
            KML.scale(1.2),
            KML.Icon(
                KML.href('http://maps.google.com/mapfiles/kml/shapes/'
                         'placemark_circle_highlight.png'),
            ),
            id='icon'),
        KML.LineStyle(KML.color('00000000'), KML.width('15')),
        id='site')

    line_style = KML.Style(
        KML.LineStyle(KML.color('7fff0000'), KML.width('4')),
        KML.PolyStyle(KML.color('7fff0000')),
        id='link')

    for site in sites:
        name = site.id
        lat, lng = site.geometry.coordinates
        kml_properties = makeExtendedDataElements(site.properties)
        placemark = KML.Placemark(
            KML.name(name),
            KML.styleUrl('#site'),
            kml_properties,
            KML.Point(
                KML.extrude('1'),
                KML.altitudeMode('relativeToGround'),
                KML.coordinates('{},{},12'.format(lat, lng))
            ),
        )
        site_folder.append(placemark)

    for link in links:
        name = link.id
        coords1, coords2 = link.geometry.coordinates
        lat1, lng1 = coords1
        lat2, lng2 = coords2
        kml_properties = makeExtendedDataElements(link.properties)
        placemark = KML.Placemark(
            KML.name(name),
            KML.styleUrl('#link'),
            kml_properties,
            KML.LineString(
                KML.extrude('1'),
                KML.altitudeMode('relativeToGround'),
                KML.coordinates(
                    '{},{},6 '.format(lat1, lng1),
                    '{},{},6'.format(lat2, lng2))
            ),
        )
        source = link.properties.get('data_source', 'unknown')

        link_source_folders[source].append(placemark)

    for (name, placemarks) in link_source_folders.items():
        link_folder.append(makeFolder(name, placemarks))

    doc = KML.kml(
        KML.Document(
            KML.name('Export.kml'),
            KML.open('1'),
            site_style,
            line_style,
            site_folder,
            link_folder))

    if Schema('kml22gx.xsd').validate(doc):
        return lxml.etree.tostring(doc, pretty_print=True)
    else:
        return ''
