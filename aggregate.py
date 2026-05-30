#!/usr/bin/env python3
"""
This is a static RSS aggregator
"""

import shutil
import logging
import argparse
from pathlib import Path


def add_feed(args):
    pass


def list_feeds(args):
    pass


def remove_feed(args):
    pass


def fetch_feeds(args):
    pass


def import_feeds(args):
    pass


def export_feeds(args):
    shutil.copy(args.data_dir / 'feeds.xml', args.opml_file)


def main():
    import sys

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
    args.func(args)


if __name__ == '__main__':
    main()