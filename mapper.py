from urlparse import urlparse
import sys

def get_scraper(content, uri):
	"""Map the URI to the appropriate scraper class."""
	dom = simplify_uri(uri)
	mod = None

	print "simplified uri: %s" %dom

	# Major sites
	mmap = {
		'slashdot':
			['slashdot.org', 'linux.slashdot.org'],
		'reddit': 'reddit.com',
		'lesswrong': 'lesswrong.com'
	}

	for k, v in mmap.iteritems():
		if type(v) == str and dom == v:
			mod = k
			break
		if type(v) == list and dom in v:
			mod = k
			break

	# Personal blogs
	mapp = {
		'scobleizer.com': 'scobleizer',
		'blog.broadbandmechanics.com': 'marcsvoice',
		'aaronsw.com': 'aaronsw',
	}

	if dom in mapp:
		mod = mapp[dom]

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
	for x in dir(module):
		z = getattr(module, x)
		try:
			if issubclass(z, Scraper):
				if x not in ['Scraper', 'web2feed.Scraper']:
					inst = getattr(module, x)(content)
					return inst
		except:
			pass

