from web2feed import Scraper, fix_uri, remove_ordinal

import re
from datetime import datetime

class TechDirtScraper(Scraper):
	"""Scraper for Techdirt"""

	def _extract_feed(self):
		posts = self.soup.findAll('div', attrs={'class':'storyblock'})

		stories = []
		for p in posts:
			try:
				h = p.find('h1')
				d = p.find('p', attrs={'class':'storydate'})
				cts = p.find('div', attrs={'class':'story'})

				title = h.a.text
				link = 'http://techdirt.com' + h.a['href']
				date = remove_ordinal(d.text)
				date = datetime.strptime(date, "%a, %b %d %Y %I:%M%p")
				contents = ''
				for t in cts.contents:
					try:
						if t.name in ['h1', 'h3']:
							continue
						if t['style']:
							continue
					except:
						pass
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


