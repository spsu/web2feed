from web2feed import Scraper, fix_uri

import re
import datetime

class RedditScraper(Scraper):
	"""Scraper for reddit.com"""

	def _extract_feed(self):
		divs = self.soup.findAll('div', attrs={'class':re.compile('thing')})

		stories = []
		for d in divs:
			a1 = d.find('a', attrs={'class':re.compile('title')})
			a2 = d.find('a', attrs={'class':re.compile('comments')})

			try:
				link = a1.attrMap['href']
				title = a1.text
				comments_link = a2.attrMap['href']
			except:
				continue

			stories.append({
					'uri': link,
					'title': title,
					'comments_uri': comments_link,
					#'date': # TODO: how?
				})

		return stories

def get_scraper(content):
	return RedditScraper(content)

