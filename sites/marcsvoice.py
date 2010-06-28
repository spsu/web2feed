from web2feed import Scraper, fix_uri, remove_ordinal

import re
from datetime import datetime

class MarcsVoiceScraper(Scraper):
	"""Scraper for Marc Canter's blog,
	http://blog.broadbandmechanics.com"""

	def _extract_feed(self):
		posts = self.soup.findAll('div', id=re.compile('post-\d+'))

		stories = []
		for p in posts:
			try:
				a = p.find('a', attrs={'rel':re.compile('bookmark')})
				d = p.find('div', attrs={'class':'post-details'})
				cts = p.findAll('p')

				# Lack of semantics is why we can't have nice things...
				date = None
				time = None
				for x in d:
					try:
						x = x.strip()
					except:
						continue

					x = x.replace('|', '').strip()

					# TODO: Really need to write a date parser module
					x = remove_ordinal(x)
					parse_date = None
					parse_time = None
					try:
						parse_date = datetime.strptime(x, "%A, %B %d, %Y")
					except Exception as e:
						pass
					try:
						parse_time = datetime.strptime(x, "%I:%M %p")
					except:
						pass

					if parse_date:
						date = parse_date
					if parse_time:
						time = parse_time

				title = a.text
				link = a.attrMap['href']
				try:
					date = datetime.combine(date, time.time())
				except Exception as e:
					pass #print e

				# extraction of text contents, again *semantics*
				contents = ''
				for t in cts:
					contents += unicode(t).strip()

				stories.append({
						'uri': link,
						'title': title,
						'date': date,
						'contents': contents
					})

			except Exception as e:
				print e
				continue

		return stories

def get_scraper(content):
	return MarcsVoiceScraper(content)

