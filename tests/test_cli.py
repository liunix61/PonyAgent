"""Tests for CLI."""

import pytest


class TestCLI:
    def test_help(self) -> None:
        from ponyagent.cli.app import main

        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0

    def test_version(self) -> None:
        from ponyagent.cli.app import main

        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0

    def test_no_goal_shows_help(self) -> None:
        from ponyagent.cli.app import main

        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code == 0

    def test_with_goal_uses_stub(self) -> None:
        from ponyagent.cli.app import main

        # With StubLLM, should complete without API key
        main(["say hello"])

    def test_build_parser(self) -> None:
        from ponyagent.cli.app import build_parser

        parser = build_parser()
        args = parser.parse_args(["goal", "--orchestrator", "crew", "--max-steps", "5"])
        assert args.goal == "goal"
        assert args.orchestrator == "crew"
        assert args.max_steps == 5
