from web2feed import Scraper

import re
from datetime import datetime

class BiologyNewsScraper(Scraper):
	"""Scraper for BiologyNewsNet (which I just found, but looks fun)"""

	def _extract_feed(self):
		posts = self.soup.findAll('div', attrs={'class':'article'})

		# Aside from table tag soup, this is the most semantic markup
		# I've seen so far. Very surprising. 
		stories = []
		for p in posts:
			try:
				h = p.find('h1')
				d = p.find('span', attrs={'class':'sort-date'})
				cts = p.find('div', attrs={'class':'post'})

				title = h.a.text
				link = h.a['href']
				date = datetime.strptime(d.text, "%B %d, %Y %I:%M %p")
				contents = ''
				for t in cts.contents:
					contents += unicode(t).strip()

				stories.append({
						'uri': link,
						'title': title,
						'date': date,
						'summary': contents
					})

			except Exception as e:
				raise e
				continue

		return stories


