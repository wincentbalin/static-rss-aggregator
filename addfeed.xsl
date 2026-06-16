<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <!-- Parameters passed from command line  -->
    <xsl:param name="text"/>
    <xsl:param name="title"/>
    <xsl:param name="xmlUrl"/>
    <xsl:param name="htmlUrl"/>
    <xsl:param name="index"/>

    <!-- Do identity transform -->
    <xsl:template match="@*|node()">
        <xsl:copy><xsl:apply-templates select="@*|node()"/></xsl:copy>
    </xsl:template>

    <!-- Insert new outline at the end of body -->
    <xsl:template match="body">
        <xsl:apply-templates select="@*|node()"/>

        <!-- Add new outline -->
        <outline>
            <xsl:attribute name="text"><xsl:value-of select="$text"/></xsl:attribute>
            <xsl:attribute name="type">rss</xsl:attribute>
            <xsl:attribute name="title"><xsl:value-of select="$title"/></xsl:attribute>
            <xsl:attribute name="xmlUrl"><xsl:value-of select="$xmlUrl"/></xsl:attribute>
            <xsl:attribute name="htmlUrl"><xsl:value-of select="$htmlUrl"/></xsl:attribute>
            <xsl:attribute name="index"><xsl:value-of select="$index"/></xsl:attribute>
        </outline>
    </xsl:template>
</xsl:stylesheet>