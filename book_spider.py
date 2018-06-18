import scrapy
from scrapy.crawler import CrawlerProcess
import json
import os

from whoosh.fields import Schema, TEXT, STORED
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

class BookSpider(scrapy.Spider):
    name = "books"

    def start_requests(self):
        urls = [
            'http://books.toscrape.com/catalogue/page-1.html'
            'http://books.toscrape.com/catalogue/page-2.html',
            'http://books.toscrape.com/catalogue/page-3.html',
            'http://books.toscrape.com/catalogue/page-4.html',
            'http://books.toscrape.com/catalogue/page-5.html',
            'http://books.toscrape.com/catalogue/page-6.html',
            'http://books.toscrape.com/catalogue/page-7.html',
            'http://books.toscrape.com/catalogue/page-8.html',
            'http://books.toscrape.com/catalogue/page-9.html',
            'http://books.toscrape.com/catalogue/page-10.html',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = response.url.split("/")[-1][-6]
        filename = 'docs/books-%s.json' % page
        data = {}
        data['books'] = []
        books = response.css("article.product_pod")
        for book in books:
            name = book.css("h3").css("a::attr(title)").extract()[0]
            price = book.css("div.product_price").css("p.price_color::text").extract()[0][1:]
            availability = book.css("div.product_price").css("p")[1].css("p::text").extract()[1].strip()
            data['books'].append({
                'name': name,
                'price': price,
                'availability': availability
            })

        with open(filename, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        self.log('Saved file %s' % filename)

# scrape the given links executing the crawler
process = CrawlerProcess({'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'})
process.crawl(BookSpider)
process.start()

# create schema for index
schema = Schema(name=TEXT(stored=True), price=TEXT(stored=True), availability=TEXT(stored=True))

#creating the index
if not os.path.exists("index"):
    os.mkdir("index")

ix = create_in("index",schema)
ix = open_dir("index")
writer = ix.writer()

all_files = os.listdir("docs/")
# reading documents in the corpus
for i in all_files:
    json_file = open("docs/"+i)
    data = json.load(json_file)
    for p in data['books']:
        writer.add_document(name=p['name'], price=p['price'], availability=p['availability'])

writer.commit()

ix=open_dir("index")
searcher = ix.searcher()

# accepting user queries for text searching
print "Enter search query, type exit to quit"
user_q = ""
while user_q != 'exit':
    user_q = raw_input()
    query = QueryParser("name", ix.schema).parse(user_q)
    results = searcher.search(query)
    if len(results)==0:print "Nothing found"
    else:
        for result in results:
            print result

