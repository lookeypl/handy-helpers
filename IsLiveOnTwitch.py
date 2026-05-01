#!/usr/bin/env python

from argparse import ArgumentParser
from sys import exit
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from urllib.parse import quote
from HandyUtils import ModuleExists, ReadConfigFile, ConfigNotFoundError

import asyncio
import traceback

class IsLiveOnTwitch:
    def __init__(self, confDir: str = "./config/"):
        self.mConfigDir = confDir
        pass

    async def run(self, twitchName: str, quiet: bool):
        try:
            clientId = ReadConfigFile("twitch.client_id", self.mConfigDir)
            clientSecret = ReadConfigFile("twitch.client_secret", self.mConfigDir)
        except ConfigNotFoundError:
            print("Failed to read Twitch configuration files from directory '{0}'. Files are either missing or empty.".format(self.mConfigDir))
            print("Ensure relative to script launch directory there is a 'config' directory containing following files:")
            print("  - twitch.client_id - file containing Twitch OAuth Client ID")
            print("  - twitch.client_secret - file containing Twitch OAuth Client Secret")
            print("Both have to be acquired from https://dev.twitch.tv/ developer console.")
            print("Alternatively, point the script at a custom configuration path with '--config <path>'.")
            return False

        twitch = await Twitch(clientId, clientSecret)
        twitchUser = await first(twitch.get_users(logins=twitchName))

        live = False
        async for channel in twitch.search_channels(query=quote(twitchName), live_only=True):
            if channel.broadcaster_login == twitchName and channel.id == twitchUser.id:
                live = channel.is_live
                break

        await twitch.close()

        if not quiet:
            if live: print("{0} is now live.".format(twitchName))
            else: print("{0} is offline.".format(twitchName))

        return live


async def main():
    try:
        if not ModuleExists('twitchAPI'):
            print('Twitch API module is not accessible. Install via \'pip install twitchAPI\'.')
            exit(2)

        parser = ArgumentParser(
            prog='IsLiveOnTwitch',
            description='Check if someone is right now live on Twitch using Twitch API.'
        )
        parser.add_argument('twitch_name', help='Name of user to check')
        parser.add_argument('-q', '--quiet', help='Suppress printing console output',
                            action='store_true', default=False)
        parser.add_argument('--config', help='Directory to fetch configuration files (twitch client ID and secret) from',
                            default="./config/")
        args = parser.parse_args()

        if await IsLiveOnTwitch(args.config).run(args.twitch_name, args.quiet):
            exit(0)

        exit(1)
    except Exception as e:
        print("Exception caught by main: {0}".format(e))
        traceback.print_exception(e)
        exit(2)

if __name__ == "__main__":
    asyncio.run(main())