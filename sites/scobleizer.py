from web2feed import Scraper, fix_uri, parse_iso_date

import re
import datetime

class ScobleizerScraper(Scraper):
	"""Scraper for Robert Scoble's blog,
	http://scobleizer.com"""

	def _extract_feed(self):
		posts = self.soup.findAll('div', attrs={'class':re.compile('post-')})

		stories = []
		for p in posts:
			try:
				a = p.find('a', attrs={'rel':re.compile('bookmark')})
				d = p.find('span', attrs={'class':'date time published'})
				cts = p.find('div', attrs={'class':'entry-content'})

				title = a.text
				link = a.attrMap['href']
				date = parse_iso_date(d.attrMap['title'])

				# crude extraction of text contents
				# XXX: Fixme, this is ugly
				contents = ''
				for t in cts:
					try:
						if t.attrMap['class'] == 'tweetmeme_button':
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
				#print e
				continue

		return stories

def get_scraper(content):
	return ScobleizerScraper(content)

