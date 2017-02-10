import ConfigParser, os.path, sys, os
import TailBot, SlackTailBot, FollowTail
from twisted.internet import reactor
from twisted.python import log
log.startLogging(sys.stdout)

def setup_irc(config, followers):
    try:
        server = config.get('ircd', 'server')
        port = config.getint('ircd', 'port')
        ssl = config.getboolean('ircd', 'ssl')
        channels = [c.strip() for c in config.get('ircd', 'channel').split(',')]
        nickname = config.get('ircd', 'nickname')
    except Exception as e:
        print "Invalid Configuration Directives! [%s]" % e
        sys.exit()

    print "Connecting to %s:%i [ssl=%s] as %s" % (server, port, ssl, nickname)
    print "Joining: %s" % (', '.join(channels))

    factory = TailBot.TailBotFactory(channels, nickname)
    for follower in followers:
        factory.addTailFollower(follower)

    if ssl:
        from twisted.internet import ssl
        reactor.connectSSL(server, port, factory, ssl.ClientContextFactory())
    else:
        reactor.connectTCP(server, port, factory)

def setup_slack(config, followers):
    try:
        url = config.get('slack', 'webhook')
        nickname = config.get('slack', 'nickname')
        channel = config.get('slack', 'channel')
    except Exception as e:
        print "Invalid Configuration Directives! [%s]" % e
        sys.exit()

    print "Sending to slack webhook URL: %s as %s" % (url, nickname)

    bot = SlackTailBot.SlackTailBot(url, nickname, channel)
    for follower in followers:
        bot.addTailFollower(follower)

def main():
    try:
        configFile = sys.argv[1]
    except:
        configFile = 'config.cfg'

    try:
        config = ConfigParser.ConfigParser()
        config.read(configFile)
    except:
        print "Config File Not Found! [%s]" % configFile
        os.exit()

    try:
        directory = config.get('files', 'directory')
        files = [f.strip() for f in config.get('files', 'filenames').split(';')]
    except Exception as e:
        print "Invalid Configuration Directives! [%s]" % e
        sys.exit()

    print "[TailBot] starting with config file [%s]" % configFile
    print "Tailing: %s" % (', '.join(files))

    followers = [FollowTail.FollowTail(directory, file) for file in files]

    if config.has_section('ircd'):
        setup_irc(config, followers)
    if config.has_section('slack'):
        setup_slack(config, followers)

    reactor.run()

if __name__ == "__main__":
    main()
