"""Run a small end-to-end check through the real MCP client and server."""

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLIENT = PROJECT_ROOT / "src" / "mcp_client.py"


def run_case(name: str, arguments: list[str], expected_text: str) -> None:
    result = subprocess.run(
        [sys.executable, str(CLIENT), *arguments],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=150,
        check=False,
    )
    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0 or expected_text not in output:
        raise RuntimeError(
            f"{name} failed (exit {result.returncode}).\n{output.strip()}"
        )
    print(f"PASS: {name}")


def main() -> int:
    try:
        run_case("MCP connection", ["--health"], "MCP connection OK")
        run_case("local documents", ["--knowledge-status"], "Loaded 5 documents")
        retrieval_cases = [
            (
                "graduation credits retrieval",
                "資訊工程學系畢業需要多少學分？",
                "元智大學資訊工程學系必修科目表.txt",
            ),
            (
                "elective courses retrieval",
                "哪些選修課程可能不會正常開課？",
                "元智大學資訊工程學系選修科目表.txt",
            ),
            (
                "internship rules retrieval",
                "申請專業實習需要符合哪些條件？",
                "元智大學資訊工程學系專業實習實施辦法.txt",
            ),
            (
                "project rules retrieval",
                "專題製作期間要完成哪些活動？",
                "元智大學資訊工程學系專題製作實施要點.txt",
            ),
            (
                "overseas study retrieval",
                "海外研習中斷後還能累計嗎？",
                "元智大學資訊工程學系海外研習實施要點.txt",
            ),
        ]
        for name, question, expected_source in retrieval_cases:
            run_case(name, ["--search", question], expected_source)
        answer_expectation = (
            "LLM (ollama /"
            if "localhost:11434" in os.environ.get("OPENAI_BASE_URL", "")
            else "--- SOURCES"
        )
        run_case(
            "end-to-end answer",
            ["資訊工程學系畢業需要多少學分？"],
            answer_expectation,
        )
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"SMOKE TEST FAILED: {error}", file=sys.stderr)
        return 1

    print("SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
