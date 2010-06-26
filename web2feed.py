#!/usr/bin/env python2.6
# Brandon Thomas 2010
# http://possibilistic.org
# web2feed
# BSD/MIT licensed.

# TODO: Figure out how to modularize for each site
# TODO: JSON payloads

import sys
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
import os
from datetime import datetime, timedelta

try:
	from StringIO import StringIO
except:
	from cStringIO import StringIO

import simplejson as json # req python2.5

def fix_uri(uri):
	"""Fix a partial URI (eg. no scheme, etc.)"""
	u = urlparse(uri)
	if not u.scheme:
		u = urlparse(urljoin('http://', '//' + u.geturl()))
	return u.geturl()

def get_page(uri, timeout=10):
	"""Get the page from online or the cache."""

	def download(uri, timeout=10):
		"""Download the contents at the URI specified."""
		u = urlparse(uri)
		c = httplib.HTTPConnection(u.netloc, timeout=timeout)
		c.request('GET', u.path)
		resp = c.getresponse()
		return resp.read()

	cache = PageCache(uri)
	if cache.exists():
		if cache.expired():
			try:
				content = download(uri, timeout)
				cache.write(content)
				return content
			except:
				print "Download failed."
		return cache.read()
	else:
		content = download(uri, timeout)
		cache.write(content)

def map_domain_to_module(domain):
	"""A router to the site-specific rules."""
	pass

class Scraper(object):
	"""Scrape the content off a page."""
	def __init__(self, contents):
		# HTML DOM Tree
		self.soup = self._parse(contents)

		# Parsed out feed content
		self.feed = self._extract_feed()

	def get_feed(self):
		"""Get the feed."""
		return self.feed

	def get_json(self):
		"""Get the feed serialized in JSON."""
		# Properly handle datetime objects
		dthandle = lambda o: o.isoformat() if isinstance(o, datetime) else None
		return json.dumps(self.feed, default=dthandle)

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
			content = self._parser_fallback(content)
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

class PageCache(object):
	"""Caches pages so it's faster to develop scraping logic for
	different websites. This feature isn't necessary in production."""

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

def get_scraper(content, uri):
	"""Dispatcher for fetching appropriate scraper."""
	from sites.slashdot import get_scraper as gs
	return gs(content)

def main():
	uri = fix_uri(sys.argv[1])
	content = get_page(uri)

	sc = get_scraper(content, uri)
	data = sc.get_feed()
	print data

	#map_domain_to_module(domain)

if __name__ == '__main__':
	main()

