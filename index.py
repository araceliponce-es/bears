import re
import json
import time
from github import Github, Auth
from jinja2 import Environment, FileSystemLoader
import os
import random
from dotenv import load_dotenv
import sys  # para usar argumentos... python index2.py --watch


load_dotenv()


def get_env(name, default=None, cast=str):
    value = os.getenv(name, default)
    if value is None:
        return None
    try:
        return cast(value)
    except:
        return default


DEFAULT_TAGS = "project,hackathon"
raw_tags = get_env("TAGS", DEFAULT_TAGS)


CONFIG = {
    "template_name": get_env("TEMPLATE_NAME", "index.html"),
    "template_dir": get_env("TEMPLATE_DIR", "templates"),
    "output_html": get_env("OUTPUT_HTML", "dist/index.html"),
    "assets_folder": get_env("ASSETS_FOLDER", "images"),
    "cache_file": get_env("CACHE_FILE", "data-es.json"),
    "stylesheet": get_env("STYLESHEET", "main.css"),
    "title": get_env("TITLE", ""),
    "tags": set(t.strip().lower() for t in raw_tags.split(",") if t.strip()),
    "recent_commits": get_env("RECENT_COMMITS", "false").lower() == "true",
    "max_commits": get_env("MAX_COMMITS", 6, int),
}


REFRESH = "--watch" in sys.argv


IGNORE_IMAGE_WORDS = [
    "badge",
    "shield",
    "travis",
    "coveralls",
    "img.shields",
]


COLOR_PALETTE = [
    "#FF6B6B",
    "#4ECDC4",
    "#45B7D1",
    "#F7B801",
    "#9B5DE5",
    "#00BBF9",
    "#F15BB5",
    "#00F5D4",
]


def get_recent_commits(user, max_commits):
    events = user.get_events()
    commits = []

    for event in events:
        if event.type == "PushEvent":
            for c in event.payload["commits"]:
                commits.append(
                    {
                        "repo": event.repo.name,
                        "message": c["message"],
                    }
                )
                if len(commits) >= max_commits:
                    return commits
    return commits


####################################


def get_random_color():
    return random.choice(COLOR_PALETTE)


# sera consistente entre builds
def get_repo_color(repo_name):
    index = abs(hash(repo_name)) % len(COLOR_PALETTE)
    return COLOR_PALETTE[index]


####################################


def valid_image(url):
    if not url:
        return False
    return not any(word in url.lower() for word in IGNORE_IMAGE_WORDS)


def convert_relative_to_raw(repo, url):
    if url.startswith("http"):
        return url

    base = f"https://raw.githubusercontent.com/{repo.owner.login}/{repo.name}/{repo.default_branch}/"
    return base + url.lstrip("./")


def extract_readme_image(repo, readme_text):
    matches = re.findall(r"!\[.*?\]\((.*?)\)", readme_text)

    for img in matches:
        img = convert_relative_to_raw(repo, img)

        if valid_image(img):
            return img

    return None


def get_local_image(repo, assets_folder):
    path = f"{assets_folder}/{repo.name}.png"
    if os.path.exists(path):
        return "/" + path
    return None


def get_opengraph_image(repo):
    return f"https://opengraph.githubassets.com/1/{repo.owner.login}/{repo.name}"


# si encuentra imagen en readme, usa esa, si no hay usa local, si no hay, ... ahora usa blank.png
def get_best_image(repo, readme_text):
    readme_image = extract_readme_image(repo, readme_text)

    if readme_image:
        return readme_image

    local = get_local_image(repo, CONFIG["assets_folder"])

    if local:
        return local

    # private repos dont seem to have a opengraph image
    # open_g = get_opengraph_image(repo)
    # if open_g:
    #     return get_opengraph_image(repo)

    return "/images/blank.png"


####################################


def get_readme(repo):
    """obtiene el contenido  del  readme,en caso no haya nadadevuelve string vacio"""
    try:
        repo_content = repo.get_readme()
        readme_text = repo_content.decoded_content.decode("utf-8")
    except Exception:
        readme_text = ""
    return readme_text


def extract_first_blockquote(text):
    match = re.search(r"(?m)^> (.+)", text)
    return match.group(1).strip() if match else None


####################################
def matches_tags(repo_topics, config_tags):
    if not config_tags:
        return False  # True: si no defines tags, muestra todo
    # return bool(config_tags.intersection(repo_topics))
    return any(tag in repo_topics for tag in config_tags)


