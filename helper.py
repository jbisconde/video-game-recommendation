import time


def load_jquery(driver):
    time.sleep(3)
    jquery = open('jquery-1.11.2.min.js').read()
    driver.execute_script(jquery)


def selector(driver, css_selector, first=True):
    query = '''return($('%s'))''' % css_selector
    item_lst = driver.execute_script(query)
    if first:
        return item_lst[0]
    else:
        return item_lst

def scroll_to_bottom(driver, css_selector):
    prev_length = 0
    cur_length = len(selector(driver, css_selector))

    while prev_length < cur_length:
        prev_length = cur_length
        cur_length = len(selector(driver, css_selector))
        driver.execute_script('window.scrollTo(0, 2500000)')

    return True


def get_outerhtml(driver, css_selector):
    query = \
        '''
        arr = $('%s');
        lst = [];
        for(var i = 0, len = arr.length; i < len; i++) {lst.push(arr[i].outerHTML);}
        return(lst)
        ''' % css_selector

    return driver.execute_script(query)


def alert(driver, msg):
    driver.execute_script('alert("%s");' % msg)