"""Utilities for EVE-online API request and response handling.

This module provides functionality to interact with EVE-online API server:
    * Any API method requests with given arbitrary parameters.
    * XML response transformation into Python dictionary.
    * HTTP and HTTPS support (default is HTTPS).
    * Custom EVE_API_URL support (default is 'api.eveonline.com').

Consider /server/ServerStatus response XML:
    <?xml version='1.0' encoding='UTF-8'?>
    <eveapi version="2">
      <currentTime>2011-08-30 22:36:14</currentTime>
      <result>
        <serverOpen>True</serverOpen>
        <onlinePlayers>30356</onlinePlayers>
      </result>
      <cachedUntil>2011-08-30 22:37:24</cachedUntil>
    </eveapi>

result = SERVER_STATUS.send_request()
    {u'attributes': {u'version': u'2'},
     u'eveapi': {u'cachedUntil': {u'text': u'2011-09-01 22:07:42'},
                 u'currentTime': {u'text': u'2011-09-01 22:05:33'},
                 u'result': {u'onlinePlayers': {u'text': u'29910'},
                             u'serverOpen': {u'text': u'True'}}}}

The result is simple dictionary with nested keys, here are some usage examples:
    onlinePlayers = int(result['eveapi']['result']['onlinePlayers']['text'])
    cached_until = parse_eve_datetime(result['eveapi']['cachedUntil']['text'])
    current_time = parse_eve_datetime(result['eveapi']['currentTime']['text'])
    delta = cached_until - current_time

All API methods are defined in this module, e.g. ACCOUNT_CHARACTERS, CHAR_WALLET_JOURNAL, CORP_WALLET_TRANSACTIONS, etc.

Links:
    http://code.google.com/p/python-eveapi/
    http://wiki.eve-id.net/APIv2_Page_Index
"""

__author__ = 'Valery Leushin <vleushin@gmail.com>'
__version__ = '1.1'

import httplib
import urllib
import xml.dom.minidom
import datetime
import time
import logging

EVE_API_URL = 'api.eve-central.com'
EVE_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

