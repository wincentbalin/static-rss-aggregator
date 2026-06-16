#!/bin/sh
#
# Aggregate feeds and show links to their articles on a HTML page.
# Use wget to download feeds and xsltproc to process them with XSLT.

usage()
{
    echo Usage: $0 directory command [arguments]
    echo
    echo Commands: init, import, fetch, add, list, rename, remove, export
    echo
    echo Arguments for commands:
    echo "    import    OPML file"
    echo "    add       Page URL"
    echo "    rename    Feed index, new name"
    echo "    remove    Feed index"
    echo "    export    OPML file"
    exit 1
}

if [ $# -eq 0 ]
then
  usage
fi

FEED_DIR=$1
COMMAND=$2

USER_AGENT="Aggregator/1.0"

FEEDS_XML="$FEED_DIR/feeds.xml"
FEEDS_XML_NEW="$FEED_DIR/feeds.xml.new"

SCRIPT_DIR=`dirname $0`
SINGLEFEED_XSL="$SCRIPT_DIR"/singlefeed.xsl
FIXFEED_XSL="$SCRIPT_DIR"/fixfeed.xsl
ADDSTYLESHEET_XSL="$SCRIPT_DIR"/addstylesheet.xsl
ADDFEED_XSL="$SCRIPT_DIR"/addfeed.xsl
EXTRACTAUTODISCOVERYLINKS_XSL="$SCRIPT_DIR"/extractautodiscoverylinks.xsl

get_max_feed_index()
{
    INDEX=0

    for DIR in "$FEED_DIR"/*
    do
        if [ ! -d "$DIR" ]
        then
            continue
        fi

        DIR_BASE=`basename $DIR`
        if [ "`echo $DIR_BASE | grep [^0-9]`" ]
        then
            continue
        fi

        if [ $DIR_BASE -gt $INDEX ]
        then
            INDEX=$DIR_BASE
        fi
    done

    echo $INDEX
}

case $COMMAND in
    init)
        echo Initialise feeds directory $FEED_DIR
        mkdir "$FEED_DIR"
        cat << EOF > "$FEEDS_XML"
<opml version="2.0">
    <head>
        <title>Static RSS aggregator feeds</title>
    </head>
    <body>
    </body>
</opml>
EOF
        ;;
    import)
        OPML_FILE=$3
        echo Importing from OPML file $OPML_FILE

        IFS='\n' set -- `xsltproc --stringparam feeds_xml "$FEEDS_XML" "$SINGLEFEED_XSL" "$OPML_FILE"`
        TEXT="$1"
        TITLE="$2"
        XML_URL="$3"
        HTML_URL="$4"

        if [ -z "$XML_URL" ]
        then
            echo All feeds processed
            exit 0
        fi

        #echo Text: $TEXT
        #echo Title: $TITLE
        #echo XML URL: $XML_URL
        #echo HTML URL: $HTML_URL

        FEED_INDEX=`get_max_feed_index`
        FEED_INDEX=`expr $FEED_INDEX + 1`
        #echo Feed index: $FEED_INDEX

        CURRENT_FEED="$FEED_DIR"/$FEED_INDEX/current.xml
        MAIN_FEED="$FEED_DIR"/$FEED_INDEX/feed.xml
        mkdir "$FEED_DIR"/$FEED_INDEX
        wget -q -U "$USER_AGENT" -O "$CURRENT_FEED" "$XML_URL"

        if ! [ -f "$CURRENT_FEED" ]
        then
            echo Could not download feed from $XML_URL
            exit 1
        fi

        # For Linux
        DEFAULT_DATE_EPOCH=`stat -c %Y "$CURRENT_FEED"`
        DEFAULT_DATE=`date -u -d "@$DEFAULT_DATE_EPOCH" "+%a, %d %b %Y %H:%M:%S %z"`
        # For BSD/MacOS
        #DEFAULT_DATE_EPOCH=`stat -f %m "$CURRENT_FEED"`
        #DEFAULT_DATE=`date -ur "$DEFAULT_DATE_EPOCH" "+%a, %d %b %Y %H:%M:%S %z"`

        # Fix edge cases (in RSS: no guid, no pubDate, date in wrong format, etc.)
        FIXED_FEED="$FEED_DIR"/$FEED_INDEX/fixed.xml
        xsltproc "$SINGLEFEED_XSL" "$CURRENT_FEED" > "$FIXED_FEED"

        # Add processing instruction for RSS or Atom XSLT stylesheet
        xsltproc "$ADDSTYLESHEET_XSL" "$FIXED_FEED" > "$MAIN_FEED"

        # Clean up
        rm "$FIXED_FEED"

        # Add outline to the internal OPML feed
        xsltproc --stringparam text "$TEXT" --stringparam title "$TITLE" --stringparam xmlUrl "$XML_URL" --stringparam htmlUrl "$HTML_URL" "$ADDFEED_XSL" "$FEEDS_XML" > "$FEEDS_XML_NEW"
        ;;
    fetch)
        echo Fetching feeds
        ;;
    add)
        PAGE_URL=$3
        echo Searching for feed in $PAGE_URL
        ;;
    list)
        echo List of feeds:
        ;;
    rename)
        FEED_INDEX=$3
        NEW_NAME=$4
        echo Renaming feed $FEED_INDEX to $NEW_NAME
        ;;
    remove)
        FEED_INDEX=$3
        echo Removing feed $FEED_INDEX
        ;;
    export)
        OPML_FILE=$3
        echo Exporting to OPML file $OPML_FILE
        cp "$FEEDS_XML" "$OPML_FILE"
        ;;
    *)
        echo Unknown command $COMMAND
        echo
        usage
esac
