import urllib.request
from lxml import etree
from helper import Pool
from pprint import pprint

POOL_SIZE = 10

BASE_URL_LINES = "http://timeo3.keolis.com/relais/217.php?xml=1"
BASE_URL_STOPS = "http://timeo3.keolis.com/relais/217.php?xml=3"

# Create a list of tuples.
# Each tuple is made of n successive elements
def grouped(iterable, n):
	return list(zip(*[iter(iterable)]*n))

def get_xml_from_url(url):
	result = urllib.request.urlopen(url)
	try:
		return etree.fromstring(result.read())
	except etree.XMLSyntaxError:
		print("Not only XML in response from :\n    "+url)

def get_from_xml(url, xpath):
	root = get_xml_from_url(url)
	return root.xpath(xpath)

def get_lines(url):
	lines = get_from_xml(
		url,
		"//ligne/*[self::code or self::sens]/text()"
	)
	return grouped(lines, 2)

def get_stops(url):
	stops = get_from_xml(
			url,
			"//arret/nom/text() | //refs/text()"
		)
	return grouped(stops, 2)

def get_times(stop):
	name = stop[0]
	refs = stop[1]
	ref = iter(refs.split("|"))
	results = []
	while not results:
		try:
			id = next(ref)
		except StopIteration:
			break
		url = BASE_URL_STOPS+"&refs="+id+"&ran=1"
		results = tuple(get_from_xml(url,"//duree/text()"))
	if len(results):
		return results

def process_stops(stops):
	with Pool(POOL_SIZE) as p:
		results = p.map(get_times, stops)
	return results
	


if __name__ == "__main__":

	lines = get_lines(BASE_URL_LINES)

	lines_urls = [
					BASE_URL_LINES+"&ligne="+line+"&sens="+way
					for line, way in lines
				]

	with Pool(POOL_SIZE) as p:
		stops_list = p.map(get_stops, lines_urls)

	with Pool(POOL_SIZE) as p:
		results = p.map(process_stops, stops_list)

	pprint(results)
