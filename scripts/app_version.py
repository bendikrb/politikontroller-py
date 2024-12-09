from google_play_scraper import app

result = app(
    "com.politikontroller.Politikontroller",
    lang="nb",
    country="no",
)

print(result["version"])  # noqa: T201
ls
