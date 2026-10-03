import json
import subprocess
import sys
from pathlib import Path

from assertpy import assert_that


def run_worker(mode: str, database: Path, output: Path) -> dict:
    root = Path(__file__).resolve().parents[1]
    worker = "import runpy; runpy.run_path('tests/helpers/restart_worker.py', run_name='__main__')"
    subprocess.run(
        [sys.executable, "-c", worker, mode, str(database), str(output)],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return json.loads(output.read_text())


class TestRestart:
    def test_board_survives_process_exit_and_fresh_process(
        self, tmp_path: Path
    ) -> None:
        database = tmp_path / "jobs.sqlite3"
        expected = run_worker("write", database, tmp_path / "before.json")

        actual = run_worker("read", database, tmp_path / "after.json")

        assert_that(
            (actual, len(actual["jobs"]), actual["errors"], actual["counts"])
        ).is_equal_to(
            (expected, 3, [], [":yellow-badge[1]", ":blue-badge[1]", ":red-badge[1]"])
        )

    def test_edit_survives_process_exit_and_fresh_process(self, tmp_path: Path) -> None:
        database = tmp_path / "jobs.sqlite3"
        created = run_worker("write", database, tmp_path / "created.json")
        edited = run_worker("edit", database, tmp_path / "edited.json")

        actual = run_worker("read", database, tmp_path / "after.json")

        assert_that(
            (
                actual["jobs"],
                [job["id"] for job in actual["jobs"]],
                actual["jobs"][0],
                actual["counts"],
                edited["errors"],
            )
        ).is_equal_to(
            (
                edited["jobs"],
                [job["id"] for job in created["jobs"]],
                {
                    **created["jobs"][0],
                    "company": "Fictional renamed",
                    "status": "Active",
                    "applied_on": "2026-09-20",
                    "stage": "Final interview",
                    "notes": "Edited notes\nSecond line",
                },
                [":yellow-badge[0]", ":blue-badge[2]", ":red-badge[1]"],
                [],
            )
        )
