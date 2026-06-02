#!/usr/bin/env python3
"""
This is a static RSS aggregator
"""

import sys
import shutil
import logging
import argparse
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Union


def init_data(data_dir: Path):
    # Create directory
    data_dir.mkdir(mode=0o755, exist_ok=True)
    # Create feeds file
    opml_root = ET.fromstring('''\
<opml version="2.0">
    <head>
        <title>Static RSS aggregator feeds</title>
    </head>
    <body>
    </body>
</opml>''')
    opml_tree = ET.ElementTree(opml_root)
    opml_tree.write(data_dir / 'feeds.xml', encoding='utf-8')


def get_max_feed_index(data_dir: Path) -> int:
    index = 0
    for entry in data_dir.iterdir():
        if not entry.is_dir():
            continue
        try:
            index = max(index, int(entry.name))
        except ValueError:
            continue
    return index


def fetch_feed(feed_dir: Path, url: str, name='current.xml'):
    with urllib.request.urlopen(url) as response, open(feed_dir / name, 'wb') as file:
        shutil.copyfileobj(response, file)


def find_element_without_attribute(parent: ET.Element, xpath: str, att_name: str, namespaces) -> Union[ET.Element, None]:
    els = parent.findall(xpath, namespaces=namespaces)
    for el in els:
        if att_name not in el.attrib.keys():
            return el
    return None


def init_main_feed_and_get_properties(feed_path: Path) -> dict:
    # Load feed file
    feed_tree = ET.parse(feed_path)
    feed_root = feed_tree.getroot()
    # Add stylesheet (different for RSS and Atom)
    if feed_root.tag == 'rss':
        # This is RSS feed
        namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
        title = feed_root.find('title')
        title_value = title.text
        xml_url = feed_root.find('atom:link[@rel="self"]', namespaces=namespaces)
        xml_url_value = xml_url.text
        html_url = feed_root.find('link')
        html_url_value = html_url.text
        feed_tree.write(feed_path, encoding='utf-8')
    elif feed_root.tag == '{http://www.w3.org/2005/Atom}feed':
        # This is Atom feed
        namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
        title = feed_root.find('atom:id', namespaces=namespaces)
        title_value = title.text
        xml_url = feed_root.find('atom:link[@rel="self"]', namespaces=namespaces)
        xml_url_value = xml_url.text
        html_url = feed_root.find('atom:link[@rel="alternate"]', namespaces=namespaces)
        if html_url is None:
            html_url = find_element_without_attribute(feed_root, 'atom:link', 'rel', namespaces)
        html_url_value = None if html_url is None else html_url.get('href')
        feed_tree.write(feed_path, encoding='utf-8', default_namespace=namespaces['atom'], xml_declaration=True)
    else:
        raise ValueError('Unknown feed format!')
    # Return feed properties
    return {
        'title': title_value,
        'xmlUrl': xml_url_value,
        'htmlUrl': html_url_value
    }


def add_feed(args):
    pass


def list_feeds(args):
    pass


def rename_feed(args):
    pass


def remove_feed(args):
    pass


def fetch_feeds(args):
    pass


def import_feeds(args):
    if not args.data_dir.exists():
        init_data(args.data_dir)
    # Load new OPML feed and check its type
    new_opml_tree = ET.parse(args.opml_file)
    new_opml_root = new_opml_tree.getroot()
    if new_opml_root.tag != 'opml':
        logging.error(f'File {args.opml_file} is not a OPML feed')
        sys.exit(1)
    # Load internal OPML feed
    internal_opml_tree = ET.parse(args.data_dir / 'feeds.xml')
    internal_opml_root = internal_opml_tree.getroot()
    internal_opml_body = internal_opml_root.find('body')
    # Iterate through entries in the new feed and look up
    # in the internal feed if it contains entries with the same URL
    for new_outline in new_opml_root.iterfind('body/outline'):
        feed_title = new_outline.get('title')
        feed_url = new_outline.get('xmlUrl')
        if new_outline.get('type') != 'rss':
            logging.warning(f'Skipping outline {feed_title} that is not RSS feed')
            continue
        found = internal_opml_root.find(f'body/outline[@xmlUrl="{feed_url}"]')
        if found is not None:
            logging.warning(f'Skipping already known feed {feed_title} with URL {feed_url}')
            continue
        logging.info(f'Importing new feed {feed_title} with URL {feed_url}')
        # Make feed directory and download feed file
        feed_index = get_max_feed_index(args.data_dir) + 1
        feed_dir = args.data_dir / str(feed_index)
        feed_dir.mkdir(mode=0o755)
        try:
            fetch_feed(feed_dir, feed_url)
        except urllib.error.URLError as e:
            logging.error(f'Error fetching feed: {e.reason}')
            feed_dir.rmdir()
            continue
        except ValueError as e:
            logging.error(f'Error fetching feed: {e}')
            feed_dir.rmdir()
            continue
        # Copy new feed to main feed with additional information
        shutil.copy(feed_dir / 'current.xml', feed_dir / 'feed.xml')
        props = init_main_feed_and_get_properties(feed_dir / 'feed.xml')
        internal_outline = ET.Element('outline', attrib={
            'title': props['title'],
            'text': props['title'],
            'type': 'rss',
            'xmlUrl': props['xmlUrl'],
            'htmlUrl': props['htmlUrl'],
            'index': str(feed_index)
        })
        internal_opml_body.append(internal_outline)
    # Write internal feed
    internal_opml_tree.write(args.data_dir / 'feeds.xml', encoding='utf-8')


def export_feeds(args):
    shutil.copy(args.data_dir / 'feeds.xml', args.opml_file)


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    parser.add_argument('--data_dir', '-d', type=Path, help='Data directory')
    subparsers = parser.add_subparsers(help='Commands')

    parser_add = subparsers.add_parser('add', help='Add RSS or Atom feed')
    parser_add.add_argument('feed_url', help='URL of the feed')
    parser_add.add_argument('feed_name', help='Name of the feed')
    parser_add.set_defaults(func=add_feed)
    
    parser_list = subparsers.add_parser('list', help='List feeds')
    parser_list.set_defaults(func=list_feeds)

    parser_rename = subparsers.add_parser('rename', help='Rename feed')
    parser_rename.add_argument('feed_index', type=int, help='Index of the feed to be renamed')
    parser_rename.add_argument('name', help='New name')
    parser_rename.set_defaults(func=rename_feed)
    
    parser_rm = subparsers.add_parser('rm', help='Remove feed')
    parser_rm.add_argument('feed_index', type=int, help='Index of the feed to be removed')
    parser_rm.set_defaults(func=remove_feed)
    
    parser_fetch = subparsers.add_parser('fetch', help='Fetch all feeds and rebuild data')
    parser_fetch.set_defaults(func=fetch_feeds)

    parser_import = subparsers.add_parser('import', help='Import feeds from OPML file')
    parser_import.add_argument('opml_file', type=Path, help='The file the list of feeds is imported from')
    parser_import.set_defaults(func=import_feeds)

    parser_export = subparsers.add_parser('export', help='Export feeds to OPML file')
    parser_export.add_argument('opml_file', type=Path, help='The file the list of feeds is exported to')
    parser_export.set_defaults(func=export_feeds)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()