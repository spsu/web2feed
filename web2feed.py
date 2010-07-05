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
import iso8601 # included in lib

import htmlentitydefs # for terminal output
import textwrap # for terminal output

from mapper import get_scraper

# ============ Run from terminal ================

def main():
	uri = fix_uri(sys.argv[1])
	print "URI (fixed): %s" % uri
	content = get_page(uri)
	print "Content len: %d" % 0 if not content else len(content)
	sc = get_scraper(content, uri)

	#print sc.get_feed()
	print sc.get_plaintext(80)

	#map_domain_to_module(domain)

def web2feed(uri, content=False, timeout=15, redirect_max=2, cache=False):
	"""The main importable API for web2feed. Content can be passed
	or downloaded by web2feed."""
	uri = fix_uri(uri)

	if not content:
		content = get_page(uri,
						timeout=timeout,
						redirect_max=redirect_max,
						caching=cache)
	scraper = get_scraper(content, uri)

	ret = {
		'meta': scraper.get_meta(),
		'feed': scraper.get_feed(),
	}
	return ret

# ============ Downloading / Caching ============

def get_page(uri, timeout=10, redirect_max=2, caching=True,
			cache_dir='./cache', cache_ext='.html'):
	"""Get the page from online or the cache."""

	# TODO: KeepAlive connections to host for batch fetching 
	# of multiple pages or media

	# ======== Nested Definitions ===============

	def download(uri, timeout=10, redirect_max=2, redirect_cnt=0):
		"""Download the contents at the URI specified."""
		print "Downloading %s ..." % uri
		u = urlparse(uri)
		c = httplib.HTTPConnection(u.netloc, timeout=timeout)
		h = {'User-Agent':
				'web2feed.py (http://github.com/echelon/web2feed) -- ' + \
				'Scraping content for the distributed web'}
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
		if cache.expired():
			try:
				content = download(uri, timeout, redirect_max)
				cache.write(content)
				return content
			except:
				print "Download failed."
		return cache.read()
	else:
		content = download(uri, timeout, redirect_max)
		cache.write(content)
		return content

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

