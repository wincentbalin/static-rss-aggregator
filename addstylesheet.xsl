<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:atom="http://www.w3.org/2005/Atom">
    <!-- Output results as indented XML -->
    <xsl:output method="xml" encoding="utf-8" indent="yes"></xsl:output>

    <!-- Do identity transform -->
    <xsl:template match="@*|node()">
        <xsl:copy><xsl:apply-templates select="@*|node()"/></xsl:copy>
    </xsl:template>

    <!-- Match target stylesheet with document format -->
    <xsl:variable name="target-stylesheet">
        <xsl:choose>
            <!-- RSS 2.0 -->
            <xsl:when test="rss"><xsl:text>../rss2html5.xsl</xsl:text></xsl:when>
            <!-- RSS 1.0 -->
            <xsl:when test="rdf:RDF"><xsl:text>../rss2html5.xsl</xsl:text></xsl:when>
            <!-- Atom -->
            <xsl:when test="atom:feed"><xsl:text>../atom2html5.xsl</xsl:text></xsl:when>
        </xsl:choose>
    </xsl:variable>

    <!-- Insert processing instruction before document root -->
    <xsl:processing-instruction name="xml-stylesheet">
        <xsl:text>type="text/xsl" href="</xsl:text>
        <xsl:value-of select="$target-stylesheet"/>
        <xsl:text>"</xsl:text>
    </xsl:processing-instruction>

    <!-- Then output the original document -->
    <xsl:apply-templates select="node()"/>
</xsl:stylesheet>