class EveApiMethod(object):
    """Class that represents arbitrary EVE API method.

    In given scenario:
        custom_api_method = EveApiMethod(method='/api/CustomMethodName', api_home='example.com')
        result = custom_api_method.send_request({'param1': 'value1', 'param2': 'value2'})
    The request will be sent to http://example.com/api/CustomMethodName.xml.aspx?param1=value1&param2=value2

    Attributes:
        method: URL prefix for method, e.g. '/account/Characters'.
        api_home: Hostname of EVE API server.
    """

    def __init__(self, method, api_home=EVE_API_URL):
        self.method = method
        self.api_home = api_home

    def send_request(self, parameters=dict(), return_xml=False, use_https=True):
        """Send request to EVE API server and return processed response.

        Args:
            parameters: Dictionary with URL parameters.
            return_xml: Also return raw API XML response.
            use_https: Use HTTPS instead of HTTP for EVE API server communication.

        Returns:
            processed_dict: Processed dictionary with corresponding structure.
            (processed_dict, raw_xml): Tuple of processed dictionary and raw XML (when return_xml=True).

        Examples:
            EveApiMethod('/eve/CharacterInfo').send_request({'characterID': 499939401})
                {u'attributes': {u'version': u'2'},
                 u'eveapi': {u'cachedUntil': {u'text': u'2011-09-01 22:40:48'},
                             u'currentTime': {u'text': u'2011-09-01 22:02:58'},
                             u'result': {u'alliance': {u'text': u'New Eden Research.'},
                                         u'allianceDate': {u'text': u'2010-03-15 14:07:00'},
                                         u'allianceID': {u'text': u'1470696988'},
                                         u'attributes': {u'columns': u'recordID,corporationID,startDate',
                                                         u'key': u'recordID',
                                                         u'name': u'employmentHistory'},
                                         u'bloodline': {u'text': u'Intaki'},
                                         u'characterID': {u'text': u'499939401'},
                                         u'characterName': {u'text': u'hcydo'},
                                         u'corporation': {u'text': u'Odylab Research'},
                                         u'corporationDate': {u'text': u'2011-08-22 01:21:00'},
                                         u'corporationID': {u'text': u'1214825692'},
                                         u'employmentHistory': {u'11522142': {u'corporationID': u'766116469',
                                                                              u'recordID': u'11522142',
                                                                              u'startDate': u'2009-09-12 07:32:00'},
                                                                u'17670088': {u'corporationID': u'98061600',
                                                                              u'recordID': u'17670088',
                                                                              u'startDate': u'2011-08-18 20:04:00'},
                                                                u'17695894': {u'corporationID': u'1214825692',
                                                                              u'recordID': u'17695894',
                                                                              u'startDate': u'2011-08-22 01:21:00'},
                                                                u'2598586': {u'corporationID': u'1000169',
                                                                             u'recordID': u'2598586',
                                                                             u'startDate': u'2008-07-12 16:56:00'},
                                                                u'2598587': {u'corporationID': u'1394595964',
                                                                             u'recordID': u'2598587',
                                                                             u'startDate': u'2008-07-12 20:34:00'}},
                                         u'race': {u'text': u'Gallente'},
                                         u'securityStatus': {u'text': u'1.19860777290912'}}}}
            EveApiMethod('/account/Characters').send_request({'keyID': 12345, 'vCode': '67890'})
                {u'attributes': {u'version': u'2'},
                 u'eveapi': {u'cachedUntil': {u'text': u'2011-09-01 23:01:52'},
                             u'currentTime': {u'text': u'2011-09-01 22:04:52'},
                             u'result': {u'attributes': {u'columns': u'name,characterID,corporationName,corporationID',
                                                         u'key': u'characterID',
                                                         u'name': u'characters'},
                                         u'characters': {u'270095316': {u'characterID': u'270095316',
                                                                        u'corporationID': u'1214825692',
                                                                        u'corporationName': u'Odylab Research',
                                                                        u'name': u'fcydo'},
                                                         u'499939401': {u'characterID': u'499939401',
                                                                        u'corporationID': u'1214825692',
                                                                        u'corporationName': u'Odylab Research',
                                                                        u'name': u'hcydo'},
                                                         u'515300277': {u'characterID': u'515300277',
                                                                        u'corporationID': u'1214825692',
                                                                        u'corporationName': u'Odylab Research',
                                                                        u'name': u'pcydo'}}}}}
        """
        conn = httplib.HTTPSConnection(self.api_home) if use_https else httplib.HTTPConnection(self.api_home)
        request_url = self.compose_url(parameters)
        logging.info('Sending request to EVE API (%s) server: %s', EVE_API_URL, self.method)
        conn.request('GET', request_url)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        processed_dict = dom_to_dict(xml.dom.minidom.parseString(data))
        return (processed_dict, data) if return_xml else processed_dict

    def compose_url(self, parameters=dict()):
        """Compose URL from method prefix and given query parameters.

        Args:
            parameters: Dictionary with query parameters.

        Returns:
            Composed request URL.

        Examples:
            >>> ACCOUNT_CHARACTERS.compose_url({'key': 'value'})
            '/account/Characters.xml.aspx?key=value'
            >>> SERVER_STATUS.compose_url()
            '/server/ServerStatus.xml.aspx'
        """
        return '%(method)s.xml.aspx%(question)s%(query)s' % {'method': self.method,
                                                             'question': '?' if len(parameters) > 0 else '',
                                                             'query': urllib.urlencode(parameters)}

ACCOUNT_CHARACTERS = EveApiMethod('/account/Characters')
ACCOUNT_STATUS = EveApiMethod('/account/AccountStatus')

