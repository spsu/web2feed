#!/usr/bin/env python2.6
# Brandon Thomas <echelon@gmail.com>
# http://possibilistic.org
# Web2Feed, a work in progress web scraping tool.
# http://github.com/echelon/web2feed
# Copyright 2010. BSD/MIT licensed.
# Utilizes GPL-licensed code, so combined distribution is GPL.

import os
import sys

# Not sure if this is a good idea...
sys.path.insert(0, os.path.abspath('./libs'))

from urlparse import urlparse, urljoin
import httplib
from BeautifulSoup import BeautifulSoup
import re

# For fixing what BeautifulSoup can't parse.
import html5lib
from html5lib import sanitizer, treebuilders

# For PageCache
import time
import hashlib
from datetime import datetime, timedelta

try:
	from StringIO import StringIO
except:
	from cStringIO import StringIO

import simplejson as json # req python2.5
from libs import iso8601
from libs.robotexclusionrulesparser import RobotExclusionRulesParser

import htmlentitydefs # for terminal output
import textwrap # for terminal output
from libs.html2text import html2text # XXX: GPL LICENSED!


from mapper import get_scraper

# ============ Library API ======================

# TODO/XXX: DEPRECATE web2feed()
def web2feed(uri, content=False, timeout=15, redirect_max=2, cache=False):
	"""Deprecated API for web2feed. Content can be passed or downloaded
	by web2feed."""
	wf = Web2Feed(uri)

	if content:
		wf.set_contents(content)
	else:
		wf.set_caching(cache)

	return wf.get_feed()

class Web2Feed(object):
	"""Web2Feed, an API for scraping websites for content."""

	def __init__(self, uri, contents=''):
		"""Supply the URI and optionally prefetched content."""
		self.uri = fix_uri(uri)
		self.contents = contents
		self.uagent = 'web2feed.py (http://github.com/echelon/web2feed) -- ' \
						'Scraping content for the distributed web'
		self.robot_rules_str = ''

		# Robots.txt rules policy
		self.obey_rules = True
		self.allow_on_fail = True

		# Page caching rules (same for requested page and robots.txt)
		self.use_caching = False
		self.cache_timeout = timedelta(minutes=10)
		self.cache_dir = './cache'

		# If prefetched content not supplied, autofetch?
		self.do_auto_fetch = True
		self.do_auto_fetch_rules = True

		# Cached scraper, purged if contents set or fetched.
		self.scraper = None

	def set_contents(self, contents):
		"""Supply externally-fetched content."""
		self.contents = contents
		self.do_auto_fetch = False
		self.do_auto_fetch_rules = False
		self.scraper = None

	def get_contents(self):
		return self.contents

	def set_uagent(self, uagent):
		"""Set the user-agent for fetching content."""
		self.uagent = uagent

	def set_robot_rules(self, rules_str):
		"""Supply the robots.txt file if externally-fetched."""
		self.robot_rules_str = rules_str
		self.do_auto_fetch_rules = False

	def get_robot_rules(self):
		return self.robot_rules_str

	def set_robot_rules_policy(self, obey_rules, allow_on_fail=True):
		"""Set he robot.txt rules policy."""
		self.obey_rules = obey_rules
		self.allow_on_fail = allow_on_fail

	def set_caching(self, use_caching, cache_timeout=timedelta(minutes=10),
			cache_dir='./cache'):
		self.use_caching = use_caching
		self.cache_timeout = cache_timeout
		self.cache_dir = cache_dir

	def fetch(self, timeout=15, redirect_max=2):
		"""Fetch the page with web2feed's libraries."""
		self.do_auto_fetch = False
		self.scraper = None

		# Robots.txt handling
		if self.obey_rules:
			if self.do_auto_fetch_rules:
				self.fetch_rules(timeout, redirect_max)

			if not self.robot_rules_str and not self.allow_on_fail:
				print "robots.txt could not be fetched, but policy " \
						"indicates we must obtain it."
				return False

			if self.robot_rules_str and not \
				robot_is_allowed(self.uri, self.uagent,
					rules_str=self.robot_rules_str):
						print "robots.txt indicates we cannot download " \
								"the resource at '%s'" % self.uri
						return False

		# TODO: Error handling
		contents = get_page(self.uri,
						timeout=timeout,
						redirect_max=redirect_max,
						caching=self.use_caching,
						cache_period=self.cache_timeout,
						cache_dir=self.cache_dir,
						uagent=self.uagent)

		self.contents = contents

	def fetch_rules(self, timeout=15, redirect_max=2):
		"""Fetch the robots.txt with web2feed's libraries."""
		self.do_auto_fetch_rules = False
		robots_uri = urljoin(self.uri, '/robots.txt')

		# TODO: Error handling
		rules = get_page(robots_uri,
					timeout=timeout,
					redirect_max=redirect_max,
					caching=self.use_caching,
					cache_period=self.cache_timeout,
					cache_dir=self.cache_dir,
					uagent=self.uagent)

		self.robot_rules_str = rules

	def get_feed(self):
		"""Scrape the page for semantic content."""
		def get_formatted(scraper):
			return {
				'meta': scraper.get_meta(),
				'feed': scraper.get_feed(),
			}

		if self.scraper:
			return get_formatted(self.scraper)

		if not self.contents and self.do_auto_fetch:
			print "Web2Feed.get_feed() Attempting to fetch..."
			self.fetch()

		if not self.contents:
			#raise Exception, "No content to scrape!"
			print "Web2Feed.get_feed() unable to parse: no contents!"
			return False

		# TODO: Cache the scraper.
		self.scraper = get_scraper(self.contents, self.uri)
		return get_formatted(self.scraper)

