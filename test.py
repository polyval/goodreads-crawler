# -*- coding: utf-8 -*-
from crawler import Shelf, Book, List


def test_shelf(url):
    shelf = Shelf(url)
    assert len(shelf.book_units) \
        == sum(1 for _ in shelf.get_titles()) \
        == sum(1 for _ in shelf.get_authors()) \
        == sum(1 for _ in shelf.get_avg_ratings()) \
        == sum(1 for _ in shelf.get_rating_counts()) \
        == sum(1 for _ in shelf.get_published_year())
    print shelf.get_titles()


def test_book(url, page=1):
    book = Book(url, page=page)
    # generator
    for title in book.titles:
        print title
    print book.titles
    print book.authors


def test_list(url):
    books = List(url)
    print books.get_titles()
    for title in books.get_titles():
        print title

    assert len(books.book_units) \
        == sum(1 for _ in books.get_titles()) \
        == sum(1 for _ in books.get_authors()) \
        == sum(1 for _ in books.get_avg_ratings()) \
        == sum(1 for _ in books.get_rating_counts())


def test_save(url):
    book = Book(url)
    book.save_to_excel('psychology')


def main():
    url = 'https://www.goodreads.com/shelf/show/psychology'
    # page = 2
    # test_shelf(url)
    # test_book(url, page=2)
    # list_url = 'https://www.goodreads.com/list/show/22031.Nonfiction_With_a_Side_of_Self_Help'
    # test_list(list_url)
    test_save(url)


if __name__ == '__main__':
    main()
    raw_input('Press Enter key to exit')
