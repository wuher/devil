#  -*- coding: utf-8 -*-
# xml.py ---
#
# Created: Fri Feb  3 01:30:53 2012 (+0200)
# Author: Janne Kuuskeri
#


import types
from decimal import Decimal, InvalidOperation
import xml.sax.handler
from django.utils.xmlutils import SimplerXMLGenerator
from django.utils.encoding import smart_unicode
from devil.datamapper import DataMapper

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


class XmlMapper(DataMapper):
    """ Naïve XML mapper.

    This mapper will map basic python constructs into xml and back. For
    anything more serious it is recommended that an xml mapper which supports
    schemas is implemented.

    Notes:
      * Element attributes are not supported (i.e. ``<person type="employee">``)
      * If an xml element contains subelements that have the same name
        the element will be considered as a list even if some of the subelements
        have different name. For example ::

            <orders>
              <order_item><id>3</id><name>Skates</name></order_item>
              <order_item><id>4</id><name>Snowboard</name></order_item>
              <order_info>Urgent</order_info>
            </orders>

        would become ::

            {'orders': [{"id": 3, "name": "Skates"},
                        {"id": 4, "name": "Snowboard"},
                        "Urgent"]}

      * By default, the produced xml will always have ``<root>`` as its
        top-level root element (can be overridden). The same root element
        must be present when parsing the xml data.
      * By default, the produced xml list item elements will be suffixed
        with ``_item``. (can be overridden). For parsing list items don't
        need to have this suffix, it is enough for them to be same.
      * When parsing, numbers can be left as strings, or they can be mapped
        to basic types ``int`` and ``float`` or alternatively to ``Decimal``.
        This can be controlled with the constructor parameter of this class.
    """

    content_type = 'text/xml'

    def __init__(self, numbermode=None):
        """ Initialize the parser.

        :param numbermode: supported values are ``None``, 'basic' or 'decimal'
        """

        self._numbermode = numbermode

    def _parse_data(self, data, charset):
        """ Parse the xml data into dictionary. """

        builder = TreeBuilder(numbermode=self._numbermode)
        if isinstance(data,basestring):
            xml.sax.parseString(data, builder)
        else:
            xml.sax.parse(data, builder)
        return builder.root[self._root_element_name()]

    def _format_data(self, data, charset):
        """ Format data into XML. """

        if data is None or data == '':
            return u''

        stream = StringIO.StringIO()
        xml = SimplerXMLGenerator(stream, charset)
        xml.startDocument()
        xml.startElement(self._root_element_name(), {})
        self._to_xml(xml, data)
        xml.endElement(self._root_element_name())
        xml.endDocument()
        return stream.getvalue()

    def _to_xml(self, xml, data, key=None):
        """ Recursively convert the data into xml.

        This function was originally copied from the
        `Piston project <https://bitbucket.org/jespern/django-piston/>`_
        It has been modified since.

        :param xml: the xml document
        :type xml: SimplerXMLGenerator
        :param data: data to be formatted
        :param key: name of the parent element (for root this is ``None``)
        """

        if isinstance(data, (list, tuple)):
            for item in data:
                elemname = self._list_item_element_name(key)
                xml.startElement(elemname, {})
                self._to_xml(xml, item)
                xml.endElement(elemname)
        elif isinstance(data, dict):
            for key, value in data.iteritems():
                xml.startElement(key, {})
                self._to_xml(xml, value, key)
                xml.endElement(key)
        else:
            xml.characters(smart_unicode(data))

    def _root_element_name(self):
        """ Return the name of the xml root element.

        By default returns 'root'. Override to return something else.
        """

        return 'root'

    def _list_item_element_name(self, key=None):
        """ Return tag-name for a list item.

        By default return the name of the key with '_item' suffix.

        For example ``volumes = [12, 34, 56]`` would become ::

            <volumes>
                <volume_item>12</volume_item>
                <volume_item>34</volume_item>
                <volume_item>56</volume_item>
            </volumes>

        @todo memoize perhaps..
        """

        key = key or ''
        return '%s_item' % (key,)


class TreeBuilder(xml.sax.handler.ContentHandler):
    """ SAX builder to parse the xml data """

    def __init__(self, numbermode=None):
        """ Initialize the parser.

        :param numbermode: supported values are ``None``, 'basic' or 'decimal'
        """

        self.numbermode = numbermode
        self.stack = []
        self.root = {}
        self.current = self.root
        self.chardata = []

    def startElement(self, name, attrs):
        """ Initialize new node and store current node into stack. """
        self.stack.append((self.current, self.chardata))
        self.current = {}
        self.chardata = []

    def endElement(self, name):
        """ End current xml element, parse and add to to parent node. """
        if self.current:
            # we have nested elements
            obj = self.current
        else:
            # text only node
            text = ''.join(self.chardata).strip()
            obj = self._parse_node_data(text)
        newcurrent, self.chardata = self.stack.pop()
        self.current = self._element_to_node(newcurrent, name, obj)

    def characters(self, content):
        """ Just store all characters. """
        self.chardata.append(content)

    def _parse_node_data(self, data):
        """ Parse the value of a node. Override to provide your own parsing. """
        data = data or ''
        if self.numbermode == 'basic':
            return self._try_parse_basic_number(data)
        elif self.numbermode == 'decimal':
            return self._try_parse_decimal(data)
        else:
            return data

    def _try_parse_basic_number(self, data):
        """ Try to convert the data into ``int`` or ``float``.

        :returns: ``Decimal`` or ``data`` if conversion fails.
        """

        # try int first
        try:
            return int(data)
        except ValueError:
            pass
        # try float next
        try:
            return float(data)
        except ValueError:
            pass
        # no luck, return data as it is
        return data

    def _try_parse_decimal(self, data):
        """ Try to convert the data into decimal.

        :returns: ``Decimal`` or ``data`` if conversion fails.
        """

        try:
            return Decimal(data)
        except InvalidOperation:
            return data

    def _element_to_node(self, node, name, value):
        """ Insert the parsed element (``name``, ``value`` pair) into the node.

        You should always use the returned node and forget the one
        that was given in parameter.

        :param node: the node where the is added to
        :returns: the node. Note that this may be a new node instance.
        """

        # is the target node a list?
        try:
            node.append(value)
        except AttributeError:
            pass
        else:
            return node

        # target node is a dict
        if name in node:
            # there's already an element with same name -> convert the node into list
            node = node.values() + [value]
        else:
            # just add the value into the node
            node[name] = value
        return node

#
# xml.py ends here
