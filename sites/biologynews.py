from web2feed import Scraper

import re
from datetime import datetime

class BiologyNewsScraper(Scraper):
	"""Scraper for BiologyNewsNet (which I just found, but looks fun)"""

	def _extract_feed(self):
		if not self.uri:
			print "BiologyNewsNet requires a URI to parse."

		if 'archive' in self.uri:
			return self._story_page()
		else:
			return self._feed_page()

	def _feed_page(self):
		"""Main feed page."""
		meta = {}
		meta['title'] = self.soup.find('title').text
		meta['description'] = self.soup.find('meta', attrs={'name':'description'})['content']

		self.meta = meta

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

	def _story_page(self):
		"""Single story page."""
		story = self.soup.find('div', attrs={'class':'article'})
		h = story.find('h1')
		d = story.find('div', attrs={'class':'utility'})
		cts = story.find('div', attrs={'class':'post'})

		title = h.a.text
		link = h.a['href']
		date = d.findAll('td')[0].text
		date = datetime.strptime(date, "%B %d, %Y %I:%M %p")
		contents = ''
		for t in cts.contents:
			try:
				cls = t['class']
				if cls in ['ad', 'relatedads']:
					continue
			except:
				pass
			try:
				typ = str(type(t))
				if 'Comment' in typ:
					continue
			except:
				pass
			contents += unicode(t).strip()

		story = {
				'uri': link,
				'title': title,
				'date': date,
				'contents': contents,
		}
		return story

