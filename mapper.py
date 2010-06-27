from urlparse import urlparse
import sys

def simplify_uri(uri):
	"""Removes 'www', etc."""
	up = urlparse(uri)
	hostsplit = up.hostname.split('.')
	domain = ''
	for p in hostsplit:
		if p is 'www':
			continue
		domain += '.' + p

	if not domain:
		return uri

	return domain[1:]

def get_scraper(content, uri):
	"""Map the URI to the appropriate scraper class."""
	dom = simplify_uri(uri)
	mod = None

	print "simplified uri: %s" %dom

	# Major sites
	if dom in ['slashdot.org', 'linux.slashdot.org']:
		mod = 'slashdot'
	elif dom == 'reddit.com':
		mod = 'reddit'

	# Major blogs
	elif dom == 'scobleizer.com':
		mod = 'scobleizer'

	elif dom == 'blog.broadbandmechanics.com':
		mod = 'marcsvoice'

	print "module: %s" %mod

	if not mod:
		return False

	mod = 'sites.' + mod

	module = __import__(mod)
	module = sys.modules[mod]
	return module.get_scraper(content)

