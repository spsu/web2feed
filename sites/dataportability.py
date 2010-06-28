from web2feed import Scraper, fix_uri, remove_ordinal

import re
from datetime import datetime

class DataPortabilitycraper(Scraper):
	"""Scraper for DataPortability"""

	def _extract_feed(self):
		posts = self.soup.findAll('div', attrs={'class':'post'})

		stories = []
		for p in posts:
			try:
				t = p.find('h1')
				d = p.find('small')
				# Contents are included in parent...

				date = None
				author = None
				contents = ''
				is_summary = False # TODO

				uri = t.a['href']
				title = t.a.text

				# Extract date and author
				for tag in d:
					try:
						if tag.name == 'a' and tag['title'].startswith('Posts'):
							author = tag.text
							continue
					except:
						pass

					try:
						tag = tag.replace('|', '').strip()
						tag = remove_ordinal(tag)
						tag = datetime.strptime(tag, '%B %d, %Y')
						date = tag
					except:
						pass

				# Extract contents
				for t in p:
					try:
						if t.name in ['h1', 'small', 'hr']:
							continue
					except:
						pass
					contents += unicode(t).strip()

				stories.append({
						'uri': uri,
						'title': title,
						'date': date,
						'author': author,
						'contents': contents
					})

			except Exception as e:
				print e
				continue

		return stories

