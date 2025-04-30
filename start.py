from tg_token_scraper.main import main, save_tokens_to_file

if __name__ == "__main__":
    tokens = main("bot")
    save_tokens_to_file(tokens, "output.txt")