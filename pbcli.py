"""
pbcli.py: A crude and simplistic command-line tool to control a Pixelblaze
controller.

This lets you list patterns, select a pattern (by name), and adjust the
master brightness level. Or you can let it run, in which case it will
show you fps of the current pattern until you hit ctrl-C.

The IP address defaults to 10.0.1.75 because that's where my Pixelblaze
landed on my home network. Sorry, you'll have to set it for yourself.
The PIXELBLAZE_ADDR env var works too.

Based on info from:
https://electromage.com/docs/websockets-api
https://zranger1.github.io/pixelblaze-client/pixelblazeProtocol/

For a more complete and convenient library which does this stuff, see:
https://zranger1.github.io/pixelblaze-client/pixelblaze/

"""

import os
import argparse
import json
import websocket

parser = argparse.ArgumentParser()

parser.add_argument('-a', '--address')
parser.add_argument('-p', '--pattern')
parser.add_argument('-b', '--brightness', type=float)
parser.add_argument('-l', '--list', action='store_true')

args = parser.parse_args()

addr = args.address
if not addr:
    addr = os.environ.get('PIXELBLAZE_ADDR', '10.0.1.75')

WSURL = f'ws://{addr}:81'

patterns = []
endontick = False

def on_open(wsapp):
    global endontick
    
    print('connected...')
    query = {
        'sendUpdates': False,
        'getConfig': True,
        'listPrograms': True,
        'getUpgradeState': False
    }
    wsapp.send(json.dumps(query))
    
    if args.brightness is not None:
        query = { 'brightness': args.brightness }
        wsapp.send(json.dumps(query))
        endontick = True

def on_message(wsapp, msg):
    if isinstance(msg, bytes):
        if msg[0] == 0x07:
            exit = handle_program_list(msg[1], msg[ 2 : ])
            if exit:
                wsapp.close()
    else:
        try:
            dat = json.loads(msg)
            if 'activeProgram' in dat:
                prog = dat['activeProgram']
                print(f'current: {prog["name"]}')
            if 'brightness' in dat:
                print(f'brightness: {dat["brightness"]}')
            if 'fps' in dat:
                print(f'{dat["fps"]} fps')
                if endontick:
                    wsapp.close()
        except Exception as ex:
            print(repr(ex))

def on_close(wsapp, close_status_code, close_msg):
    print('...disconnected')

def handle_program_list(cont, msg):
    global endontick
    
    if cont & 0x01:
        del patterns[ : ]

    for dat in msg.split(b'\n'):
        key, _, name = dat.partition(b'\t')
        if key and name:
            pat = (key.decode(), name.decode())
            patterns.append(pat)
        
    if cont & 0x04:
        if args.list:
            for key, name in patterns:
                print(name)
            return True
        if args.pattern:
            got = [ (key, name) for key, name in patterns if name == args.pattern ]
            if not got:
                print('pattern not found')
                return True
            key, name = got[0]
            query = { 'activeProgramId': key }
            wsapp.send(json.dumps(query))
            endontick = True
    
wsapp = websocket.WebSocketApp(WSURL, on_close=on_close, on_open=on_open, on_message=on_message)
wsapp.run_forever()

