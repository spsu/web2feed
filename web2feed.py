#!/usr/bin/env python2.6
# Brandon Thomas 2010
# web2feed
# BSD/MIT licensed. 

import sys
from urlparse import urlparse, urljoin
import httplib
from BeautifulSoup import BeautifulSoup
import libxml2
from lxml import etree
import html5lib
from html5lib import sanitizer, treebuilders

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

def download(uri):
	"""Download the contents at the URI specified."""
	u = urlparse(uri)
	c = httplib.HTTPConnection(u.netloc)
	c.request('GET', u.path)
	resp = c.getresponse()
	return resp.read()

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
		#t = self.soup.findAll('div', id=r'^text-*')
		t = self.soup.findAll('div')
		#t = self.soup.findAll(attrs={'id' : r'text'})
		#print self.soup.findAll('b')
		#print self.soup.prettify()
		#print self.soup
		print t


def main():
	uri = fix_uri(sys.argv[1])
	content = download(uri)
	sc = SlashdotScraper(content)
	sc.get_feed()

	#map_domain_to_module(domain)

if __name__ == '__main__':
	main()

