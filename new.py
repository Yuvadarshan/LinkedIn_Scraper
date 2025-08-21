import os, random, sys, time
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By  
import re

options = Options()
options.add_argument("--start-maximized")

service = Service(r"C:\Windows\System32\chromedriver-win32\chromedriver.exe")  # Windows path to chromedriver
browser = webdriver.Chrome(service=service, options=options)

# LinkedIn login page
browser.get("https://www.linkedin.com/login/")

"""Create a txt file and sign in to your account (better if it's a premium account)"""

with open(r"C:\Users\Sylesh Pavendan\OneDrive\Desktop\LI\config.txt") as file:
    line = file.readlines()
    username = line[0].strip()
    password = line[1].strip()

# ✅ Updated to Selenium 4 style
elementID = browser.find_element(By.ID, 'username')
elementID.send_keys(username)
time.sleep(10)
elementID = browser.find_element(By.ID, 'password')
elementID.send_keys(password)
elementID.submit()
time.sleep(20)

"""Go to your school page, alumni section"""
browser.get('https://www.linkedin.com/search/results/people/?heroEntityKey=urn%3Ali%3Aorganization%3A15103020&keywords=chennai%20institute%20of%20technology&origin=CLUSTER_EXPANSION&position=2&searchId=47649dc7-d26e-4570-a9c6-681a428032c7&sid=y4q')

profilesID = []
profilesID=["https://www.linkedin.com/in/sk-naveen/","https://www.linkedin.com/in/saravanan18302/","https://www.linkedin.com/in/sachithra-nesamani-77a35a1ba/","https://www.linkedin.com/in/rio-m-6665672b6/","https://www.linkedin.com/in/arsmavethk-m-072876256/","https://www.linkedin.com/in/dileepanraje7b4c99/","https://www.linkedin.com/in/madhushree-t-211389200/","https://www.linkedin.com/in/dheeksha-gopika/","https://www.linkedin.com/in/yamini-anbu-158562199/","https://www.linkedin.com/in/madhusudhanan-m-06a7201b9/","https://www.linkedin.com/in/lakshmipooja-e-3055141bb/","https://www.linkedin.com/in/subash-chandra-bose-vengatesan-b45b42150/","https://www.linkedin.com/in/arjun-s-s-189840279/","https://www.linkedin.com/in/vishnu-ram-m-23395218b/",""]

import re

results = []

for profile_url in profilesID:
    browser.get(profile_url)
    time.sleep(6)  # Give more time for dynamic content to load
    name = "N/A"
    grad_year = None
    experiences = []
    eligible = False

    # Extract name using Selenium
    try:
        name_elem = browser.find_element(By.TAG_NAME, 'h1')
        name = name_elem.text.strip()
    except Exception:
        pass

    # Extract education using Selenium
    try:
        edu_elements = browser.find_elements(By.XPATH, "//li[contains(., 'Chennai Institute of Technology')]")
        for edu in edu_elements:
            text = edu.text
            years = re.findall(r'\d{4}', text)
            if years:
                grad_year = int(years[-1])
                if grad_year < 2025:
                    eligible = True
                    break
    except Exception:
        pass
    if not eligible:
        continue

    # Extract experience using BeautifulSoup with broader search
    soup = BeautifulSoup(browser.page_source, "lxml")
    try:
        exp_sections = soup.find_all('section', class_='artdeco-card pv-profile-card break-words mt2')
        for exp_section in exp_sections:
            if exp_section.find('div', id='experience'):
                all_text = exp_section.get_text(separator='\n', strip=True)
                lines = [line for line in all_text.split('\n') if line.strip()]
                if lines and 'Experience' in lines[0]:
                    lines = lines[1:]
                experiences = lines
    except Exception as e:
        print("Experience extraction error:", e)

    print(f"Name: {name}\nGrad Year: {grad_year}\nExperiences: {experiences}\n")
    results.append({'name': name, 'grad_year': grad_year, 'experiences': "; ".join(experiences)})

print(results)

df = pd.DataFrame(results)
df.to_csv('boisexperience.csv', index=False)