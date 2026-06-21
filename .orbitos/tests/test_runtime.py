import json
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[2]


def run(command, cwd, expect_success=True):
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if expect_success and result.returncode != 0:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    if not expect_success and result.returncode == 0:
        raise AssertionError(f"Command unexpectedly passed: {' '.join(command)}")
    return result


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def copy_product(source, target):
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=source,
        capture_output=True,
        check=True,
    )
    target.mkdir(parents=True, exist_ok=True)
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative_path = Path(raw_path.decode("utf-8"))
        source_path = source / relative_path
        target_path = target / relative_path
        if source_path.is_file():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)


def test_runtime(runtime_root):
    python = sys.executable
    init_script = runtime_root / ".orbitos/scripts/init-runtime.py"
    writer_script = runtime_root / ".orbitos/scripts/write_event.py"
    validation_script = runtime_root / ".orbitos/scripts/run-validation.py"

    require(not (runtime_root / ".orbitos/docs").exists(), "product repo must not ship .orbitos/docs")

    startup_content = (runtime_root / ".orbitos/workflows/startup-sync.md").read_text(encoding="utf-8")
    startup_execution = startup_content.split("## 执行流程", 1)[1].split("## 异常处理", 1)[0]
    for project_input in ("AGENTS.md", "README.md", "STATUS.md"):
        require(project_input not in startup_execution, f"Startup Sync execution reads project input: {project_input}")

    root_agents = (runtime_root / "AGENTS.md").read_text(encoding="utf-8")
    require(root_agents.count("定位目标工作区域") == 1, "root AGENTS.md semantic routing is missing or duplicated")
    require(root_agents.count("不全量扫描") == 1, "root AGENTS.md vault-scan boundary is missing or duplicated")

    run(["git", "init"], runtime_root)
    run([python, str(init_script)], runtime_root)

    required_paths = [
        runtime_root / ".orbitos/agents/registry.yaml",
        runtime_root / "01-收件箱/00-粘贴.md",
        runtime_root / "02-时间线/今日.md",
        runtime_root / "02-时间线/本周.md",
    ]
    for path in required_paths:
        require(path.is_file(), f"init-runtime did not create {path.relative_to(runtime_root)}")

    exclude_path = runtime_root / ".git/info/exclude"
    require(exclude_path.is_file(), "init-runtime did not create .git/info/exclude")
    exclude_content = exclude_path.read_text(encoding="utf-8")
    require(".mimocode/" in exclude_content, "init-runtime did not register .mimocode/ local exclude")
    require(".nova/" in exclude_content, "init-runtime did not register .nova/ local exclude")

    runtime_private_dir = runtime_root / ".mimocode"
    runtime_private_dir.mkdir(parents=True, exist_ok=True)
    runtime_private_file = runtime_private_dir / "session.json"
    runtime_private_file.write_text('{"runtime": true}\n', encoding="utf-8")
    ignored_check = run(["git", "check-ignore", "-v", ".mimocode/session.json"], runtime_root)
    require(".git/info/exclude" in ignored_check.stdout, "runtime private workdir is not ignored by local exclude")

    inbox_sentinel = runtime_root / "01-收件箱/user-sentinel.md"
    timeline_sentinel = runtime_root / "02-时间线/今日.md"
    registry_sentinel = runtime_root / ".orbitos/agents/registry.yaml"
    inbox_sentinel.write_text("user content must survive\n", encoding="utf-8")
    timeline_sentinel.write_text("timeline content must survive\n", encoding="utf-8")
    registry_sentinel.write_text(
        json.dumps({"version": 1, "updated": "2026-06-17", "agents": []}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    run([python, str(init_script)], runtime_root)
    require(inbox_sentinel.read_text(encoding="utf-8") == "user content must survive\n", "init-runtime overwrote user inbox content")
    require(timeline_sentinel.read_text(encoding="utf-8") == "timeline content must survive\n", "init-runtime overwrote timeline content")
    require("2026-06-17" in registry_sentinel.read_text(encoding="utf-8"), "init-runtime overwrote registry content")
    require(exclude_path.read_text(encoding="utf-8") == exclude_content, "init-runtime rewrote local exclude unexpectedly")

    codex_profile = runtime_root / "00-系统/agents/codex.md"
    nova_profile = runtime_root / "00-系统/agents/nova.md"

    def append_marker(path, marker):
        with path.open("a", encoding="utf-8") as handle:
            handle.write(marker)

    codex_marker = "\n- runtime smoke: codex private state append\n"
    nova_marker = "\n- runtime smoke: nova private state append\n"
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(append_marker, codex_profile, codex_marker),
            executor.submit(append_marker, nova_profile, nova_marker),
        ]
        for future in futures:
            future.result()
    require(codex_marker in codex_profile.read_text(encoding="utf-8"), "codex private state write did not persist")
    require(nova_marker in nova_profile.read_text(encoding="utf-8"), "nova private state write did not persist")

    writer_command = [
        python,
        str(writer_script),
        "--agent-id",
        "codex",
        "--slug",
        "runtime_integration_test",
        "--summary",
        "Runtime integration test receipt.",
        "--reason",
        "Verify the OrbitOS completion receipt pipeline.",
        "--file",
        "updated:.orbitos/workflows/progress-sync.md:integration test",
        "--validation",
        "passed",
    ]
    writer_result = run(writer_command, runtime_root)
    event_path = runtime_root / writer_result.stdout.strip()
    require(event_path.is_file(), "write_event did not create an event")
    event = json.loads(event_path.read_text(encoding="utf-8"))
    require(event["actor"]["agent_id"] == "codex", "event actor is incorrect")
    require(event["id"].endswith("_codex_runtime_integration_test"), "event id is incorrect")

    invalid_review = writer_command[:-4] + [
        "--validation",
        "passed",
        "--review-required",
        "--dry-run",
    ]
    run(invalid_review, runtime_root, expect_success=False)

    python_validation = run([python, str(validation_script)], runtime_root)
    require("Validation eval passed" in python_validation.stdout, "Python validation did not report success")

    node = shutil.which("node")
    if node:
        node_validation = run(
            [node, str(runtime_root / ".orbitos/scripts/run-validation.mjs")],
            runtime_root,
        )
        require("Validation eval passed" in node_validation.stdout, "Node validation did not report success")

    event["unexpected_field"] = True
    event_path.write_text(json.dumps(event, indent=2) + "\n", encoding="utf-8")
    failed_validation = run(
        [python, str(validation_script)], runtime_root, expect_success=False
    )
    require("additional property is not allowed" in failed_validation.stdout, "validation did not reject a corrupted event")

    return "Python and Node" if node else "Python (Node unavailable, fallback skipped)"


def main():
    with tempfile.TemporaryDirectory(prefix="orbitos-runtime-test-") as temp_dir:
        runtime_root = Path(temp_dir) / "orbitos"
        copy_product(SOURCE_ROOT, runtime_root)
        validation_modes = test_runtime(runtime_root)
    print(f"Runtime integration test passed: {validation_modes} validation.")


if __name__ == "__main__":
    main()
