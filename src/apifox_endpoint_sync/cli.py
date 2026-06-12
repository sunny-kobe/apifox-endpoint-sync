from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PUBLIC_PARAMETER_NAMES = {
    "authorization",
    "uid",
    "did",
    "lang",
    "ctry",
    "app",
    "vsn",
    "ch",
    "pf",
    "br",
    "os",
    "mod",
    "us",
    "seq",
    "adid",
    "gaid",
    "idfa",
    "nw",
    "ts",
}

FORBIDDEN_ENDPOINT_KEYS = {
    "commonParameters",
    "auth",
    "security",
    "preProcessors",
    "postProcessors",
    "commonResponseStatus",
}

METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


class SyncError(Exception):
    """Expected CLI error with a user-facing message."""


@dataclass(frozen=True)
class Settings:
    token: str | None
    project_id: str | None
    project_name: str | None
    branch: str | None


@dataclass(frozen=True)
class UpdatePlan:
    endpoint_id: str
    update_file: Path
    method: str
    path: str
    project_id: str | None
    project_name: str | None
    branch: str | None
    dry_run: bool
    validate_schema: bool
    fetch_current: bool
    login: bool
    check_project: bool


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        dotenv = load_dotenv(args.env_file)
        settings = Settings(
            token=args.token or dotenv.get("APIFOX_TOKEN") or os.environ.get("APIFOX_TOKEN"),
            project_id=args.project_id
            or dotenv.get("APIFOX_PROJECT_ID")
            or os.environ.get("APIFOX_PROJECT_ID"),
            project_name=args.project_name
            or dotenv.get("APIFOX_PROJECT_NAME")
            or os.environ.get("APIFOX_PROJECT_NAME"),
            branch=args.branch or dotenv.get("APIFOX_BRANCH") or os.environ.get("APIFOX_BRANCH"),
        )

        update_file = args.update_file.resolve()
        payload = load_json(update_file)
        method, path = validate_endpoint_update(
            payload,
            expected_method=args.expected_method,
            expected_path=args.expected_path,
        )
        plan = UpdatePlan(
            endpoint_id=args.endpoint_id,
            update_file=update_file,
            method=method,
            path=path,
            project_id=settings.project_id,
            project_name=settings.project_name,
            branch=settings.branch,
            dry_run=args.dry_run,
            validate_schema=not args.skip_schema_validate,
            fetch_current=not args.skip_fetch_current,
            login=not args.skip_login,
            check_project=not args.skip_project_list,
        )

        runner = CommandRunner(dry_run=args.dry_run, verbose=args.verbose)
        print_plan(plan)
        if args.dry_run:
            print_dry_run_commands(plan)
            return 0

        if plan.login:
            if not settings.token:
                raise SyncError("APIFOX_TOKEN is required unless --skip-login is used.")
            runner.run(["apifox", "login", "--with-token"], input_text=settings.token + "\n")

        if plan.check_project:
            runner.run(build_project_list_command(settings))

        if plan.fetch_current:
            runner.run(build_endpoint_get_command(args.endpoint_id, settings))

        if plan.validate_schema:
            runner.run(
                ["apifox", "cli-schema", "validate", "endpoint-update"],
                input_text=json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            )

        runner.run(
            build_endpoint_update_command(args.endpoint_id, settings),
            input_text=json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        )
        print("Update completed.")
        return 0
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="apifox-endpoint-sync",
        description="Safely update one Apifox endpoint document from endpoint-update JSON.",
    )
    parser.add_argument("--endpoint-id", required=True, help="Target Apifox endpoint ID.")
    parser.add_argument(
        "--update-file",
        required=True,
        type=Path,
        help="Path to an endpoint-update JSON file.",
    )
    parser.add_argument("--expected-method", help="Optional method guard, for example GET.")
    parser.add_argument("--expected-path", help="Optional path guard, for example /api/admin/users.")
    parser.add_argument("--env-file", type=Path, default=Path(".env"), help="Path to .env file.")
    parser.add_argument("--token", help="Apifox token. Prefer APIFOX_TOKEN or .env for local use.")
    parser.add_argument("--project-id", help="Apifox project ID. Overrides APIFOX_PROJECT_ID.")
    parser.add_argument("--project-name", help="Expected project name. Overrides APIFOX_PROJECT_NAME.")
    parser.add_argument("--branch", help="Apifox branch name. Overrides APIFOX_BRANCH.")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without writing.")
    parser.add_argument("--skip-login", action="store_true", help="Do not run apifox login.")
    parser.add_argument(
        "--skip-project-list",
        action="store_true",
        help="Do not run apifox project list before update.",
    )
    parser.add_argument(
        "--skip-fetch-current",
        action="store_true",
        help="Do not run apifox endpoint get before update.",
    )
    parser.add_argument(
        "--skip-schema-validate",
        action="store_true",
        help="Do not run apifox cli-schema validate endpoint-update.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print command execution details.")
    return parser.parse_args(argv)


