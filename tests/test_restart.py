import json
import subprocess
import sys
from pathlib import Path

from assertpy import assert_that


class TestRestart:
    def test_board_survives_process_exit_and_fresh_process(
        self, tmp_path: Path
    ) -> None:
        root = Path(__file__).resolve().parents[1]
        worker = "import runpy; runpy.run_path('tests/helpers/restart_worker.py', run_name='__main__')"
        database = tmp_path / "jobs.sqlite3"
        before = tmp_path / "before.json"
        after = tmp_path / "after.json"
        subprocess.run(
            [sys.executable, "-c", worker, "write", str(database), str(before)],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        expected = json.loads(before.read_text())

        subprocess.run(
            [sys.executable, "-c", worker, "read", str(database), str(after)],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        actual = json.loads(after.read_text())

        assert_that(
            (actual, len(actual["jobs"]), actual["errors"], actual["counts"])
        ).is_equal_to(
            (expected, 3, [], [":yellow-badge[1]", ":blue-badge[1]", ":red-badge[1]"])
        )
