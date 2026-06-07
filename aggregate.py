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
from pyexpat import ExpatError
from typing import List, Union
from html.parser import HTMLParser
from xml.dom.minidom import Element, Document


class AlternateLinkParser(HTMLParser):
    """
    Parse HTML contents and extract <link rel="alternate".../> tags
    """

    def __init__(self):
        super().__init__()
        self.alternate_links = []
    
    def handle_starttag(self, tag: str, attrs: List[tuple[str, Union[str, None]]]):
        # Process <link> tags only
        if tag.lower() == 'link':
            attr_dict = dict(attrs)
            if attr_dict.get('rel', '').lower() == 'alternate':
                href = attr_dict.get('href')
                title = attr_dict.get('title', 'Untitled feed')
                if href:
                    self.alternate_links.append((href, title))
    
    def get_alternate_links(self) -> list:
        return self.alternate_links


def write_dom(path: Path, dom: Document):
    with open(path, 'w', encoding='utf-8') as xml_file:
        dom.writexml(xml_file, encoding='utf-8')


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
    write_dom(data_dir / 'feeds.xml', opml_root)


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
    headers = {'User-Agent': 'Aggregator/1.0'}
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response, open(feed_dir / name, 'wb') as file:
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
        if node.nodeType in (node.TEXT_NODE, node.CDATA_SECTION_NODE):
            return node.data
    return None


def join_report(header_row: List[str], rows: List[List[str]]) -> str:
    return '\n'.join(['\t'.join(row) for row in [header_row] + rows])


def init_main_feed_and_get_properties(feed_path: Path):
    # Load feed file
    with open(feed_path, 'r', encoding='utf-8', errors='ignore') as feed_file:
        with xml.dom.minidom.parse(feed_file) as feed_dom:
            # Add stylesheet (different for RSS and Atom)
            feed_doc = feed_dom.documentElement
            if feed_doc.tagName in ('rss', 'rdf:RDF'):
                # This is RSS feed
                # Add stylesheet
                pi = feed_dom.createProcessingInstruction('xml-stylesheet', 'type="text/xsl" href="../rss2html5.xsl"')
                feed_dom.insertBefore(pi, feed_doc)
            elif feed_doc.tagName == 'feed':
                # This is Atom feed
                # Add stylesheet
                pi = feed_dom.createProcessingInstruction('xml-stylesheet', 'type="text/xsl" href="../atom2html5.xsl"')
                feed_dom.insertBefore(pi, feed_doc)
            else:
                raise ValueError('Unknown feed format!')
            write_dom(feed_path, feed_dom)


def rebuild_index(data_dir: Path):
    # TODO Implement this function!
    with open(data_dir / 'feeds.xml', 'r', encoding='utf-8') as feeds_file:
        with xml.dom.minidom.parse(feeds_file) as feeds_dom:
            feeds_body = getChildElementByTagName(feeds_dom.documentElement, 'body')


def add_feed(args):
    # Get page and parse it for alternate links
    parser = AlternateLinkParser()
    headers = {'User-Agent': 'Aggregator/1.0'}
    request = urllib.request.Request(args.page_url, headers=headers)
    with urllib.request.urlopen(request) as response:
        # Ensure decoding correct charset
        charset = response.headers.get_content_charset() or 'utf-8'
        # Parse page
        parser.feed(response.read().decode(charset, errors='replace'))
    alternate_links = parser.get_alternate_links()
    # Get feed URL
    if len(alternate_links) == 0:
        logging.error(f'No feed links found at {args.page_url}')
        sys.exit(1)
    elif len(alternate_links) == 1:
        feed_url, feed_title = alternate_links[0]
    else:
        print('Found multiple feeds:')
        for index, (url, title) in enumerate(alternate_links, 1):
            print(f'{index}: {url} ({title})')
        index = input('Which feed do you want to use? ')
        feed_url, feed_title = alternate_links[int(index) - 1]
    # Download feed
    feed_index = get_max_feed_index(args.data_dir) + 1
    feed_dir = args.data_dir / str(feed_index)
    feed_dir.mkdir(mode=0o755)
    try:
        fetch_feed(feed_dir, feed_url)
    except urllib.error.URLError as e:
        logging.error(f'Error fetching feed: {e.reason}')
        feed_dir.rmdir()
        sys.exit(1)
    except ValueError as e:
        logging.error(f'Error fetching feed: {e}')
        feed_dir.rmdir()
        sys.exit(1)
    # Copy new feed to main feed with additional information
    shutil.copy(feed_dir / 'current.xml', feed_dir / 'feed.xml')
    try:
        init_main_feed_and_get_properties(feed_dir / 'feed.xml')
    except ExpatError as e:
        logging.error(f'XML error: {e}')
        shutil.rmtree(feed_dir)
        sys.exit(1)
    # Add feed to feeds index
    feeds_path = args.data_dir / 'feeds.xml'
    with open(feeds_path, 'r', encoding='utf-8') as feeds_file:
        with xml.dom.minidom.parse(feeds_file) as feeds_dom:
            feeds_body = getChildElementByTagName(feeds_dom.documentElement, 'body')
            feeds_outline = feeds_dom.createElement('outline')
            feeds_outline.setAttribute('text', feed_title)
            feeds_outline.setAttribute('type', 'rss')
            feeds_outline.setAttribute('title', feed_title)
            feeds_outline.setAttribute('xmlUrl', feed_url)
            feeds_outline.setAttribute('htmlUrl', args.page_url)
            feeds_outline.setAttribute('index', str(feed_index))
            feeds_body.appendChild(feeds_outline)
            write_dom(feeds_path, feeds_dom)
    rebuild_index(args.data_dir)