CHAR_ACCOUNT_BALANCES = EveApiMethod('/char/AccountBalance')
CHAR_ASSET_LIST = EveApiMethod('/char/AssetList')
CHAR_CALENDAR_EVENT_ATTENDEES = EveApiMethod('/char/CalendarEventAttendees')
CHAR_CHARACTER_SHEET = EveApiMethod('/char/CharacterSheet')
CHAR_CONTACT_LIST = EveApiMethod('/char/ContactList')
CHAR_CONTACT_NOTIFICATIONS = EveApiMethod('/char/ContactNotifications')
CHAR_CONTRACTS = EveApiMethod('/char/Contracts')
CHAR_CONTRACT_ITEMS = EveApiMethod('/char/ContractItems')
CHAR_CONTRACT_BIDS = EveApiMethod('/char/ContractBids')
CHAR_FACTIONAL_WARFARE_STATS = EveApiMethod('/char/FacWarStats')
CHAR_INDUSTRY_JOBS = EveApiMethod('/char/IndustryJobs')
CHAR_KILL_LOG = EveApiMethod('/char/Killlog')
CHAR_MAIL_BODIES = EveApiMethod('/char/MailBodies')
CHAR_MAILING_LISTS = EveApiMethod('/char/MailingLists')
CHAR_MAIL_MESSAGES = EveApiMethod('/char/MailMessages')
CHAR_MARKET_ORDERS = EveApiMethod('/char/MarketOrders')
CHAR_MEDALS = EveApiMethod('/char/Medals')
CHAR_NOTIFICATIONS = EveApiMethod('/char/Notifications')
CHAR_NOTIFICATION_TEXTS = EveApiMethod('/char/NotificationTexts')
CHAR_RESEARCH = EveApiMethod('/char/Research')
CHAR_SKILL_IN_TRAINING = EveApiMethod('/char/SkillInTraining')
CHAR_SKILL_QUEUE = EveApiMethod('/char/SkillQueue')
CHAR_STANDINGS = EveApiMethod('/char/Standings')
CHAR_UPCOMING_CALENDAR_EVENTS = EveApiMethod('/char/UpcomingCalendarEvents')
CHAR_WALLET_JOURNAL = EveApiMethod('/char/WalletJournal')
CHAR_WALLET_TRANSACTIONS = EveApiMethod('/char/WalletTransactions')

CORP_ACCOUNT_BALANCES = EveApiMethod('/corp/AccountBalance')
CORP_ASSET_LIST = EveApiMethod('/corp/AssetList')
CORP_CONTACT_LIST = EveApiMethod('/corp/ContactList')
CORP_CONTAINER_LOG = EveApiMethod('/corp/ContainerLog')
CORP_CONTRACTS = EveApiMethod('/corp/Contracts')
CORP_CONTRACT_ITEMS = EveApiMethod('/corp/ContractItems')
CORP_CONTRACT_BIDS = EveApiMethod('/corp/ContractBids')
CORP_CORPORATION_SHEET = EveApiMethod('/corp/CorporationSheet')
CORP_FACTIONAL_WARFARE_STATS = EveApiMethod('/corp/FacWarStats')
CORP_INDUSTRY_JOBS = EveApiMethod('/corp/IndustryJobs')
CORP_KILL_LOG = EveApiMethod('/corp/Killlog')
CORP_MARKET_ORDERS = EveApiMethod('/corp/MarketOrders')
CORP_MEDALS = EveApiMethod('/corp/Medals')
CORP_MEMBER_MEDALS = EveApiMethod('/corp/MemberMedals')
CORP_MEMBER_SECURITY = EveApiMethod('/corp/MemberSecurity')
CORP_MEMBER_SECURITY_LOG = EveApiMethod('/corp/MemberSecurityLog')
CORP_MEMBER_TRACKING = EveApiMethod('/corp/MemberTracking')
CORP_OUTPOST_LIST = EveApiMethod('/corp/OutpostList')
CORP_OUTPOST_SERVICE_DETAIL = EveApiMethod('/corp/OutpostServiceDetail')
CORP_SHAREHOLDERS = EveApiMethod('/corp/Shareholders')
CORP_STANDINGS = EveApiMethod('/corp/Standings')
CORP_STARBASE_DETAILS = EveApiMethod('/corp/StarbaseDetail')
CORP_STARBASE_LIST = EveApiMethod('/corp/StarbaseList')
CORP_TITLES = EveApiMethod('/corp/Titles')
CORP_WALLET_JOURNAL = EveApiMethod('/corp/WalletJournal')
CORP_WALLET_TRANSACTIONS = EveApiMethod('/corp/WalletTransactions')

