from urllib.request import urlopen
from urllib.parse import urlencode
import json

def request(type, arg):
    data = json.loads(urlopen('http://aur.archlinux.org/rpc.php?'
        + urlencode(dict(type=type, arg=arg))).read().decode('ascii'))
    if data['type'] == 'error':
        raise LookupError(data['results'])
    assert data['type'] == type
    return data['results']

if __name__ == '__main__':
    import sys, pprint
    r = request(*sys.argv[1:])
    pprint.pprint(r)