def list_feeds(args):
    feeds_report = []
    with open(args.data_dir / 'feeds.xml', 'r', encoding='utf-8') as feeds_file:
        with xml.dom.minidom.parse(feeds_file) as feeds_dom:
            feeds_body = getChildElementByTagName(feeds_dom.documentElement, 'body')
            for feed in getChildElementsByTagName(feeds_body, 'outline'):
                feed_info = [
                    feed.getAttribute(name) for name in ['index', 'text', 'xmlUrl']
                ]
                feeds_report.append(feed_info)
    feeds_report.sort(key=lambda row: int(row[0]))
    print(f'{len(feeds_report)} feeds:')
    for row in feeds_report:
        print('\t'.join(row))


def rename_feed(args):
    feeds_path = args.data_dir / 'feeds.xml'
    with open(feeds_path, 'r', encoding='utf-8') as feeds_file:
        with xml.dom.minidom.parse(feeds_file) as feeds_dom:
            feeds_body = getChildElementByTagName(feeds_dom.documentElement, 'body')
            feed = getChildElementByTagNameAndAttributeValue(feeds_body, 'outline', 'index', str(args.feed_index))
            if feed is None:
                logging.error(f'Feed {args.feed_index} not found')
                sys.exit(1)
            old_title = feed.getAttribute('text')
            feed.setAttribute('text', args.new_title)
            write_dom(feeds_path, feeds_dom)
            rebuild_index(args.data_dir)
    logging.info(f'Renamed feed {args.feed_index} from {old_title} to {args.new_title}')


def remove_feed(args):
    feeds_path = args.data_dir / 'feeds.xml'
    with open(feeds_path, 'r', encoding='utf-8') as feeds_file:
        with xml.dom.minidom.parse(feeds_file) as feeds_dom:
            feeds_body = getChildElementByTagName(feeds_dom.documentElement, 'body')
            feed = getChildElementByTagNameAndAttributeValue(feeds_body, 'outline', 'index', str(args.feed_index))
            if feed is None:
                logging.error(f'Feed {args.feed_index} not found')
                sys.exit(1)
            feed_title = feed.getAttribute('text')
            feeds_body.removeChild(feed)
            write_dom(feeds_path, feeds_dom)
            rebuild_index(args.data_dir)
            logging.info(f'Removed feed {args.feed_index} ({feed_title})')


def fetch_feeds(args):
    pass


def import_feeds(args):
    if not args.data_dir.exists():
        init_data(args.data_dir)
    # Load new OPML feed and check its type; also load internal feeds.xml
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
            feeds_imported, feeds_not_imported = [], []
            for outline in getChildElementsByTagName(opml_body, 'outline'):
                feed_title = outline.getAttribute('title')
                feed_url = outline.getAttribute('xmlUrl')
                report_row = [feed_url, feed_title, outline.getAttribute('htmlUrl')]
                if outline.getAttribute('type') != 'rss':
                    logging.warning(f'Skipping outline {feed_title} that is not RSS feed')
                    feeds_not_imported.append(['Not a RSS feed'] + report_row)
                    continue
                found = getChildElementByTagNameAndAttributeValue(feeds_body, 'outline', 'xmlUrl', feed_url)
                if found is not None:
                    logging.warning(f'Skipping already known feed {feed_title} with URL {feed_url}')
                    feeds_not_imported.append(['Already known feed'] + report_row)
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
                    feeds_not_imported.append([str(e.reason)] + report_row)
                    continue
                except ValueError as e:
                    logging.error(f'Error fetching feed: {e}')
                    feed_dir.rmdir()
                    feeds_not_imported.append([str(e)] + report_row)
                    continue
                # Copy new feed to main feed with additional information
                shutil.copy(feed_dir / 'current.xml', feed_dir / 'feed.xml')
                try:
                    init_main_feed_and_get_properties(feed_dir / 'feed.xml')
                except ExpatError as e:
                    logging.error(f'XML error: {e}')
                    shutil.rmtree(feed_dir)
                    feeds_not_imported.append([str(e)] + report_row)
                    continue
                # Add feed to feeds index
                feeds_outline = feeds_dom.createElement('outline')
                for att_name in ['text', 'type', 'title', 'xmlUrl', 'htmlUrl']:
                    feeds_outline.setAttribute(att_name, outline.getAttribute(att_name))
                feeds_outline.setAttribute('index', str(feed_index))
                feeds_body.appendChild(feeds_outline)
                feeds_imported.append([str(feed_index)] + report_row)
            # Print reports
            if feeds_imported:
                logging.info('Feeds imported:\n' +
                             join_report(['Index', 'Feed URL', 'Title', 'Page URL'], feeds_imported))
            if feeds_not_imported:
                logging.info('Feeds not imported:\n' +
                             join_report(['Error', 'Feed URL', 'Title', 'Page URL'], feeds_not_imported))
            if feeds_imported:
                # Save changed 
                write_dom(args.data_dir / 'feeds.xml', feeds_dom)
                # Rebuild index
                rebuild_index(args.data_dir)


def export_feeds(args):
    shutil.copy(args.data_dir / 'feeds.xml', args.opml_file)


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    parser.add_argument('--data_dir', '-d', type=Path, help='Data directory')
    subparsers = parser.add_subparsers(help='Commands')

    parser_add = subparsers.add_parser('add', help='Add RSS or Atom feed')
    parser_add.add_argument('page_url', help='URL of the page to get a feed from')
    parser_add.set_defaults(func=add_feed)
    
    parser_list = subparsers.add_parser('list', help='List feeds')
    parser_list.set_defaults(func=list_feeds)

    parser_rename = subparsers.add_parser('rename', help='Rename feed')
    parser_rename.add_argument('feed_index', type=int, help='Index of the feed to be renamed')
    parser_rename.add_argument('new_title', help='New title')
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