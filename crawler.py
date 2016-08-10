# -*- coding: utf-8 -*-
import re
import random
import argparse
import datetime
import cookielib

import colorama
import requests
from bs4 import BeautifulSoup
from termcolor import colored
from openpyxl import Workbook

from auth import Logging, is_login


class cached_property(object):

    """A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


class Header(object):

    """Generate header dict for request"""

    @staticmethod
    def get_header():
        User_Agents = [
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11',
            'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
        ]
        header = {
            'User-Agent': random.choice(User_Agents),
            'Host': "www.goodreads.com",
            'Origin': "https://www.goodreads.com",
        }
        return header


class Book(object):

    def __init__(self, url, page=1):
        type_str = url.split('/')[-3].title()
        constructor = globals()[type_str]
        self.deputy = constructor(url, page=page)

    @cached_property
    def titles(self):
        return self.deputy.get_titles()

    @cached_property
    def authors(self):
        return self.deputy.get_authors()

    @cached_property
    def avg_ratings(self):
        return self.deputy.get_avg_ratings()

    @cached_property
    def rating_counts(self):
        return self.deputy.get_rating_counts()

    @cached_property
    def published_year(self):
        return self.deputy.get_published_year()

    def save_to_excel(self, path):
        wb = Workbook()
        ws = wb.active

        ws.append(['title', 'author', 'avg_rating',
                   'rating_counts', 'published_year'])

        for title in self.titles:
            ws.append([title,
                       self.authors.next(),
                       self.avg_ratings.next(),
                       self.rating_counts.next(),
                       self.published_year.next()
                       ])

        save_path = path + '.xlsx'
        wb.save(save_path)


class Shelf(object):

    def __init__(self, url=None, genre=None, page=1):
        if url:
            if not re.compile(r"(http|https)://www.goodreads.com/shelf/show/.+?").match(url):
                raise ValueError('Not a shelf url')
            url = url.rsplit('?page')[0]
        if genre:
            url = 'https://www.goodreads.com/shelf/show/' + genre

        self.url = url + '?page=' + str(page)
        self.page = page

    def _get_content(self):
        r = requests.get(self.url, headers=Header.get_header(), verify=False)
        return BeautifulSoup(r.content)

    @cached_property
    def book_units(self):
        """Get list of book infomation

        :return: bs4 object
        """
        soup = self._get_content()
        units = soup.select(".leftContainer .elementList")
        return units

    def get_titles(self):
        for soup in self.book_units:
            title = soup.find("a", {"class": "bookTitle"}).text
            yield title

    def get_authors(self):
        for soup in self.book_units:
            author = soup.find("span", {"itemprop": "name"}).text
            try:
                yield author
            except IndexError:
                yield None

    def get_avg_ratings(self):
        for soup in self.book_units:
            extra_info = soup.find(
                "span", {"class": "greyText smallText"}).text
            try:
                yield re.findall(r"rating.(.+?)\s", extra_info)[0]
            except IndexError:
                yield None

    def get_rating_counts(self):
        for soup in self.book_units:
            extra_info = soup.find(
                "span", {"class": "greyText smallText"}).text
            try:
                yield re.findall(r"(?<=\s).+?(?=ratings)", extra_info)[0]
            except IndexError:
                yield None

    def get_published_year(self):
        for soup in self.book_units:
            extra_info = soup.find(
                "span", {"class": "greyText smallText"}).text
            try:
                yield re.findall(r"published.(.+?)\s", extra_info)[0]
            except IndexError:
                yield None


class List(object):

    def __init__(self, url, page=1):
        if not re.compile(r"(http|https)://www.goodreads.com/list/show/.+?").match(url):
            raise ValueError('Not a shelf url')

        url = url.rsplit('?page')[0]
        self.url = url + '?page=' + str(page)

    def _get_content(self):
        r = requests.get(self.url, headers=Header.get_header(), verify=False)
        return BeautifulSoup(r.content)

    @cached_property
    def book_units(self):
        """Get list of book infomation

        :return: bs4 object
        """
        soup = self._get_content()
        units = soup.find_all("tr", {"itemtype": "http://schema.org/Book"})
        return units

    def get_titles(self):
        for soup in self.book_units:
            title = soup.select(".bookTitle span[itemprop]")[0].text
            yield title

    def get_authors(self):
        for soup in self.book_units:
            author = soup.select(".authorName span[itemprop]")[0].text
            try:
                yield author
            except IndexError:
                yield None

    def get_avg_ratings(self):
        for soup in self.book_units:
            extra_info = soup.find("span", {"class": "minirating"}).text
            try:
                yield re.findall(r"(?<=\s).+?(?=avg)", extra_info)[0]
            except IndexError:
                yield None

    def get_rating_counts(self):
        for soup in self.book_units:
            extra_info = soup.find("span", {"class": "minirating"}).text
            try:
                yield re.findall(r"(?<=\s).+?(?=ratings)", extra_info)[0]
            except IndexError:
                yield None

    def get_published_year(self):
        return None


if __name__ == '__main__':
    parse = argparse.ArgumentParser(description='Crawl book infomation')
    parse.add_argument('url', help='url to crawl')
    parse.add_argument('path', help='path to save book info')
    parse.add_argument('-p', '--page', help='specific page you want to crawl',
                       type=int, default=1)
    args = parse.parse_args()

    colorama.init()

    requests = requests.Session()
    requests.cookies = cookielib.LWPCookieJar('cookies')
    try:
        requests.cookies.load(ignore_discard=True)
    except IOError:
        Logging.error('run auth.py to log in')
        raise Exception('have not been authenticated')

    if not is_login():
        Logging.error('cookies have expired, please run auth.py again')
        raise Exception('have not been authenticated')

    book = Book(args.url, args.page)
    book.save_to_excel(args.path)
