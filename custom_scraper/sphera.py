import os
import time

import pyautogui

from temp.sphera import initialize_chrome_driver
from utils.config import BASE_DIR

if __name__ == '__main__':
    item_url = 'https://sphera.com/2022/xml-data/processes/80a4496a-1089-4811-91e6-8de53ae1a0de.xml'
    save_dir = os.path.join(BASE_DIR, 'temp')
    driver = initialize_chrome_driver(printable=True, save_dir=save_dir)
    driver.get(item_url)
    time.sleep(2)

    driver.execute_script('window.print();')

    time.sleep(1)

    pyautogui.hotkey('ctrl', 's')
    time.sleep(1)
    pyautogui.press('enter')

    time.sleep(1)

    driver.close()

    print("Finished")
