from web2feed import Scraper

import re
from datetime import datetime

class AaronSwartzBlogScraper(Scraper):
	"""Scraper for Aaron Swartz blog."""

	def _extract_feed(self):
		container = self.soup.find('td', attrs={'class':'content'})

		# Aaron's blog requires event-parsing
		stories = []
		curStory = None
		for tag in container:
			try:
				if not tag.name:
					continue
			except:
				continue

			if tag.name == 'h2':
				if curStory and curStory['title'] and curStory['uri']:
					stories.append(curStory)
				curStory = {
					'title': None,
					'uri': None,
					'date': None,
					'contents': '',
					'author': 'Aaron Swartz', # TODO openid
				}
				try:
					a = tag.find('a', rel='bookmark')
					curStory['title'] = a.text
					curStory['uri'] = 'http://www.aaronsw.com/weblog/%s' % a.attrMap['href']

				except:
					pass

				continue

			try:
				if tag['class'] == 'posted':
					date = tag.a.text
					date = re.sub('\s+', ' ', date).strip()
					curStory['date'] = datetime.strptime(date, '%B %d, %Y')
					continue
			except:
				pass

			if tag:
				curStory['contents'] += unicode(tag)

		return stories

