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
    echo Arguments:
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

FEEDS_XML="$FEED_DIR/feeds.xml"

SCRIPT_DIR=`dirname $0`
SINGLEFEED_XSL="$SCRIPT_DIR"/singlefeed.xsl

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
        FEED_INDEX=`get_max_feed_index`
        FEED_INDEX=`expr $FEED_INDEX + 1`
        echo Feed index: $FEED_INDEX
        xsltproc --stringparam opmlFeed "$OPML_FEED"
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
