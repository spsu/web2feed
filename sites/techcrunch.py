from web2feed import Scraper, fix_uri, remove_ordinal

import re
from datetime import datetime

class TechCrunchScraper(Scraper):
	"""Scraper for TechCrunch"""

	def _extract_feed(self):
		posts = self.soup.findAll('div', id=re.compile('post-\d+'))

		stories = []
		for p in posts:
			try:
				t = p.find('div', attrs={'class':re.compile('excerpt_header')})
				d = p.find('div', attrs={'class':'excerpt_subheader_left'})
				cts = p.find('div', attrs={'class':'entry'})

				# HTML really sucks. There is absolutely no care taken by
				# most authors to convey any kind of semantics--it is 
				# absolutely impossible to extract information easily!
				# Why do we have to do complex traversals within the DOM??

				date = None
				author = None
				contents = ''

				uri = t.a['href']
				title = t.a.text

				# Extract date and author
				for tag in d:
					try:
						if tag.name == 'a':
							author = tag.text
							continue
					except:
						pass

					try:
						tag = tag.replace('on', '').strip()
						tag = datetime.strptime(tag, '%b %d, %Y')
						date = tag
					except:
						pass

				# Extract contents
				for t in cts.contents:
					contents += unicode(t).strip()

				stories.append({
						'uri': uri,
						'title': title,
						'date': date,
						'author': author,
						'summary': contents
					})

			except Exception as e:
				print e
				continue

		return stories

