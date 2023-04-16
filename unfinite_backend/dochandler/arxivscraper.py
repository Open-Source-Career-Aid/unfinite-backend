import requests
import pandas as pd
from bs4 import BeautifulSoup
from requests import HTTPError
from selenium import webdriver
import csv
import arxivscraper as ax
import courlan as cl
import time
import re
from fake_useragent import UserAgent
from datetime import datetime
# cs_subtopics = "cs.AI",
# scraper = arxivscraper.Scraper(category='physics:cond-mat', date_from='2017-05-27',date_until='2017-06-07')


def arxiv_scrape(category, subtopics):
    try:
        for t in subtopics:
            scraper = ax.Scraper(category=category,date_from='2020-01-01',date_until=datetime.now().strftime("%Y-%m-%d"), t=10, filters={'categories':[t],'abstract':['learning']})
            output = scraper.scrape()
            cols = ('id', 'title', 'categories', 'abstract', 'doi', 'created', 'updated', 'authors', 'affiliation')
            try:
                df = pd.DataFrame(output,columns=cols)
                # create url column
                df["pdf_url"] = df["id"].apply(lambda x: "https://arxiv.org/pdf/" + x + ".pdf")
                # saves the data to a csv file, but ideally we save it to a database
                df.to_csv(f'{t}.csv', index=True, header=True)
                print(df.head())
            except ValueError as e:
                print("Error: ", e)
                continue
    except HTTPError as e:
        print("Error: ", e)
        return


def new_research_submissions():
    # Get the topic from the user
    """ This is a niave approach to the problem.
    I will be using the brute force to scrape the arxiv website.
    In future, I will be using the arxvi API to get the data.
    """
    try:
        root_url = "https://arxiv.org/"
        cs_topic = ["https://arxiv.org/list/cs.AI/recent", "https://arxiv.org/list/cmp-lg/recent", "https://arxiv.org/list/stat.ML/recent"]
        # topics = ["cs.AI", "cmp-lg", "stat.ML"]
        for i in range(len(cs_topic)):
            headers = {
                "User-Agent":  str(UserAgent().random),
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.google.com/",
                "Connection": "keep-alive"
            }
            r = requests.get(cs_topic[i], headers=headers)
            if r.status_code == 200:
                print("Success")
                soup = BeautifulSoup(r.content, 'html.parser')
                # print(soup.prettify())
                # all entries per page
                all_entries = soup.find("a", string="all")
                if all_entries is not None:
                    all_entries = root_url + all_entries.get("href")
                    all_resp = requests.get(all_entries, headers=headers)
                    try:
                        if all_resp.status_code == 200:
                            # doing things with all recent entries for past week
                            print("Success for all entries")
                            def add_root_url(url):
                                if url.startswith("http"):
                                    return url
                                return root_url + url
                            all_soup = BeautifulSoup(all_resp.content, 'html.parser')
                            all_titles = all_soup.find_all("div", class_="list-title mathjax")
                            all_authors = all_soup.find_all("div", class_="list-authors")
                            all_subjects = all_soup.find_all("span", class_="primary-subject")
                            all_entries_pdf = all_soup.find_all("a", title="Abstract")
                            all_entries_reference = all_soup.find_all("a", title="Download PDF")
                            # save the all entries pdf to a csv file
                            all_entries_pdf = list(map(add_root_url, all_entries_pdf))
                            all_entries_reference = list(map(add_root_url, all_entries_reference))
                            print(len(all_entries_pdf))
                            print(all_entries)
                    except HTTPError as e:
                        if e.code == 503:
                            print("Got 503. Retrying after {0:d} seconds.".format(30))
                            time(30)
                            continue

                        else:
                            print("Connection Terminated as a result of error " % e)

                    print(all_entries)
                print()
                exit(1)
    except HTTPError as e:

        print("Connection Terminated as a result of error " % e)
    return


if __name__ == "__main__":
    # run the scraper on python 3.9 or below
    scrape_category = "cs"
    stopics = ["cs.AI", "cmp-lg", "stat.ml"]
    arxiv_scrape(scrape_category, stopics)