# ============ Run from terminal ================

def main():

	wf = Web2Feed(sys.argv[1])

	wf.set_caching(True)
	wf.set_robot_rules_policy(True, False)

	print wf.get_feed()


	sys.exit()
	content = get_page(uri)
	print "Content len: %d" % 0 if not content else len(content)
	sc = get_scraper(content, uri)

	#print sc.get_feed()
	print sc.get_plaintext(80)

	#map_domain_to_module(domain)

# ============ Downloading / Caching ============

def get_page(uri, timeout=10, redirect_max=2, caching=True, uagent=None,
			cache_period=timedelta(minutes=10),
			cache_dir='./cache', cache_ext='.html'):
	"""Get the page from online or the cache."""

	# TODO: KeepAlive connections to host for batch fetching 
	# of multiple pages or media

	# ======== Nested Definitions ===============

	def download(uri, timeout=10, redirect_max=2, redirect_cnt=0, uagent=None):
		"""Download the contents at the URI specified."""
		print "Downloading %s ..." % uri
		u = urlparse(uri)
		c = httplib.HTTPConnection(u.netloc, timeout=timeout)
		if uagent==None:
			uagent = 'web2feed.py (http://github.com/echelon/web2feed) ' \
						'-- Scraping content for the distributed web'
		h = {'User-Agent': uagent}
		c.request('GET', u.path, headers=h)
		resp = c.getresponse()

		if (300 <= resp.status < 400):
			if redirect_cnt > redirect_max:
				raise Exception, "Too many redirects."

			# TODO: Handle relative locations.
			newloc = resp.getheader('location')
			return download(newloc, timeout, redirect_max, redirect_cnt+1)
		else:
			return resp.read()

	class PageCache(object):
		"""Caches pages so it's faster to develop scraping logic for
		different websites. This feature isn't necessary in
		production."""

		PREFIX = './cache'
		SUFFIX = '.html'

		def __init__(self, uri):
			self.uri = uri

		def filename(self):
			"""Get the cache filename."""
			hname = hashlib.md5(self.uri).hexdigest()
			return self.PREFIX + '/' + hname + self.SUFFIX

		def exists(self):
			"""Does the cache file exist?"""
			return os.path.exists(self.filename())

		def expired(self, td=timedelta(minutes=10)):
			"""Has the cache file gone stale?"""
			try:
				ts = os.path.getmtime(self.filename())
				time = datetime.fromtimestamp(ts)
				return datetime.today() > time + td
			except:
				return True

		def read(self):
			"""Read from the cache file."""
			f = open(self.filename(), 'r')
			c = f.read()
			f.close()
			return c

		def write(self, contents):
			"""Save to the cache file."""
			f = open(self.filename(), 'w')
			f.write(contents)
			f.close()

	# ======== Function Body ====================

	if not caching:
		try:
			return download(uri, timeout, redirect_max)
		except:
			print "Download failed."
			return False

	PageCache.PREFIX = cache_dir
	PageCache.SUFFIX = cache_ext

	cache = PageCache(uri)
	if cache.exists():
		if cache.expired(cache_period):
			try:
				content = download(uri, timeout, redirect_max, uagent)
				cache.write(content)
				return content
			except:
				print "Download failed."
		return cache.read()
	else:
		content = download(uri, timeout, redirect_max, uagent)
		cache.write(content)
		return content

# ============ Robots.txt Rule Checking =========

def robot_is_allowed(uri, uagent, allow_on_fail=True, rules_str='', cache=True,
		cache_period=timedelta(minutes=10)):
	"""Check if the robot is allowed to fetch the desired URI.
	The URI must be absolute.
	Can make decision policy when robots.txt  was unable to be fetched.
	Can supply the already-fetched rules string. If letting web2feed
	download robots.txt, it can be cached."""

	if not rules_str:
		robots_uri = urljoin(uri, '/robots.txt')
		# TODO: better check.
		if robots_uri == '/robots.txt':
			print 'Non-absolute uri for robot_is_allowed: %s' % uri
			return allow_on_fail

		print 'ROBOT URI: %s' % robots_uri
		rules_str = get_page(robots_uri, caching=cache,
							cache_period=cache_period)

	if not rules_str:
		return allow_on_fail

	rparse = RobotExclusionRulesParser()
	rparse.parse(rules_str)
	return rparse.is_allowed(uagent, uri)

# ============ Scraping Content =================

