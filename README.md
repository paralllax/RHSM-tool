# RHSM-tool
A small simple tool to query the rhsm api and get info about updates/devices

```
usage: update-checker.py [-h] -t TOKEN [-a DEVICE] [-b DEVICE] [-p DEVICE]
                         [-s DEVICE]

A tool to query the RHSM API

optional arguments:
  -h, --help            show this help message and exit
  -t TOKEN, --token TOKEN
                        -t <offline token> -- this can be retrieved from
                        https://access.redhat.com/management/api#/ the token
                        lasts 30 days and is used to generate an access token
                        for making API calls. The access token lasts 900
                        seconds.
  -a DEVICE, --all-updates DEVICE
                        This will list all available updates for everything
                        matching DEVICE. Note it is a wildcard match so if you
                        provide 'foo' as a match, it will match all devices
                        '*foo*'
  -b DEVICE, --bug-updates DEVICE
                        Similar to '-a' except only show bug fix updates
  -p DEVICE, --performance-updates DEVICE
                        Similar to '-a' except only show performance
                        enhancement updates
  -s DEVICE, --security-updates DEVICE
                        Similar to '-a' except only show security updates
```
