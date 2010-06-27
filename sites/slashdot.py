from web2feed import Scraper, fix_uri

import re
from datetime import datetime

class SlashdotScraper(Scraper):
	"""Scraper logic for Slashdot.org

	Index Pages
	-----------
		for item in items:
			item.uri
				.title
				.date
				.contents

	Story Pages
	-----------
		TODO
	"""

	def _extract_feed(self):
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


#def get_scraper(contents):
#	return SlashdotScraper(contents)