class Scraper(object):
	"""Scrape the content off a page."""
	def __init__(self, contents, uri):
		# Web location page was downloaded from (if known)
		self.uri = uri

		# HTML DOM Tree.
		# Only used in parsing.
		self.soup = self._parse(contents)

		# Meta information such as <title> and description
		self.meta = {}

		# Parsed out feed content
		# Used for any presentation. 
		# TODO: Do cleaning, etc. on this.
		self.feed = self._extract_feed()

		# TODO: Bad form
		self._guess_format()
		self._add_markdown()

	def _guess_format(self):
		"""Guess the format of the data returned."""
		for i in range(len(self.feed)):
			x = self.feed[i]
			guess_contents = not 'contents_format' in x
			guess_summary = not 'summary_format' in x

			if 'contents' in x and guess_contents:
				if re.search(r'<\w+>', x['contents']):
					x['contents_format'] = 'text/html'
				else:
					x['contents_format'] = 'text/plain'

			if 'summary' in x and guess_summary:
				if re.search(r'<\w+>', x['summary']):
					x['summary_format'] = 'text/html'
				else:
					x['summary_format'] = 'text/plain'

	def _add_markdown(self):
		"""Add markdown version of the content."""
		for i in range(len(self.feed)):
			x = self.feed[i]
			if 'contents' in x:
				x['contents_markdown'] = html2text(x['contents'], self.uri)
			if 'summary' in x:
				x['summary_markdown'] = html2text(x['summary'], self.uri)

	def get_feed(self):
		"""Get the feed."""
		return self.feed

	def get_meta(self):
		"""Get the meta info."""
		return self.meta

	def get_json(self):
		"""Get the feed serialized in JSON."""
		# Properly handle datetime objects
		dthandle = lambda o: o.isoformat() if isinstance(o, datetime) else None
		return json.dumps(self.feed, default=dthandle)

	def get_plaintext(self, wrap=80):
		"""Output a feed to the terminal. This can be used for
		debugging or for reading/wasting time."""

		# TODO: multiple feed types.

		def format(title, date, author, contents, wrap):
			sz = 0
			lines = []
			if date and author:
				title += ' (by %s on %s)' % (author, date)
			elif date or author:
				title += ' (%s)' % ('on ' + date) if date else ('by ' + author)

			lines += textwrap.wrap(title, wrap)

			for ln in lines:
				s = len(ln)
				if s > sz:
					sz = s

			lines.append('-'*sz)
			lines += textwrap.wrap(contents, wrap)
			return '\n'.join(lines)

		def contents_or_summary(story):
			"""Get the contents or summary."""
			contents = ''
			if 'contents' in story:
				contents = story['contents']
			elif 'summary' in story:
				contents = story['summary']
			return contents

		feed = self.feed
		if type(feed) is dict:
			feed = [feed,]

		ret = ''
		for story in feed:
			cts = contents_or_summary(story)
			cts = ''.join(BeautifulSoup(cts).findAll(text=True)) # html->txt

			cts = entity_unescape(cts)
			title = entity_unescape(story['title'])

			date = ''
			if 'date' in story and story['date']:
				date = story['date'].strftime('%B %d, %H:%M')

			author = ''
			if 'author' in story and story['author']:
				author = story['author']

			ret += format(title, date, author, cts, wrap)
			ret += "\n\n"

		return ret

	def _extract_feed(self):
		"""Overload for parsing out the feed contents."""
		return None

	@staticmethod
	def _parse(content):
		"""Parse HTML content with BeautifulSoup."""
		try:
			return BeautifulSoup(content)
		except:
			print "HTMLParser error. Trying libxml."
			content = Scraper._parser_fallback(content)
			f = open('out', 'w')
			f.write(content)
			f.close()
			return BeautifulSoup(content)
			#self.soup = content

	@staticmethod
	def _parser_fallback(content):
		"""If BeautifulSoup's parser fails, try libxml."""
		parser = html5lib.HTMLParser(
					tree=treebuilders.getTreeBuilder('beautifulsoup'))
		soup = parser.parse(StringIO(content))
		return soup.prettify()

# ============ String Helper Funcs ==============

def fix_uri(uri):
	"""Fix a partial URI (eg. no scheme, etc.)"""
	u = urlparse(uri)
	if not u.scheme:
		u = urlparse(urljoin('http://', '//' + u.geturl()))
	return u.geturl()

def parse_iso_date(date_str):
	"""Wrapper around iso8601 library."""
	return iso8601.parse_date(date_str)

def remove_ordinal(date_str):
	"""Remove ordinal that datetime library can't parse."""
	return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

def entity_unescape(text):
	"""Turn htmlentities into unicode.
	From http://effbot.org/zone/re-sub.htm#unescape-html"""
	def fixup(m):
		text = m.group(0)
		if text[:2] == "&#":
			# character reference
			try:
				if text[:3] == "&#x":
					return unichr(int(text[3:-1], 16))
				else:
					return unichr(int(text[2:-1]))
			except ValueError:
				pass
		else:
			# named entity
			try:
				text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
			except KeyError:
				pass
		return text # leave as is
	return re.sub("&#?\w+;", fixup, text)

if __name__ == '__main__':
	main()

