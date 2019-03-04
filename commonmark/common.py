from __future__ import absolute_import, unicode_literals

import re
import sys

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

if sys.version_info >= (3, 0):
    if sys.version_info >= (3, 4):
        import html
        HTMLunescape = html.unescape
    else:
        from .entitytrans import _unescape
        HTMLunescape = _unescape
else:
    from commonmark import entitytrans
    HTMLunescape = entitytrans._unescape

ENTITY = '&(?:#x[a-f0-9]{1,8}|#[0-9]{1,8}|[a-z][a-z0-9]{1,31});'

TAGNAME = '[A-Za-z][A-Za-z0-9-]*'
ATTRIBUTENAME = '[a-zA-Z_:][a-zA-Z0-9:._-]*'
UNQUOTEDVALUE = "[^\"'=<>`\\x00-\\x20]+"
SINGLEQUOTEDVALUE = "'[^']*'"
DOUBLEQUOTEDVALUE = '"[^"]*"'
ATTRIBUTEVALUE = "(?:" + UNQUOTEDVALUE + "|" + SINGLEQUOTEDVALUE + \
    "|" + DOUBLEQUOTEDVALUE + ")"
ATTRIBUTEVALUESPEC = "(?:" + "\\s*=" + "\\s*" + ATTRIBUTEVALUE + ")"
ATTRIBUTE = "(?:" + "\\s+" + ATTRIBUTENAME + ATTRIBUTEVALUESPEC + "?)"
OPENTAG = "<" + TAGNAME + ATTRIBUTE + "*" + "\\s*/?>"
CLOSETAG = "</" + TAGNAME + "\\s*[>]"
HTMLCOMMENT = '<!---->|<!--(?:-?[^>-])(?:-?[^-])*-->'
PROCESSINGINSTRUCTION = "[<][?].*?[?][>]"
DECLARATION = "<![A-Z]+" + "\\s+[^>]*>"
CDATA = '<!\\[CDATA\\[[\\s\\S]*?\\]\\]>'
HTMLTAG = "(?:" + OPENTAG + "|" + CLOSETAG + "|" + HTMLCOMMENT + "|" + \
    PROCESSINGINSTRUCTION + "|" + DECLARATION + "|" + CDATA + ")"
reHtmlTag = re.compile('^' + HTMLTAG, re.IGNORECASE)
reBackslashOrAmp = re.compile(r'[\\&]')
ESCAPABLE = '[!"#$%&\'()*+,./:;<=>?@[\\\\\\]^_`{|}~-]'
reEntityOrEscapedChar = re.compile(
    '\\\\' + ESCAPABLE + '|' + ENTITY, re.IGNORECASE)
XMLSPECIAL = '[&<>"]'
reXmlSpecial = re.compile(XMLSPECIAL)
reXmlSpecialOrEntity = re.compile(ENTITY + '|' + XMLSPECIAL, re.IGNORECASE)


def unescape_char(s):
    if s[0] == '\\':
        return s[1]
    else:
        return HTMLunescape(s)


def unescape_string(s):
    """Replace entities and backslash escapes with literal characters."""
    if re.search(reBackslashOrAmp, s):
        return re.sub(
            reEntityOrEscapedChar,
            lambda m: unescape_char(m.group()),
            s)
    else:
        return s


def normalize_uri(uri):
    try:
        return quote(uri.encode('utf-8'), safe=str('/@:+?=&()%#*,'))
    except UnicodeDecodeError:
        # Python 2 also throws a UnicodeDecodeError, complaining about
        # the width of the "safe" string. Removing this parameter
        # solves the issue, but yields overly aggressive quoting, but we
        # can correct those errors manually.
        s = quote(uri.encode('utf-8'))
        s = re.sub(r'%40', '@', s)
        s = re.sub(r'%3A', ':', s)
        s = re.sub(r'%2B', '+', s)
        s = re.sub(r'%3F', '?', s)
        s = re.sub(r'%3D', '=', s)
        s = re.sub(r'%26', '&', s)
        s = re.sub(r'%28', '(', s)
        s = re.sub(r'%29', ')', s)
        s = re.sub(r'%25', '%', s)
        s = re.sub(r'%23', '#', s)
        s = re.sub(r'%2A', '*', s)
        s = re.sub(r'%2C', ',', s)
        return s


UNSAFE_MAP = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
}


def replace_unsafe_char(s):
    return UNSAFE_MAP.get(s, s)


def escape_xml(s, preserve_entities):
    if s is None:
        return ''
    if re.search(reXmlSpecial, s):
        if preserve_entities:
            return re.sub(
                reXmlSpecialOrEntity,
                lambda m: replace_unsafe_char(m.group()),
                s)
        else:
            return re.sub(
                reXmlSpecial,
                lambda m: replace_unsafe_char(m.group()),
                s)
    else:
        return s
