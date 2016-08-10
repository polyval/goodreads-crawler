# -*- coding: utf-8 -*-
import os
import sys
import cookielib
from getpass import getpass
from ConfigParser import ConfigParser

import requests
from bs4 import BeautifulSoup
from termcolor import colored
import colorama


colorama.init()

requests = requests.Session()
requests.cookies = cookielib.LWPCookieJar('cookies')
try:
    requests.cookies.load(ignore_discard=True)
except IOError:
    pass


class Logging:
    """Print out message in terminal with color"""
    flag = True

    @staticmethod
    def error(msg):
        if Logging.flag:
            print "".join([colored("ERROR", "red"), ": ", colored(msg, "white")])

    @staticmethod
    def warn(msg):
        if Logging.flag:
            print "".join([colored("WARN", "yellow"), ": ", colored(msg, "white")])

    @staticmethod
    def info(msg):
        if Logging.flag:
            print "".join([colored("INFO", "magenta"), ": ", colored(msg, "white")])

    @staticmethod
    def debug(msg):
        if Logging.flag:
            print "".join([colored("DEBUG", "magenta"), ": ", colored(msg, "white")])

    @staticmethod
    def success(msg):
        if Logging.flag:
            print "".join([colored("SUCCESS", "green"), ": ", colored(msg, "white")])


Logging.flag = True
url = 'https://www.goodreads.com/user/sign_in'


def is_login():
    url = 'https://www.goodreads.com/user/sign_in'
    r = requests.get(url, allow_redirects=True, verify=False)
    status_code = int(r.status_code)
    if status_code == 200 and r.history:
        return True
    else:
        return False


def get_extra_form_data():
    """Get built-in field value in form"""
    r = requests.get(url, allow_redirects=False, verify=False)
    soup = BeautifulSoup(r.content)
    csrf_token = soup.find('input', {'name': 'authenticity_token'})['value']
    unkonw_n = soup.find('input', {'name': 'n'})['value']
    return csrf_token, unkonw_n


def get_account_from_config(config_file='config.ini'):
    cf = ConfigParser()
    if os.path.exists(config_file) and os.path.isfile(config_file):
        Logging.info(u'正在加载配置文件')
        cf.read(config_file)

        email = cf.get('info', 'email')
        password = cf.get('info', 'password')
        if email == '' or password == '':
            Logging.error(u'未填写配置文件')
            return None, None
        else:
            return email, password
    else:
        Logging.error(u'配置文件加载失败')
     

def post_form(email, password):
    csrf_token, unkonw_n = get_extra_form_data()

    form = {
        'utf8': '&#x2713',
        'authenticity_token': csrf_token,
        'user[email]': email,
        'user[password]': password,
        'remember_me': 'on',
        'next': 'Sign in',
        'n': unkonw_n
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
        'Host': "www.goodreads.com",
        'Origin': "https://www.goodreads.com",
        'Referer': "https://www.goodreads.com"
    }

    r = requests.post(url, data=form, headers=headers, verify=False)
    
    if not r.history:
        raise Exception('log in failed')


def login(email=None, password=None):
    if is_login():
        Logging.success(u'你已经登陆过')
        return True

    # in case the expired cookies
    try:
        requests.cookies.revert()
    except IOError:
        pass
    
    if not email:
        email, password = get_account_from_config()
    if not email:
        sys.stdout.write('Please enter your email: ')
        email = raw_input()
        password = getpass('Please enter your password：')

    post_form(email, password)
    requests.cookies.save()
    

if __name__ == '__main__':
    login()
    raw_input('Press Enter key to exit')