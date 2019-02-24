from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
import string
import random
import os
import sys
import time;

def generate_random_string(length=8):
    '''Generate a random string N characters in length'''

    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def generate_random_number(start, end):
    '''Generate a random between the start and the end params'''
    
    return random.randint(start, end)

def fill_out_bracket():
    '''Fill out a bracket and submit it'''
    
    # open browser and navigate to site
    opts = Options()
    opts.set_headless()
    assert opts.headless  # Operating in headless mode
    browser = Firefox(options=opts)
    
    # submit used defined brackets per child process
    number_of_brackets = sys.argv[3]

    for i in range(number_of_brackets):      
        # get random stuff
        random.seed()
        random_string = generate_random_string()
        random_number_picks = generate_random_number(0, 2)
        random_number_score = generate_random_number(135,180)
        
        print(f"random_string is {random_string} : random picks is {random_number_picks} : random_number_score is {random_number_score}")
    
        pool_name = sys.argv[1]
        browser.get(f"http://www.itsawesomebaby.com/pool/{pool_name}")
        
        # make random picks
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
    
def spawn_children():
    '''Create forked processes and submit brackets'''

    forks = 1
    if len(sys.argv) == 3:
        forks = int(sys.argv[2])
 
    for i in range(forks):
        try:
            pid = os.fork()
        except OSError:
            sys.stderr.write("Could not create a child process\n")
            continue
 
        if pid == 0:
            print("In the child process {} that has the PID {}".format(i+1, os.getpid()))
            fill_out_bracket()
            exit()

    # wait for the children to finish
    for i in range(forks):
        finished = os.waitpid(0, 0)
        print(f"finished {finished}")


if __name__ == '__main__':
    
    # create a whole bunch of children and try to overwhelm the server
    spawn_children()