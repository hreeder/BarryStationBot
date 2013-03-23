#!/usr/bin/env python
import sys
import config, plugins
from twisted.words.protocols import irc
from twisted.internet import protocol, reactor, ssl


class BarryBot(irc.IRCClient):
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        print "Signed on as %s." % (self.nickname,)

        network = self.factory.network

        if network['identity']['nickserv_pw']:
            self.msg('NickServ', 'IDENTIFY %s' % (network[
                     'identity']['nickserv_pw'],))

            reactor.callLater(10, reactor.callInThread, self.joinChannels)
        else:
            joinChannels(self)

    def joinChannels(self):
        network = self.factory.network
        for channel in network['autojoin']:
            self.join(channel)

    def joined(self, channel):
        print "Joined %s." % (channel,)

    def privmsg(self, user, channel, msg):
        print "[%s] %s: %s" % (channel, user.split('!', 1)[0], msg,)
        if not user:
            return
        if self.nickname in msg:
            prefix = "%s: " % (user.split('!', 1)[0], )
        if config.trigger in msg[:1]:
            print "Command: %s" % msg.split()[0][1:]
            prefix = "%s: " % (user.split('!', 1)[0], )
        else:
            prefix = ''

        if prefix:
            self.msg(channel, prefix + "hello")
            print "[%s] %s: %s" % (channel, self.factory.network['identity']['nickname'], prefix + "hello",)

    def _get_nickname(self):
        return self.factory.network['identity']['nickname']

    def _get_realname(self):
        return self.factory.network['identity']['realname']

    def _get_username(self):
        return self.factory.network['identity']['username']
    nickname = property(_get_nickname)
    realname = property(_get_realname)
    username = property(_get_username)


class BarryBotFactory(protocol.ClientFactory):
    protocol = BarryBot

    def __init__(self, network_name, network):
        self.network_name = network_name
        self.network = network

    def ClientConnectionLost(self, connector, reason):
        print "Lost Connection (%s), reconnecting." % (reason)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)
        reactor.stop()

if __name__ == "__main__":
    for name in config.networks.keys():
        factory = BarryBotFactory(name, config.networks[name])

        host = config.networks[name]['host']
        port = config.networks[name]['port']
        reactor.connectTCP(host, port, factory)

    reactor.run()
