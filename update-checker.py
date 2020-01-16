#! /usr/bin/env python3

#--#--#--#--#--#--#--#--#--#--#--#--#--#
#--# Import everything we need
#--#--#--#--#--#--#--#--#--#--#--#--#--#

import requests
import argparse
import sys

#--#--#--#--#--#--#--#--#--#--#--#--#--#
#--# Set our variables and lists
#--#--#--#--#--#--#--#--#--#--#--#--#--#

token_url = 'https://access.redhat.com/management/api#/'
access_url = 'https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token'
api_url = 'https://api.access.redhat.com/management/v1/systems'
device_list = []
patches_id = []
patches_s = []
patches_t = []

#--#--#--#--#--#--#--#--#--#--#--#--#--#
#--# Set up the help menu and arguments
#--#--#--#--#--#--#--#--#--#--#--#--#--#

parser = argparse.ArgumentParser(description='A tool to query the RHSM API',
        epilog='Just like that you are all done')

#--#--#--#--#--#--#--#--#--#--#--#--#--#
#--# We add the token flag as required so the script can't run with out it
#--# we have a flag for each type of update - All updates - bug fixes
#--# security updates -- performance updates. These save the values
#--# following when you use the flag to whatever the flag name is
#--# so  --security-updates is saved to args.security_updates
#--#--#--#--#--#--#--#--#--#--#--#--#--#

parser.add_argument('-t', '--token', required=True, metavar='TOKEN',
        help='''-t <offline token> -- this can be retrieved from
        https://access.redhat.com/management/api#/ the token lasts 30 days and is used to 
        generate an access token for making API calls. The access token lasts 900 seconds.''')
parser.add_argument('-a', '--all-updates', metavar='DEVICE',
        help='''This will list all available updates for everything matching DEVICE. 
        Note it is a wildcard match so if you provide 'foo' as a match, it will 
        match all devices '*foo*' ''')
parser.add_argument('-b', '--bug-updates', metavar='DEVICE',
        help="Similar to '-a' except only show bug fix updates")
parser.add_argument('-p', '--performance-updates', metavar='DEVICE',
        help="Similar to '-a' except only show performance enhancement updates")
parser.add_argument('-s', '--security-updates', metavar='DEVICE',
        help="Similar to '-a' except only show security updates")

#--#--#--#--#--#--#--#--#--#--#--#--#--#
#--# Load our arguments
#--#--#--#--#--#--#--#--#--#--#--#--#--#

args = parser.parse_args()

#--#--#--#--#--#--#--#--#--#--#--#--#--#
#--# Run a few check to make sure we don't use too many options, or miss any
#--# essentially we are checking that if the token exists, one of the other 
#--# flags also exists, otherwise exit
#--#--#--#--#--#--#--#--#--#--#--#--#--#

if args.token and not (args.all_updates or args.bug_updates or
        args.performance_updates or args.security_updates):
    print('Did you specify the type of updates you would like to check?')
    sys.exit(1)

if args.token and len(sys.argv) > 5:
    print('Please only list one method of checking updates at a time')
    sys.exit(1)

#--#--#--#--#--#--#--#--#--#--#--#--#--#
#--# The main meat of the script, we define our functions here
#--# This first one takes our offline token we provided and sends a request
#--# to the redhat portal. This returns a limited time access token to use for 
#--# API calls. Sadly the offline token must be generated from the website directly
#--# otherwise I would have scripted it out. At the end, we return the access_token
#--# so we can use it to craft our calls below
#--#--#--#--#--#--#--#--#--#--#--#--#--#
def get_access_token(offline_token):
    req = requests.post(access_url,
            data={'grant_type':'refresh_token','client_id':'rhsm-api','refresh_token':offline_token})

    if req.status_code != 200:
        print(req.text)
        raise Exception('Recieved non 200 response when retrieving access token')
        sys.exit(1)

    access_token = req.json()
    access_token = access_token['access_token']
    return access_token

#--#--#--#--#--#--#--#--#--#--#--#--#--#
#--# This is where the most work happens, we have this function which takes
#--# the device match string from what we threw in the CLI and the search string
#--# to match the type of updates we want to check(all,bug,performance,security)
#--#--#--#--#--#--#--#--#--#--#--#--#--#

def get_devices(device_match, search_string):

    # this call returns a list of every device match
    headers = {'Authorization': 'Bearer ' + access_token}
    url = api_url + '?filter=' + device_match
    req = requests.get(url, headers=headers).json()

    # Here we filter through the list and pull all the uuids for another search 
    for item in req['body']:
        device_list.append(item['uuid'])

    # we make a call for each uuid to pull it's updates
    for uuid in device_list:
        url = api_url + '/' + uuid

        dev_name = requests.get(url, headers=headers).json()
        dev_name = dev_name['body']['name']
        url = url + '/errata'
        patches = requests.get(url, headers=headers).json()

        # we filter through the patch list info and pull the package, rhba/rhsa
        # and the synopsys and create 3 separate lists
        for item in patches['body']:
            patches_id.append(item['id'])
            patches_s.append(item['synopsis'])
            patches_t.append(item['type'])
        print('\n' + dev_name)
        
        # we merge all the lists into one
        slurp = list(zip(patches_t, patches_s, patches_id))
        
        # we filter through all the lists and pull whatever the search was 
        # whether it was bug,security,all, or performance
        filtered = list(filter(lambda elems: search_string in elems, slurp))
        
        # we convert it to a set, which only pulls unique values and gets
        # rid of any all duplicates
        filtered = set(filtered)

        # we go through the entries and print them all out
        for a,b,c in filtered:
            print(' [+] ' + a + ' - ' + c + ' - ' + b)

#--#--#--#--#--#--#--#--#--#--#--#--#--#
#--# This calls our function from earlier and saves the access_token
#--# the if statement checks to see what value from our flags is not empty
#--# if it is not empty, then it run the second function and sends the appropriate
#--# search flag for certain updates to the function
#--#--#--#--#--#--#--#--#--#--#--#--#--#
access_token = get_access_token(args.token)

if args.all_updates:
    get_devices(args.all_updates, 'Advisory')
elif args.security_updates:
    get_devices(args.security_updates, 'Security Advisory')
elif args.bug_updates:
    get_devices(args.bug_updates, 'Bug Fix Advisory')
elif args.performance_updates:
    get_devices(args.performance_updates, 'Product Enhancement Advisory')
