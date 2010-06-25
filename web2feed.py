#!/usr/bin/env python2.6
# Brandon Thomas 2010
# http://possibilistic.org
# web2feed
# BSD/MIT licensed. 

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
		self.soup = self.parse(contents)

	def get_feed(self):
		pass

	def parse(self, content):
		"""Parse HTML content with BeautifulSoup."""
		try:
			return BeautifulSoup(content)
		except:
			print "HTMLParser error. Trying libxml."
			content = self.parser_fallback(content)
			f = open('out', 'w')
			f.write(content)
			f.close()
			return BeautifulSoup(content)
			#self.soup = content

	def parser_fallback(self, content):
		"""If BeautifulSoup's parser fails, try libxml."""
		parser = html5lib.HTMLParser(
					tree=treebuilders.getTreeBuilder('beautifulsoup'))
		soup = parser.parse(StringIO(content))
		return soup.prettify()

class SlashdotScraper(Scraper):
	"""Slashdot"""
	def get_feed(self):
		# Get stories

		divs = self.soup.findAll(attrs={
						'id': re.compile('^firehose-'),
						'class': re.compile('article')
				})

		stories = []
		for d in divs:
			head = d.find(attrs={'class': 'datitle'})
			cts = d.find(id=re.compile('text-'))
			date = d.find(id=re.compile('fhtime-'))

			link = fix_uri(head.attrMap['href'])
			title = head.text

			contents = ' '.join(unicode(t) for t in cts).strip()
			#stories.append(st)
			#stories_plain = cts.text

			# TODO: Get year somehow...
			date = date.text[3:]
			date = datetime.strptime(date, "%A %B %d, @%I:%M%p")
			date = date.replace(year=2010) # XXX: Get year 
			stories.append({
					'uri': link,
					'title': title,
					'date':	date,
					'contents':	contents,
				})

		return stories

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

def main():
	uri = fix_uri(sys.argv[1])
	content = get_page(uri)

	sc = SlashdotScraper(content)
	sc.get_feed()

	#map_domain_to_module(domain)

if __name__ == '__main__':
	main()

