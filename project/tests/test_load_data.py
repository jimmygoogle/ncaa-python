from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
import string
import random
import os
import sys
import time
import argparse

def generate_random_string(length=8):
    '''Generate a random string N characters in length'''

    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def generate_random_number(start, end):
    '''Generate a random between the start and the end params'''
    
    return random.randint(start, end)

def fill_out_bracket(args):
    '''Fill out a bracket and submit it'''
    
    # open browser and navigate to site
    opts = Options()
    opts.set_headless()
    assert opts.headless  # Operating in headless mode
    browser = Firefox(options=opts)
    
    # submit used defined brackets per child process
    number_of_brackets = int(args.number_of_brackets)

    # use random words for the username and emails
    word_file = "/usr/share/dict/words"
    words = open(word_file).read().splitlines()
    words_length = (len(words)) - 1

    for i in range(number_of_brackets):      
        # get random stuff
        random.seed()
        random_string = words[generate_random_number(0, words_length)].lower()
        random_number_picks = generate_random_number(0, 2)
        random_number_score = generate_random_number(135,180)
        
        print(f"random_string is {random_string} : random picks is {random_number_picks} : random_number_score is {random_number_score}")
    
        pool_name = args.pool_name
        url = args.url
        browser.get(f"{url}/pool/{pool_name}")

        # use the 'make picks' feature to fill out picks
        browser.find_element_by_id('picks-header').click()
        picks = ['chalk', 'mix', 'random']
        element = picks[random_number_picks]
        browser.find_element_by_id(element).click()
        
        # fill out user form and submit
        browser.find_element_by_id('email').send_keys(f"{random_string}@mailinator.com")
        browser.find_element_by_id('username').send_keys(random_string)
        browser.find_element_by_id('tieBreaker').send_keys(random_number_score)
        browser.find_element_by_id('submit_user_bracket').click()
    
    # close the browser
    browser.close()
    
def spawn_children(args):
    '''Create forked processes and submit brackets'''

    children = int(args.children)
    for i in range(children):
        try:
            pid = os.fork()
        except OSError:
            print("Could not create a child process")
            continue
 
        if pid == 0:
            print(f"In the child process {i+1} that has the PID {os.getpid()}")
            fill_out_bracket(args)
            exit()

    # wait for the children to finish
    for i in range(children):
        finished = os.waitpid(0, 0)
        print(f"finished {finished}")


if __name__ == '__main__':
    parser=argparse.ArgumentParser()

    parser.add_argument('--children', help='Number of children to create')
    parser.add_argument('--url', help='URL of the site to test')
    parser.add_argument('--pool_name', help='Pool name')
    parser.add_argument('--number_of_brackets', help='Number of brackets to create')

    args = parser.parse_args()
    
    # create a whole bunch of children and load data
    spawn_children(args)
