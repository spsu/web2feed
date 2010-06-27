from urlparse import urlparse
import sys

def get_scraper(content, uri):
	"""Map the URI to the appropriate scraper class."""
	dom = simplify_uri(uri)
	mod = None

	print "simplified uri: %s" %dom

	# Mapping
	mapp = {
		'.aaronsw.com': 'aaronsw',
		'.broadbandmechanics.com': 'marcsvoice',
		'.lesswrong.com': 'lesswrong',
		'.reddit.com': 'reddit',
		'.scobleizer.com': 'scobleizer',
		'.slashdot.org': 'slashdot',
	}

	dom = '.' + dom
	for k in mapp:
		if dom.endswith(k):
			mod = mapp[k]
			break

	print "module: %s" %mod

	if not mod:
		return False

	mod = 'sites.' + mod

	module = __import__(mod)
	module = sys.modules[mod]

	try:
		return module.get_scraper(content)
	except AttributeError:
		return anonymous_inst(module, content)

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

def anonymous_inst(module, content):
	"""Instantiate scraper anonymously."""
	from web2feed import Scraper
	cls = None
	for x in dir(module):
		z = getattr(module, x)
		try:
			if issubclass(z, Scraper):
				if x not in ['Scraper', 'web2feed.Scraper']:
					cls = x
					break
		except:
			pass

	if not cls:
		print "Anonyomous instance not found"
		return

	return getattr(module, cls)(content)