def load_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            raise SyncError(f"Invalid .env line {line_number}: expected KEY=value.")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            values[key] = value
    return values


def load_json(path: Path) -> Any:
    if not path.exists():
        raise SyncError(f"Update file does not exist: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise SyncError(f"Invalid JSON in {path}: {exc}") from exc


def validate_endpoint_update(
    payload: Any,
    *,
    expected_method: str | None = None,
    expected_path: str | None = None,
) -> tuple[str, str]:
    if not isinstance(payload, Mapping):
        raise SyncError("endpoint-update JSON must be an object.")

    method_value = payload.get("method")
    path_value = payload.get("path")
    if not isinstance(method_value, str) or not method_value.strip():
        raise SyncError("endpoint-update JSON must include a non-empty method.")
    if not isinstance(path_value, str) or not path_value.strip():
        raise SyncError("endpoint-update JSON must include a non-empty path.")

    method = method_value.strip().upper()
    path = path_value.strip()
    if method not in METHODS:
        raise SyncError(f"Unsupported HTTP method: {method_value}")
    if not path.startswith("/"):
        raise SyncError("path must start with '/'.")

    if expected_method and method != expected_method.strip().upper():
        raise SyncError(f"method mismatch: expected {expected_method.strip().upper()}, got {method}.")
    if expected_path and path != expected_path.strip():
        raise SyncError(f"path mismatch: expected {expected_path.strip()}, got {path}.")

    for forbidden_key in FORBIDDEN_ENDPOINT_KEYS:
        if contains_key(payload, forbidden_key):
            raise SyncError(f"Forbidden endpoint field found: {forbidden_key}")

    public_parameters = sorted(find_public_parameters(payload))
    if public_parameters:
        joined = ", ".join(public_parameters)
        raise SyncError(f"Public parameters must not be written into a single endpoint: {joined}")

    return method, path


def contains_key(value: Any, key: str) -> bool:
    if isinstance(value, Mapping):
        if key in value:
            return True
        return any(contains_key(child, key) for child in value.values())
    if isinstance(value, list):
        return any(contains_key(child, key) for child in value)
    return False


def find_public_parameters(value: Any, *, parameter_context: bool = False) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        maybe_name = value.get("name")
        if isinstance(maybe_name, str) and maybe_name.strip().lower() in PUBLIC_PARAMETER_NAMES:
            found.add(maybe_name.strip())
        for key, child in value.items():
            key_text = key.strip() if isinstance(key, str) else ""
            child_is_parameter_context = parameter_context or key_text.lower() in {
                "parameters",
                "headers",
                "query",
                "queries",
                "cookies",
                "pathparameters",
                "queryparameters",
                "headerparameters",
            }
            if child_is_parameter_context and key_text.lower() in PUBLIC_PARAMETER_NAMES:
                found.add(key.strip())
            found.update(find_public_parameters(child, parameter_context=child_is_parameter_context))
    elif isinstance(value, list):
        for child in value:
            found.update(find_public_parameters(child, parameter_context=parameter_context))
    return found


def build_project_list_command(settings: Settings) -> list[str]:
    command = ["apifox", "project", "list"]
    if settings.project_id:
        command.extend(["--project-id", settings.project_id])
    if settings.project_name:
        command.extend(["--project-name", settings.project_name])
    return command


def build_endpoint_get_command(endpoint_id: str, settings: Settings) -> list[str]:
    command = ["apifox", "endpoint", "get", endpoint_id]
    add_project_and_branch(command, settings)
    return command


def build_endpoint_update_command(endpoint_id: str, settings: Settings) -> list[str]:
    command = ["apifox", "endpoint", "update", endpoint_id]
    add_project_and_branch(command, settings)
    return command


def add_project_and_branch(command: list[str], settings: Settings) -> None:
    if settings.project_id:
        command.extend(["--project-id", settings.project_id])
    if settings.branch:
        command.extend(["--branch", settings.branch])


class CommandRunner:
    def __init__(self, *, dry_run: bool, verbose: bool) -> None:
        self.dry_run = dry_run
        self.verbose = verbose

    def run(self, command: Sequence[str], *, input_text: str | None = None) -> None:
        validate_allowed_command(command)
        if self.dry_run:
            print(shell_join(command))
            return
        if self.verbose:
            suffix = " <stdin>" if input_text is not None else ""
            print(f"+ {shell_join(command)}{suffix}")
        try:
            completed = subprocess.run(
                list(command),
                input=input_text,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise SyncError("apifox CLI was not found in PATH.") from exc
        if completed.returncode != 0:
            raise SyncError(f"Command failed with exit code {completed.returncode}: {shell_join(command)}")


def validate_allowed_command(command: Sequence[str]) -> None:
    if len(command) < 2 or command[0] != "apifox":
        raise SyncError(f"Refusing non-Apifox command: {shell_join(command)}")

    parts = list(command)
    allowed = False
    if parts[:3] == ["apifox", "login", "--with-token"] and len(parts) == 3:
        allowed = True
    elif parts[:3] == ["apifox", "project", "list"]:
        allowed = True
    elif parts[:3] == ["apifox", "endpoint", "get"] and len(parts) >= 4:
        allowed = True
    elif parts[:4] == ["apifox", "cli-schema", "validate", "endpoint-update"]:
        allowed = True
    elif parts[:3] == ["apifox", "endpoint", "update"] and len(parts) >= 4:
        allowed = True

    if not allowed:
        raise SyncError(f"Refusing command outside the Apifox allowlist: {shell_join(command)}")

    joined = " ".join(parts).lower()
    forbidden_fragments = (
        " import",
        "common-parameter",
        "environment update",
        "variable update",
        "project setting update",
        "security",
        "auth scheme",
        "pre-processor",
        "post-processor",
        "processor update",
    )
    for fragment in forbidden_fragments:
        if fragment in joined:
            raise SyncError(f"Refusing forbidden Apifox operation: {shell_join(command)}")


def print_plan(plan: UpdatePlan) -> None:
    print("Apifox endpoint update plan")
    print(f"- endpointId: {plan.endpoint_id}")
    print(f"- method/path: {plan.method} {plan.path}")
    print(f"- update file: {plan.update_file}")
    print(f"- project id: {plan.project_id or '(not set)'}")
    print(f"- project name: {plan.project_name or '(not set)'}")
    print(f"- branch: {plan.branch or '(default)'}")
    print(f"- dry run: {'yes' if plan.dry_run else 'no'}")


def print_dry_run_commands(plan: UpdatePlan) -> None:
    settings = Settings(
        token=None,
        project_id=plan.project_id,
        project_name=plan.project_name,
        branch=plan.branch,
    )
    print("Commands that would run")
    commands: list[list[str]] = []
    if plan.login:
        commands.append(["apifox", "login", "--with-token"])
    if plan.check_project:
        commands.append(build_project_list_command(settings))
    if plan.fetch_current:
        commands.append(build_endpoint_get_command(plan.endpoint_id, settings))
    if plan.validate_schema:
        commands.append(["apifox", "cli-schema", "validate", "endpoint-update"])
    commands.append(build_endpoint_update_command(plan.endpoint_id, settings))
    for command in commands:
        validate_allowed_command(command)
        stdin_note = " <stdin>" if command[:3] in (["apifox", "login", "--with-token"], ["apifox", "endpoint", "update"]) or command[:4] == ["apifox", "cli-schema", "validate", "endpoint-update"] else ""
        print(f"- {shell_join(command)}{stdin_note}")


def shell_join(parts: Iterable[str]) -> str:
    quoted: list[str] = []
    for part in parts:
        if part.replace("-", "").replace("_", "").replace("/", "").replace(".", "").isalnum():
            quoted.append(part)
        else:
            quoted.append("'" + part.replace("'", "'\"'\"'") + "'")
    return " ".join(quoted)


if __name__ == "__main__":
    raise SystemExit(main())