EVE_ALLIANCE_LIST = EveApiMethod('/eve/AllianceList')
EVE_CERTIFICATE_TREE = EveApiMethod('/eve/CertificateTree')
EVE_CHARACTER_ID = EveApiMethod('/eve/CharacterID')
EVE_CHARACTER_INFO = EveApiMethod('/eve/CharacterInfo')
EVE_CHARACTER_NAME = EveApiMethod('/eve/CharacterName')
EVE_CONQUERABLE_STATION_LIST = EveApiMethod('/eve/ConquerableStationList')
EVE_ERROR_LIST = EveApiMethod('/eve/ErrorList')
EVE_FACTIONAL_WARFARE_STATS = EveApiMethod('/eve/FacWarStats')
EVE_FACTIONAL_WARFARE_TOP_STATS = EveApiMethod('/eve/FacWarTopStats')
EVE_REFTYPES_LIST = EveApiMethod('/eve/RefTypes')
EVE_SKILL_TREE = EveApiMethod('/eve/SkillTree')

MAP_FACTIONAL_WARFARE_SYSTEMS = EveApiMethod('/map/FacWarSystems')
MAP_JUMPS = EveApiMethod('/map/Jumps')
MAP_KILLS = EveApiMethod('/map/Kills')
MAP_SOVEREIGNTY = EveApiMethod('/map/Sovereignty')

SERVER_STATUS = EveApiMethod('/server/ServerStatus')

def _dict_with_path(path, value):
    """Create new dictionary that will have value under corresponding nested key path.

    Args:
        path: List of nested keys, e.g. ['key1', 'key2'].
        value: Given value will be set for the last key in path, i.e. {'key2': 'some value'}.
        
    Returns:
        New dict with one value under corresponding path.

    Examples:
        >>> _dict_with_path(['key1', 'key2'], 'some value')
        {'key1': {'key2': 'some value'}}
        >>> _dict_with_path(['one', 'two', 'three', 'four'], 'five')
        {'one': {'two': {'three': {'four': 'five'}}}}
    """
    root_d = d = dict()
    last_element = path.pop()
    for element in path:
        d[element] = dict()
        d = d[element]
    d[last_element] = value
    return root_d


def _dict_update(dict1, dict2):
    """Update dict1 with dict2 values. Unlike dict.update(), pays attention to nested dictionaries and updates them too.

    Args:
        dict1: Dictionary to update.
        dict2: Dictionary with updates.

    Returns:
        Updated dict1.

    Examples:
        >>> dict1 = {'key1': {'key2': {'key3a': 'some value'}}}
        >>> dict2 = {'key1': {'key2': {'key3b': 'some new value'}}}
        >>> _dict_update(dict1, dict2)
        {'key1': {'key2': {'key3a': 'some value', 'key3b': 'some new value'}}}

    NB: usual dict.update() simply overrides key1 in dict1 with key1 from dict2.
        >>> dict1.update(dict2); dict1
        {'key1': {'key2': {'key3b': 'some new value'}}}

    Links:
        http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    """
    for k, v in dict2.iteritems():
        if type(v) is dict:
            r = _dict_update(dict1.get(k, {}), v)
            dict1[k] = r
        else:
            dict1[k] = dict2[k]
    return dict1


