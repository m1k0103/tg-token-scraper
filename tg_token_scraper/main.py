import requests
from bs4 import BeautifulSoup
import re

# API limit: 
#  - UNAUTHENTICATED = 60 per hour per IP addr
#  - AUTHENTICATED = 1500 per hour

def get_recently_updated(query):
    tg_tokens = []

    r = requests.get(f"https://github.com/search?q={query}&type=repositories&s=updated&o=desc")
    soup = BeautifulSoup(r.content, "html.parser")

    # extracts the repo owners and names from the html content
    repo_name_regex = re.compile(".*search-match.*")
    repo_elements = soup.find_all("span", {"class":repo_name_regex})
    repo_names = []
    # only if / is in the repo name as sometimes finds descriptions too
    for el in repo_elements:
        if "/" in el.text:
            repo_names.append(el.text)
    
    repo_links = []
    for i in repo_names:
        owner,repo = i.split("/")
        json = requests.get(f"https://api.github.com/repos/{owner}/{repo}").json()
        # get first 3 and last 3 commits
        commits_url = json["commits_url"]

        all_commits = requests.get(commits_url.replace("{/sha}", "")).json()
        #if all_commits["mesasge"] == "Git Repository is empty.":
        #    print("repo empty")
        
        # first 3, last 3
        commits_to_search = all_commits[:3] + all_commits[len(all_commits)-3:]

        # gets each commit, gets the html_url, then searches the html contents for 
        # telegram bot tokens

        for commit in commits_to_search:
            html_url = commit["html_url"]
            commit_content = requests.get(html_url).text
            tg_tokens.append(re.findall(r"\d{9}:[a-zA-Z0-9_-]{35}", commit_content))
            


    print(tg_tokens)


get_recently_updated("bot")