from web2feed import Scraper

import re
from datetime import datetime

class LessWrongScraper(Scraper):
	"""Scraper for LessWrong"""

	def _extract_feed(self):
		posts = self.soup.findAll('div', attrs={'class':re.compile('editors-pick')})

		stories = []
		for p in posts:
			try:
				h = p.find('h2')
				d = p.find('span', attrs={'class':'date'})
				cts = p.find('div', attrs={'class':'md'})

				title = h.a.text
				link = 'http://lesswrong.com' + h.a['href']

				date = datetime.strptime(d.text, "%d %B %Y %I:%M%p")
				contents = ''
				for t in cts.div:
					contents += unicode(t).strip()

				stories.append({
						'uri': link,
						'title': title,
						'date': date,
						'contents': contents
					})

			except Exception as e:
				raise e
				continue

		return stories