def get_github_data(token, username):
    auth = Auth.Token(token)
    g = Github(auth=auth, per_page=100)
    user = g.get_user(username)

    # Obtener todos los repos públicos y privados
    # repos = user.get_repos(visibility="all", sort="updated") no
    # repos = user.get_repos(type="owner", sort="updated") no
    # importantisimo usar g.get_user ( no usar user)
    repos = g.get_user().get_repos()
    repos_list = list(repos)
    total_repos = len(repos_list)

    remaining = g.get_rate_limit().resources.core.remaining
    print("queda", remaining)
    if remaining < 50:
        print("queda menos de 50")
        time.sleep(60)

    data = {
        "name": user.name or user.login,
        "bio": user.bio or "",
        "avatar": user.avatar_url,
        "followers": user.followers,
        "following": user.following,
        "repos": [],
    }

    print(f"📦 Total repos encontrados: {total_repos}")
    print("───────────────────────────────────────")

    total_processed = 0
    matched = 0

    # debug
    # for repo in g.get_user().get_repos():
    # print(repo.name, repo.private)

    for index, repo in enumerate(repos_list, start=1):
        total_processed += 1

        # Omitir forks y archivados
        if repo.fork or repo.archived:
            continue

        # Obtener topics puede fallar en actions
        try:
            topics = repo.get_topics()
        except:
            topics = []
        topics = [t.lower() for t in (topics or [])]

        # debug
        print(f"[{index}/{total_repos}] {repo.name} → topics are: {topics}")

        # Determinar si el repo es destacado
        if matches_tags(topics, CONFIG["tags"]):
            matched += 1

            readme_text = get_readme(repo)

            image_url = get_best_image(repo, readme_text)

            # lang_list = list((repo.get_languages() or {}).keys())
            # something inside the dict includes "url" as a key.
            langs_raw = repo.get_languages() or {}
            print(repo.name, "RAW LANGS:", langs_raw)

            lang_list = list(langs_raw.keys())

            # default_image_url = repo.name + ".png"

            data["repos"].append(
                {
                    "name": repo.name,
                    "url": repo.html_url,
                    "description": repo.description or "No description",
                    "stars": repo.stargazers_count,
                    "languages": lang_list,
                    "topics": topics,
                    "updated_at": repo.updated_at.isoformat(),
                    "private": repo.private,
                    "image_url": image_url,
                    "readme": readme_text,
                    "blockquote": extract_first_blockquote(readme_text),
                    "color": get_random_color(),
                }
            )

    # Ordenar por estrellas y fecha
    data["repos"].sort(key=lambda r: (r["stars"], r["updated_at"]), reverse=True)

    if CONFIG["recent_commits"]:
        try:
            data["recent_commits"] = get_recent_commits(user, CONFIG["max_commits"])
        except:
            data["recent_commits"] = []

    print("───────────────────────────────────────")
    print(f"✅ Total procesados: {total_processed}")
    print(f"⭐ Repos destacados encontrados: {matched}")

    return data


def generate_html(data, config):
    # env = Environment(loader=FileSystemLoader("templates"))
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    env = Environment(
        loader=FileSystemLoader(os.path.join(BASE_DIR, CONFIG["template_dir"]))
    )

    template = env.get_template(CONFIG["template_name"])

    html_output = template.render(
        user=data,
        title=CONFIG["title"],
        stylesheet=CONFIG["stylesheet"],
    )

    with open(CONFIG["output_html"], "w", encoding="utf-8") as f:
        f.write(html_output)

    print("HTML done")


def generate_json(data):
    """
    https://www.geeksforgeeks.org/python/create-a-file-if-not-exists-in-python/

    si elarchivo no existe,lo crea
    copia data enelarchivo
        :param data: Description
    """

    with open(CONFIG["cache_file"], "w") as w:
        json.dump(data, w)


if __name__ == "__main__":
    token = os.getenv("GH_TOKEN")
    username = os.getenv("GH_USERNAME")

    # si no coloco --watch y el data.json existe
    if os.path.exists(CONFIG["cache_file"]) and not REFRESH:
        print("usando cache local")
        with open(CONFIG["cache_file"]) as f:
            data = json.load(f)

    # no olvides las variables obligatorias
    elif not token or not username:
        print("Faltan variables GH_TOKEN o GH_USERNAME en .env")
        exit()
    # usa las variables del env
    else:
        print("obteniendo datos de gh")
        data = get_github_data(token, username)
        generate_json(data)

    generate_html(data, CONFIG)
