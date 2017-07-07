import yaml
from mattermost_bot.bot import listen_to
from mattermost_bot.bot import respond_to
from CloudFlare import cloudflare
from maxcdn import MaxCDN


with open("credentials.yml", 'r') as credfile:
    CREDENTIALS = yaml.load(credfile)


def fetch_cloudflare_zones():
    data = dict()
    data['cloudflare'] = dict()
    for account in CREDENTIALS['cloudflare']:
        data['cloudflare'][account] = dict()
        api = cloudflare.CloudFlare(
            email=CREDENTIALS['cloudflare'][account]['email'],
            token=CREDENTIALS['cloudflare'][account]['key'])
        zones = api.zones.get()
        for zone in zones:
            zone_name = zone['name']
            zone_id = zone['id']
            data['cloudflare'][account][zone_name] = zone_id
    return data


def fetch_maxcdn_zones():
    data = dict()
    data['maxcdn'] = dict()
    for account in CREDENTIALS['maxcdn']:
        data['maxcdn'][account] = dict()
        api = MaxCDN(
            CREDENTIALS['maxcdn'][account]['alias'],
            CREDENTIALS['maxcdn'][account]['consumer_key'],
            CREDENTIALS['maxcdn'][account]['consumer_secret'])
        # page_size=100 because default value is 50
        zones = api.get("/zones/pull.json?page_size=100")
        for zone in zones["data"]["pullzones"]:
            zone_name = zone['name']
            zone_id = zone['id']
            data['maxcdn'][account][zone_name] = zone_id
    return data


def purge_cloudflare_zone(zone_name):
    try:
        account, zone_id = get_cloudflare_zone_id(zone_name)
    except ValueError:
        return get_cloudflare_zone_id(zone_name)
    api = cloudflare.CloudFlare(
        email=CREDENTIALS['cloudflare'][account]['email'],
        token=CREDENTIALS['cloudflare'][account]['key'])
    return api.zones.delete(
        zone_id +
        '/purge_cache',
        data={'purge_everything': True}
        )


def purge_maxcdn_zone(zone_name):
    try:
        account, zone_id = get_maxcdn_zone_id(zone_name)
    except ValueError:
        return get_maxcdn_zone_id(zone_name)
    api = MaxCDN(
        CREDENTIALS['maxcdn'][account]['alias'],
        CREDENTIALS['maxcdn'][account]['consumer_key'],
        CREDENTIALS['maxcdn'][account]['consumer_secret'])
    return api.purge(zone_id)


def refresh_zones():
    with open('zones.yml', 'w') as outfile:
        maxcdn_zones = fetch_maxcdn_zones()
        cloudflare_zones = fetch_cloudflare_zones()
        yaml.dump(maxcdn_zones, outfile, default_flow_style=False)
        yaml.dump(cloudflare_zones, outfile, default_flow_style=False)
    return 'Done'


def list_zones():
    zone_list = list()
    with open("zones.yml", 'r') as zonefile:
        zones = yaml.load(zonefile)
    zone_list.append('**MaxCDN Zones:**')
    for account in zones['maxcdn']:
        for zone_name, zone_id in zones['maxcdn'][account].items():
            zone_list.append(zone_name)
            #return zone_name
    zone_list.append('**Cloudflare Zones:**')
    for account in zones['cloudflare']:
        for zone_name, zone_id in zones['cloudflare'][account].items():
            zone_list.append(zone_name)
            #return zone_name
    return zone_list


def get_cloudflare_zone_id(zone_name):
    with open("zones.yml", 'r') as zonefile:
        zones = yaml.load(zonefile)
    for account in zones['cloudflare']:
        if zone_name in zones['cloudflare'][account].keys():
            zone_id = zones['cloudflare'][account][zone_name]
            account_name = account
    try:
        zone_id
    except NameError:
        return 'ZoneNotFound'
    else:
        return account_name, zone_id


def get_maxcdn_zone_id(zone_name):
    with open("zones.yml", 'r') as zonefile:
        zones = yaml.load(zonefile)
    for account in zones['maxcdn']:
        if zone_name in zones['maxcdn'][account].keys():
            zone_id = zones['maxcdn'][account][zone_name]
            account_name = account
    try:
        zone_id
    except NameError:
        return 'ZoneNotFound'
    else:
        return account_name, zone_id


@respond_to('cloudflare drop (.*)')
@respond_to('cf drop (.*)')
@listen_to('cloudflare drop (.*)')
@listen_to('cf drop (.*)')
def cloudflare_purge(message, zone):
    message.send(str(purge_cloudflare_zone(zone)))


@respond_to('maxcdn drop (.*)')
@listen_to('maxcdn drop (.*)')
def maxcdn_purge(message, zone):
    message.send(str(purge_maxcdn_zone(zone)))


@respond_to('list cdn zones')
@listen_to('list cdn zones')
def list_cdn_zones(message):
    zones = list_zones()
    message.send("\n".join(zones))


@respond_to('refresh cdn zones')
@listen_to('refresh cdn zones')
def refresh_cdn_zones(message):
    message.send(refresh_zones())


cloudflare_purge.__doc__ = "purge cloudflare cache"
maxcdn_purge.__doc__ = "purge maxcdn cache"
list_cdn_zones.__doc__ = "list cdn zones"
refresh_cdn_zones.__doc__ = "fetch new zones from CDN providers"
