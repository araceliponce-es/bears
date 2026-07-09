from pathlib import Path
import os
import sys

from helpers import load_yaml, merge


def main():
    config_file = "bears.yml"

    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    action_path = Path(os.getenv("GITHUB_ACTION_PATH", Path(__file__).parent))

    default_config = load_yaml(action_path / "default_config.yml")

    user_config = load_yaml(Path(config_file))

    config = merge(default_config, user_config)

    tailwind = config.get("tailwind", {})

    source = tailwind.get("source", "input.css")

    output = tailwind.get("output", "main.css")

    minify = str(tailwind.get("minify", True)).lower()

    # GitHub Actions communication
    github_env = os.getenv("GITHUB_ENV")

    if github_env:
        with open(github_env, "a", encoding="utf-8") as f:
            f.write(f"TAILWIND_SOURCE={source}\n")
            f.write(f"TAILWIND_OUTPUT={output}\n")
            f.write(f"TAILWIND_MINIFY={minify}\n")

    else:
        # local debugging
        print("TAILWIND_SOURCE=", source)
        print("TAILWIND_OUTPUT=", output)
        print("TAILWIND_MINIFY=", minify)


if __name__ == "__main__":
    main()
