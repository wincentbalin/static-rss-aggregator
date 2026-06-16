<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:atom="http://www.w3.org/2005/Atom">
    <!-- Default RFC822 date to set if non-existent -->
    <xsl:param name="default_date"></xsl:param>

    <!-- Output results as indented XML -->
    <xsl:output method="xml" encoding="utf-8" indent="yes"></xsl:output>

    <!-- Do identity transform -->
    <xsl:template match="@*|node()">
        <xsl:copy><xsl:apply-templates select="@*|node()"/></xsl:copy>
    </xsl:template>

    <!-- Fix RSS items lacking guid: add it from link -->
    <xsl:template match="item[not(guid)][link]">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <guid><xsl:value-of select="normalize-space(link)"/></guid>
            <xsl:apply-templates select="node()"/>
        </xsl:copy>
    </xsl:template>

    <!-- Fix RSS items lacking pubDate: add it from CLI parameter -->
    <xsl:template match="item[not(pubDate)]">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <pubDate><xsl:value-of select="$default_date"/></pubDate>
            <xsl:apply-templates select="node()"/>
        </xsl:copy>
    </xsl:template>

    <!-- Fix RSS items with German RFC822 date format -->
    <xsl:template match="pubDate">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <xsl:choose>
                <!-- De-German RFC822 date string if it starts with
                     German two-letters weekday names Mo,/Di/Mi/Do/Fr/Sa/So
                     followed by a comma; also change month names different
                     from English ones; the three-letters month names
                     Jan/Feb/Apr/Jun/Jul/Aug/Sep/Nov are equivalent in both
                     languages -->
                <xsl:when test="starts-with(., 'Mo, ') or starts-with(., 'Di, ') or 
                                starts-with(., 'Mi, ') or starts-with(., 'Do, ') or 
                                starts-with(., 'Fr, ') or starts-with(., 'Sa, ') or 
                                starts-with(., 'So, ')">
                    <xsl:variable name="d1">
                        <xsl:call-template name="str-replace-one">
                            <xsl:with-param name="text" select="string(.)"/>
                            <xsl:with-param name="from" select="'Mo, '"/>
                            <xsl:with-param name="to" select="'Mon, '"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="d2">
                        <xsl:call-template name="str-replace-one">
                            <xsl:with-param name="text" select="d1"/>
                            <xsl:with-param name="from" select="'Di, '"/>
                            <xsl:with-param name="to" select="'Tue, '"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="d3">
                        <xsl:call-template name="str-replace-one">
                            <xsl:with-param name="text" select="d2"/>
                            <xsl:with-param name="from" select="'Mi, '"/>
                            <xsl:with-param name="to" select="'Wed, '"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="d4">
                        <xsl:call-template name="str-replace-one">
                            <xsl:with-param name="text" select="d3"/>
                            <xsl:with-param name="from" select="'Do, '"/>
                            <xsl:with-param name="to" select="'Thu, '"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="d5">
                        <xsl:call-template name="str-replace-one">
                            <xsl:with-param name="text" select="d4"/>
                            <xsl:with-param name="from" select="'Fr, '"/>
                            <xsl:with-param name="to" select="'Fri, '"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="d6">
                        <xsl:call-template name="str-replace-one">
                            <xsl:with-param name="text" select="d5"/>
                            <xsl:with-param name="from" select="'Sa, '"/>
                            <xsl:with-param name="to" select="'Sat, '"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="d7">
                        <xsl:call-template name="str-replace-one">
                            <xsl:with-param name="text" select="d6"/>
                            <xsl:with-param name="from" select="'So, '"/>
                            <xsl:with-param name="to" select="'Sun, '"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="m1">
                        <xsl:call-template name="str-replace-one">
                            <xsl:with-param name="text" select="d7"/>
                            <xsl:with-param name="from" select="' Mär '"/>
                            <xsl:with-param name="to" select="' Mar '"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="m2">
                        <xsl:call-template name="str-replace-one">
                            <xsl:with-param name="text" select="m1"/>
                            <xsl:with-param name="from" select="' Mai '"/>
                            <xsl:with-param name="to" select="' May '"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="m3">
                        <xsl:call-template name="str-replace-one">
                            <xsl:with-param name="text" select="m2"/>
                            <xsl:with-param name="from" select="' Okt '"/>
                            <xsl:with-param name="to" select="' Oct '"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="m4">
                        <xsl:call-template name="str-replace-one">
                            <xsl:with-param name="text" select="m3"/>
                            <xsl:with-param name="from" select="' Dez '"/>
                            <xsl:with-param name="to" select="' Dec '"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:value-of select="$m4"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="string(.)"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:copy>
    </xsl:template>

    <!-- String replacement, because XSLT 1.0 has no such function -->
    <xsl:template name="str-replace">
        <xsl:param name="text"/>
        <xsl:param name="from"/>
        <xsl:param name="to"/>
        <xsl:choose>
            <xsl:when test="$from != '' and contains($text, $from)">
                <xsl:value-of select="substring-before($text, $from)"/>
                <xsl:value-of select="$to"/>
                <xsl:call-template name="str-replace">
                    <xsl:with-param name="text" select="substring-after($text, $from)"/>
                    <xsl:with-param name="from" select="$from"/>
                    <xsl:with-param name="to" select="$to"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$text"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- String replacement, because XSLT 1.0 has no such function (single replacement variant) -->
    <xsl:template name="str-replace-one">
        <xsl:param name="text"/>
        <xsl:param name="from"/>
        <xsl:param name="to"/>
        <xsl:choose>
            <xsl:when test="$from != '' and contains($text, $from)">
                <xsl:value-of select="substring-before($text, $from)"/>
                <xsl:value-of select="$to"/>
                <xsl:value-of select="substring-after($text, $from)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$text"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>