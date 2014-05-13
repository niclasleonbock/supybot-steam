###
# Copyright (c) 2014, Niclas Leon Bock
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import json

import supybot.utils as utils
from supybot.commands import *
import supybot.conf as conf
import supybot.world as world
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

class Steam(callbacks.Plugin):
    """Just type in 'nowgaming' or 'ng' as command and have fun.
       To link your nickname to your steam profile use 'setsteamprofile'"""

    threaded = True

    summary_url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=%(apikey)s&steamids=%(steamid)s"

    def __init__(self, irc):
        self.__parent = super(Steam, self)
        self.__parent.__init__(irc)
        self.db = SteamUserDB(dbfilename)
        world.flushers.append(self.db.flush)

    def die(self):
        if self.db.flush in world.flushers:
            world.flushers.remove(self.db.flush)
        self.db.close()
        self.__parent.die()

    def fetch_summary(self, steamid64):
        url = self.summary_url % { "apikey": self.registryValue("apiKey"), "steamid": steamid64 }

        status = json.loads(utils.web.getUrl(url))
        players = status["response"]["players"]

        if len(players) <= 0 or players[0]["steamid"] != steamid64:
            raise Exception("Invalid or unknown steamid64 " + steamid64)

        return players[0]

    def nowGaming(self, irc, msg, args, nickname):
        """takes no or one argument(s) (nickname)

        Displays currently played game on steam.
        """

        name = nickname or msg.nick
        steamid = self.db.getId(name)

        if not steamid:
            return irc.error("No steamaccount is linked to nickname " + name + ".")

        status = self.fetch_summary(steamid)
        game = "is playing " + status["gameextrainfo"] if "gameextrainfo" in status else "isn't playing any game"

        return irc.reply(name + " (Steampersona: " + status["personaname"] + ") " + game + " right now!")

    ng = wrap(nowGaming, [optional("something")])
    nowgaming = wrap(nowGaming, [optional("something")])

    def setSteamID(self, irc, msg, args, steamid):
        """takes one argument <steamid>

        Links your nickname to your steam profile id (steamid64).
        """

        if not steamid:
            return irc.error("SteamID (steamid64) is required. You may use http://steamidconverter.com/ to get it.")

        status = self.fetch_summary(steamid)

        self.db.set(msg.nick, status["steamid"])

        return irc.reply("SteamID set to " + status["steamid"] + "!")

    setsteamid = wrap(setSteamID, [optional("something")])


class SteamUserDB(plugins.ChannelUserDB):
    """Holds the 64bit steam id with the corresponding nickname"""

    def __init__(self, *args, **kwargs):
        plugins.ChannelUserDB.__init__(self, *args, **kwargs)

    def serialize(self, v):
        return list(v)

    def deserialize(self, channel, id, L):
        (id,) = L
        return (id,)

    def set(self, nick, id):
        self['steamid', nick.lower()] = (id,)

    def getId(self, nick):
        try:
            return self['steamid', nick.lower()][0]
        except:
            return 

dbfilename = conf.supybot.directories.data.dirize("steamid.db")

Class = Steam

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79: