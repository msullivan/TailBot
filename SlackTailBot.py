#!/usr/bin/env python

from twisted.internet import reactor
from twisted.web.client import Agent, HTTPConnectionPool
from twisted.web.http_headers import Headers
from twisted.web.client import FileBodyProducer
from StringIO import StringIO
from collections import deque
import json
import FollowTail

from twisted.web import client
client._HTTP11ClientFactory.noisy = False #asdf.

TIMEOUT=10
RETRY=5

class SlackTailBot:
    def __init__(self, url, nickname, channel):
        self.url = url
        self.nickname = nickname
        self.channel = channel

        pool = HTTPConnectionPool(reactor)
        self.agent = Agent(reactor, pool=pool)
        self.req = None
        self.messages = deque()

    def build_message(self, line):
        cmd = {"channel": self.channel,
               "username": self.nickname,
               "text": line,
               "icon_emoji": ":ghost:"}
        return json.dumps(cmd)

    def fire_request(self):
        if self.req or not self.messages: return

        line = self.messages[0]
        message = self.build_message(line)
        body = FileBodyProducer(StringIO(message))

        self.req = self.agent.request(
            'POST',
            self.url,
            Headers({'Content-type': ['application/json']}),
            body)

        timeout = reactor.callLater(TIMEOUT, self.req.cancel)
        def cbResponse(resp):
            #print "response: %d: %s" % (resp.code, resp.phrase)
            self.messages.popleft()
            self.fire_request()
        def errResponse(err):
            print "error, will retry: %s" % err
            reactor.callLater(RETRY, self.fire_request)
        def cleanup(resp):
            timeout.cancel()
            self.req = None
            return resp

        self.req.addBoth(cleanup)
        self.req.addCallback(cbResponse)
        self.req.addErrback(errResponse)

    def send(self, line, filename):
        msg = '[%s] %s' % (filename, line)
        self.messages.append(msg)
        self.fire_request()

    def addTailFollower(self, tail):
        tail.callback.addCallback(self.send)
