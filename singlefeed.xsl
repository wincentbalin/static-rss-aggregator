<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <!-- Path to feeds.xml -->
    <xsl:param name="feeds_xml"></xsl:param>

    <!-- Load feeds.xml -->
    <xsl:variable name="feeds" select="document($feeds_xml)"/>

    <!-- Output results as text lines -->
    <xsl:output method="text" encoding="utf-8"></xsl:output>

    <!-- Match the root element and process outlines -->
    <xsl:template match="/">
        <xsl:variable name="firstMissing" select="//outline[@type='rss' and not(@xmlUrl = $feeds//outline/@xmlUrl)][1]"></xsl:variable>
            <!-- Output attributes, one per line -->
            <xsl:value-of select="$firstMissing/@text"/><xsl:text>&#10;</xsl:text>
            <xsl:value-of select="$firstMissing/@title"/><xsl:text>&#10;</xsl:text>
            <xsl:value-of select="$firstMissing/@xmlUrl"/><xsl:text>&#10;</xsl:text>
            <xsl:value-of select="$firstMissing/@htmlUrl"/><xsl:text>&#10;</xsl:text>
    </xsl:template>
</xsl:stylesheet>