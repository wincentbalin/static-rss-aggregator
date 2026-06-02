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
import xml.dom.minidom
from pathlib import Path
from typing import List, Union
from xml.dom.minidom import Element


def init_data(data_dir: Path):
    # Create directory
    data_dir.mkdir(mode=0o755, exist_ok=True)
    # Create feeds file
    opml_root = xml.dom.minidom.parseString('''\
<opml version="2.0">
    <head>
        <title>Static RSS aggregator feeds</title>
    </head>
    <body>
    </body>
</opml>''')
    with open(data_dir / 'feeds.xml', 'w', encoding='utf-8') as opml_file:
        opml_root.writexml(opml_file, encoding='utf-8')


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


def getChildElementsByTagName(parent: Element, tagName: str) -> List[Element]:
    nodes = []
    for node in parent.childNodes:
        if node.nodeType == node.ELEMENT_NODE and node.tagName == tagName:
            nodes.append(node)
    return nodes


def getChildElementByTagName(parent: Element, tagName: str) -> Union[Element, None]:
    for node in parent.childNodes:
        if node.nodeType == node.ELEMENT_NODE and node.tagName == tagName:
            return node
    return None


def getChildElementByTagNameAndAttributeValue(parent: Element, tagName: str,
                                              attributeName: str, attributeValue: str) -> Union[Element, None]:
    for node in parent.childNodes:
        if node.nodeType == node.ELEMENT_NODE and node.tagName == tagName:
            if node.getAttribute(attributeName) == attributeValue:
                return node
    return None


def getChildElementWithAttribute(parent: Element, tagName: str, attributeName: str) -> Union[Element, None]:
    for node in parent.childNodes:
        if node.nodeType == node.ELEMENT_NODE and node.tagName == tagName:
            if node.hasAttribute(attributeName):
                return node
    return None



def getChildElementWithoutAttribute(parent: Element, tagName: str, attributeName: str) -> Union[Element, None]:
    for node in parent.childNodes:
        if node.nodeType == node.ELEMENT_NODE and node.tagName == tagName:
            if not node.hasAttribute(attributeName):
                return node
    return None


def getText(parent: Element) -> Union[str, None]:
    for node in parent.childNodes:
        if node.nodeType == node.TEXT_NODE:
            return node.data
    return None


def init_main_feed_and_get_properties(feed_path: Path) -> dict:
    # Load feed file
    with open(feed_path, 'r', encoding='utf-8') as feed_file:
        with xml.dom.minidom.parse(feed_file) as feed_dom:
            # Add stylesheet (different for RSS and Atom)
            feed_doc = feed_dom.documentElement
            if feed_doc.tagName == 'rss':
                # This is RSS feed
                channel = getChildElementByTagName(feed_doc, 'channel')
                title = getChildElementByTagName(channel, 'title')
                title_value = getText(title).strip()
                xml_url = getChildElementByTagNameAndAttributeValue(channel, 'atom:link', 'rel', 'self')
                xml_url_value = xml_url.getAttribute('href')
                html_url = getChildElementWithoutAttribute(channel, 'link', 'rel')
                html_url_value = getText(html_url)
                # Add stylesheet
            elif feed_doc.tagName == 'feed':
                # This is Atom feed
                title = getChildElementByTagName(feed_doc, 'title')
                title_value = getText(title).strip()
                xml_url = getChildElementByTagNameAndAttributeValue(feed_doc, 'link', 'rel', 'self')
                xml_url_value = xml_url.getAttribute('href')
                html_url = getChildElementByTagNameAndAttributeValue(feed_doc, 'link', 'rel', 'alternate')
                if html_url is None:
                    html_url = getChildElementWithoutAttribute(feed_doc, 'link', 'rel')
                html_url_value = html_url.getAttribute('href')
                # Add stylesheet
            else:
                raise ValueError('Unknown feed format!')
            #with open(feed_path, 'w', encoding='utf-8') as changed_file:
            #    feed_dom.writexml(changed_file, encoding='utf-8')
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
    with open(args.opml_file, 'r', encoding='utf-8') as opml_file, \
         open(args.data_dir / 'feeds.xml', 'r', encoding='utf-8') as feeds_file:
        with xml.dom.minidom.parse(opml_file) as opml_dom, \
             xml.dom.minidom.parse(feeds_file) as feeds_dom:
            # Check OPML file type
            if opml_dom.documentElement.tagName != 'opml':
                logging.error(f'File {args.opml_file} is not a OPML feed')
                sys.exit(1)
            opml_body = getChildElementByTagName(opml_dom.documentElement, 'body')
            feeds_body = getChildElementByTagName(feeds_dom.documentElement, 'body')
            # Iterate through entries in the new feed and look up
            # in the internal feed if it contains entries with the same URL
            for outline in getChildElementsByTagName(opml_body, 'outline'):
                feed_title = outline.getAttribute('title')
                feed_url = outline.getAttribute('xmlUrl')
                if outline.getAttribute('type') != 'rss':
                    logging.warning(f'Skipping outline {feed_title} that is not RSS feed')
                    continue
                found = getChildElementByTagNameAndAttributeValue(feeds_body, 'outline', 'xmlUrl', feed_url)
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
                logging.info(f'Props: {props}')

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