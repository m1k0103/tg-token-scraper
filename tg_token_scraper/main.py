import requests
from bs4 import BeautifulSoup
import re

# API limit: 
#  - UNAUTHENTICATED = 60 per hour per IP addr
#  - AUTHENTICATED = 1500 per hour

def main(query):
    tg_tokens = {}

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
    print(f"Found {len(repo_names)} repos.")
    
    repo_links = []
    for i in repo_names:
        owner,repo = i.split("/")
        json = requests.get(f"https://api.github.com/repos/{owner}/{repo}").json()
        
        try:
            if "API rate limit" in json["message"]:
                print("Rate limit reached. Exiting...")
                quit()
        except KeyError:
            pass

        # get first 3 and last 3 commits
        commits_url = json["commits_url"]
        all_commits = requests.get(commits_url.replace("{/sha}", "")).json()
        print(f"Retrieved all commits for {owner}/{repo}")

        # if github repo is empty
        try:
            if "Git Repository is empty." in all_commits["message"]:
                print(f"{owner}/{repo} is empty. Skipping..")
                continue
        except TypeError:
            pass


        # if api rate limit exceeded
        try:
            if "API rate limit exceeded for" in all_commits["message"]:
                pass
        except KeyError and TypeError:
            print("Api limit reached. Please change IP.")
            break


        # first 3, last 3
        commits_to_search = all_commits[:3] + all_commits[len(all_commits)-3:]

        # gets each commit, gets the html_url, then searches the html contents for 
        # telegram bot tokens

        for commit in commits_to_search:
            html_url = commit["html_url"]
            commit_content = requests.get(html_url).text
            tokens = re.findall(r"\d{10}:[A-Za-z0-9_-]{35,}", commit_content)
            print(tokens)
            if tokens:
                tg_tokens.update(tokens)
                print(f"Found {len(tokens)} in ")
            else:
                print(f"No tokens found in {owner}/{repo}")


    return tg_tokens


main("bot")