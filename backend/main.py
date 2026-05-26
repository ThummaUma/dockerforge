import os
import subprocess
import shutil
import stat
import time
import git
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import generate_dockerfile, fix_dockerfile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RepoRequest(BaseModel):
    github_url: str


def force_delete(path):
    def handle_error(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    if os.path.exists(path):
        shutil.rmtree(path, onerror=handle_error)
        time.sleep(2)


def clone_repo(github_url):
    clone_path = "C:/Users/thumm/cloned_repo"
    force_delete(clone_path)
    git.Repo.clone_from(github_url, clone_path)
    return clone_path


def scan_repo(repo_path):
    important_files = [
        "package.json", "requirements.txt", "pom.xml",
        "build.gradle", "go.mod", "Gemfile", "composer.json",
        "index.js", "app.py", "main.py", "server.js"
    ]
    summary = "Files found in repo:\n"
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            filepath = os.path.join(root, file)
            relative = filepath.replace(repo_path, "")
            summary += f"\n{relative}"
    summary += "\n\n--- File Contents ---\n"
    for filename in important_files:
        filepath = os.path.join(repo_path, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                summary += f"\n\n{filename}:\n{content}"
            except:
                pass
    return summary


def run_docker_build(repo_path, dockerfile_content):
    try:
        if not dockerfile_content or not isinstance(dockerfile_content, str):
            dockerfile_content = "FROM python:3.9-slim\nWORKDIR /app\nCOPY . .\nCMD [\"python\", \"app.py\"]"

        dockerfile_path = os.path.join(repo_path, "Dockerfile")
        with open(dockerfile_path, "w", encoding="utf-8") as f:
            f.write(dockerfile_content)

        cmd = f'docker build -t dockerforge-test "{repo_path}"'
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            shell=True,
            encoding="utf-8",
            errors="ignore"
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""
        return result.returncode, stdout, stderr

    except subprocess.TimeoutExpired:
        return 1, "", "Build timed out"
    except Exception as e:
        return 1, "", str(e)


def run_docker_container():
    try:
        result = subprocess.run(
            'docker run --rm -d --name dockerforge_test dockerforge-test',
            capture_output=True,
            text=True,
            timeout=30,
            shell=True,
            encoding="utf-8",
            errors="ignore"
        )

        if result.returncode == 0:
            container_id = result.stdout.strip()
            time.sleep(3)

            check = subprocess.run(
                f'docker ps --filter id={container_id} --format "{{{{.ID}}}}"',
                capture_output=True,
                text=True,
                shell=True,
                encoding="utf-8",
                errors="ignore"
            )

            subprocess.run(
                'docker stop dockerforge_test',
                capture_output=True,
                shell=True
            )

            if check.stdout.strip():
                return True, "Container started and ran successfully! ✅"
            else:
                return False, "Container started but stopped immediately"
        else:
            return False, f"Container failed to start: {result.stderr[:200]}"

    except subprocess.TimeoutExpired:
        subprocess.run('docker stop dockerforge_test', shell=True)
        return False, "Container timed out - may need environment variables"
    except Exception as e:
        return False, f"Container run error: {str(e)}"


@app.post("/generate")
async def generate(request: RepoRequest):
    logs = []
    try:
        logs.append("Cloning repository...")
        repo_path = clone_repo(request.github_url)
        logs.append("Repository cloned successfully!")

        logs.append("Scanning repository files...")
        file_summary = scan_repo(repo_path)
        logs.append("Scan complete!")

        logs.append("Asking AI to generate Dockerfile...")
        dockerfile = generate_dockerfile(file_summary)
        if not dockerfile:
            dockerfile = "FROM python:3.9-slim\nRUN apt-get update && apt-get install -y libpq-dev gcc\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD [\"python\", \"app.py\"]"
        logs.append("Dockerfile generated!")

        final_dockerfile = dockerfile
        build_success = False

        for attempt in range(1, 4):
            logs.append(f"Build attempt {attempt}/3...")
            returncode, stdout, stderr = run_docker_build(repo_path, final_dockerfile)

            if returncode == 0:
                logs.append("Build successful!")
                build_success = True
                break
            else:
                error_msg = stderr if stderr else stdout if stdout else "Unknown error"
                logs.append(f"Build failed. Error: {error_msg[:500]}")
                if attempt < 3:
                    logs.append("Asking AI to fix the error...")
                    fixed = fix_dockerfile(final_dockerfile, error_msg)
                    if fixed:
                        final_dockerfile = fixed
                    logs.append("AI provided a fix, retrying...")

        if build_success:
            logs.append("Running container to verify it starts...")
            run_success, run_log = run_docker_container()
            logs.append(run_log)

        return {
            "success": build_success,
            "dockerfile": final_dockerfile,
            "logs": logs
        }

    except Exception as e:
        return {
            "success": False,
            "dockerfile": "",
            "logs": logs + [f"Error: {str(e)}"]
        }