def dom_to_dict(element, path=list()):
    """Convert DOM structure to Python dictionary.

    Has some EVE API specifics: rowsets are parsed differently, i.e. following rowset:
        <result>
            <rowset name="characters" key="characterID" columns="name,characterID,corporationName,corporationID">
                <row name="fcydo" characterID="270095316" corporationName="Odylab Research" corporationID="1214825692"/>
                <row name="hcydo" characterID="499939401" corporationName="Odylab Research" corporationID="1214825692"/>
                <row name="pcydo" characterID="515300277" corporationName="Odylab Research" corporationID="1214825692"/>
            </rowset>
        </result>
    will be transformed into following dictionary structure ('key' attribute value is used as dictionary key):
         u'result': {u'attributes': {u'columns': u'name,characterID,corporationName,corporationID',
                                     u'key': u'characterID',
                                     u'name': u'characters'},
                     u'characters': {u'270095316': {u'characterID': u'270095316',
                                                    u'corporationID': u'1214825692',
                                                    u'corporationName': u'Odylab Research',
                                                    u'name': u'fcydo'},
                                     u'499939401': {u'characterID': u'499939401',
                                                    u'corporationID': u'1214825692',
                                                    u'corporationName': u'Odylab Research',
                                                    u'name': u'hcydo'},
                                     u'515300277': {u'characterID': u'515300277',
                                                    u'corporationID': u'1214825692',
                                                    u'corporationName': u'Odylab Research',
                                                    u'name': u'pcydo'}}}}}

    Args:
        element: Current DOM element.
        path: List of strings that represent current key path, e.g. ['eveapi', 'cachedUntil'].

    Returns:
        Dictionary with corresponding structure.
    """
    result = dict()
    for child in element.childNodes:
        if child.nodeType is child.TEXT_NODE:
            child_data = child.data.strip()
            if len(child_data) > 0:
                _dict_update(result, _dict_with_path(path + [u'text'], child_data))
        elif child.nodeType is child.ELEMENT_NODE:
            attributes = dict()
            for k, v in child.attributes.items():
                attributes[k] = v
            if len(attributes) > 0:
                _dict_update(result, _dict_with_path(path + [u'attributes'], attributes))
            if child.tagName == 'rowset':
                _dict_update(result, _process_eveapi_rowset(child,
                                                            path + [child.attributes['name'].value],
                                                            attributes['key']))
            else:
                _dict_update(result, dom_to_dict(child, path + [child.tagName]))
    return result


def _process_eveapi_rowset(element, path, key):
    """Process EVE API response XML rowset element.

    Args:
        element: Rowset DOM element.
        path: List of strings that represent current key path, e.g. ['eveapi', 'cachedUntil'].
        key: Key attribute name.

    Returns:
        Dictionary with corresponding rowset structure.
    """
    result = dict()
    for child in element.childNodes:
        if child.nodeType is child.ELEMENT_NODE:
            attributes = dict()
            for k, v in child.attributes.items():
                attributes[k] = v
            key_value = attributes[key]
            _dict_update(result, _dict_with_path(path + [key_value], attributes))
    return result


def parse_eve_datetime(eve_datetime):
    """Parse EVE date string that has format '%Y-%m-%d %H:%M:%S' into datetime.

    Args:
        eve_datetime: EVE date string.

    Returns:
        Corresponding datetime object.

    Examples:
        >>> parse_eve_datetime('2011-08-30 22:37:24')
        datetime.datetime(2011, 8, 30, 22, 37, 24)
        >>> parse_eve_datetime('2011-08-30 22:34:41')
        datetime.datetime(2011, 8, 30, 22, 34, 41)
        >>> parse_eve_datetime('2011-08-30 22:34:41.123456')
        datetime.datetime(2011, 8, 30, 22, 34, 41)
        >>> parse_eve_datetime('')
        >>> parse_eve_datetime(None)
    """
    if eve_datetime is None or len(eve_datetime) is 0:
        return None
    return datetime.datetime(*time.strptime(eve_datetime[0:19], EVE_DATE_FORMAT)[0:6])