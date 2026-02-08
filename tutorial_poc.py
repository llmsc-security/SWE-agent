#!/usr/bin/env python3
"""
Tutorial POC: HTTP API Test Client for SWE-agent Flask Endpoints

This script demonstrates how to interact with the SWE-agent API server.
It provides test cases for the Flask endpoints including:
- Health check
- Run agent on a problem statement
- Get trajectory status
- List trajectories

Usage:
    python tutorial_poc.py --host localhost --port 11400
"""

import argparse
import json
import sys
import time
from typing import Any, Optional

import requests


class SWEAgentAPIClient:
    """Client for interacting with SWE-agent API server."""

    def __init__(self, host: str = "localhost", port: int = 11400):
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()

    def health_check(self) -> dict[str, Any]:
        """Check if the API server is running."""
        response = self.session.get(f"{self.base_url}/health")
        return self._handle_response(response, "Health check failed")

    def run_agent(
        self,
        repo: str,
        issue: str,
        model_name: str = "gpt-4o",
        config_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """Start the agent to work on a problem statement.

        Args:
            repo: Repository URL or identifier (e.g., "https://github.com/owner/repo")
            issue: The issue/problem description
            model_name: Model to use (e.g., "gpt-4o", "claude-3-5-sonnet")
            config_path: Optional path to configuration file

        Returns:
            Operation result with run_id
        """
        payload = {
            "repo": repo,
            "issue": issue,
            "model_name": model_name,
        }
        if config_path:
            payload["config_path"] = config_path

        response = self.session.post(
            f"{self.base_url}/run",
            json=payload,
            timeout=30,
        )
        return self._handle_response(response, "Failed to start agent run")

    def get_trajectory(self, run_id: str) -> dict[str, Any]:
        """Get trajectory information for a specific run."""
        response = self.session.get(
            f"{self.base_url}/trajectory/{run_id}",
            timeout=30,
        )
        return self._handle_response(response, f"Failed to get trajectory: {run_id}")

    def list_trajectories(self) -> list[dict[str, Any]]:
        """List all available trajectories."""
        response = self.session.get(f"{self.base_url}/trajectories", timeout=30)
        return self._handle_response(response, "Failed to list trajectories")

    def get_trajectory_file(self, run_id: str) -> dict[str, Any]:
        """Get the full trajectory file content."""
        response = self.session.get(
            f"{self.base_url}/trajectory/{run_id}/file",
            timeout=30,
        )
        return self._handle_response(response, f"Failed to get trajectory file: {run_id}")

    def stop_run(self, run_id: str) -> dict[str, Any]:
        """Stop an ongoing agent run."""
        response = self.session.post(
            f"{self.base_url}/run/{run_id}/stop",
            timeout=30,
        )
        return self._handle_response(response, f"Failed to stop run: {run_id}")

    def _handle_response(self, response: requests.Response, error_msg: str) -> Any:
        """Handle API response and raise appropriate exceptions."""
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            error_detail = ""
            try:
                error_detail = f" - {response.json()}"
            except json.JSONDecodeError:
                error_detail = f" - {response.text}"
            raise Exception(f"{error_msg}{error_detail}") from e

        if response.status_code == 204:  # No content
            return None
        return response.json()


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def test_health_check(client: SWEAgentAPIClient) -> bool:
    """Test the health check endpoint."""
    print_section("Test 1: Health Check")
    try:
        result = client.health_check()
        print(f"API Status: {result.get('status', 'unknown')}")
        print(f"Version: {result.get('version', 'unknown')}")
        print("Health check: PASSED")
        return True
    except Exception as e:
        print(f"Health check: FAILED - {e}")
        return False


def test_run_agent(client: SWEAgentAPIClient, test_issue: str) -> Optional[str]:
    """Test starting an agent run."""
    print_section("Test 2: Run Agent")
    repo = "https://github.com/owner/test-repo"

    try:
        print(f"Starting agent on repo: {repo}")
        print(f"Issue: {test_issue[:100]}...")

        result = client.run_agent(
            repo=repo,
            issue=test_issue,
            model_name="gpt-4o",
        )

        run_id = result.get("run_id")
        if run_id:
            print(f"Run started with ID: {run_id}")
            print(f"Status: {result.get('status', 'unknown')}")
            return run_id
        else:
            print(f"Run response: {result}")
            return None
    except Exception as e:
        print(f"Failed to start run: {e}")
        return None


def test_list_trajectories(client: SWEAgentAPIClient) -> bool:
    """Test listing trajectories."""
    print_section("Test 3: List Trajectories")
    try:
        trajectories = client.list_trajectories()
        print(f"Found {len(trajectories)} trajectory(s)")
        for traj in trajectories:
            print(f"  - {traj.get('id', 'unknown')}: {traj.get('status', 'unknown')}")
        print("List trajectories: PASSED")
        return True
    except Exception as e:
        print(f"List trajectories: FAILED - {e}")
        return False


def wait_for_completion(client: SWEAgentAPIClient, run_id: str, timeout: int = 300) -> bool:
    """Wait for an agent run to complete."""
    print(f"Waiting for run {run_id} to complete (timeout: {timeout}s)...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            result = client.get_trajectory(run_id)
            status = result.get("status", "unknown")
            print(f"  Status: {status}")

            if status in ["completed", "success"]:
                print("Run completed successfully!")
                return True
            elif status in ["failed", "error"]:
                print(f"Run failed with status: {status}")
                return False

            time.sleep(5)
        except Exception as e:
            print(f"  Error checking status: {e}")
            time.sleep(5)

    print("Timeout waiting for run completion")
    return False


def run_full_demo(client: SWEAgentAPIClient) -> None:
    """Run a complete demo sequence."""
    print_section("Full Demo Sequence")

    # Sample issue for testing
    test_issue = """Fix the bug in the main function where the variable is not initialized.

The issue is in line 42 of main.py where 'result' is used without being initialized first."""

    # Step 1: Start agent run
    run_id = test_run_agent(client, test_issue)
    if not run_id:
        print("Demo aborted: Could not start run")
        return

    # Step 2: Wait for completion
    success = wait_for_completion(client, run_id, timeout=120)

    # Step 3: Get trajectory
    if success:
        print_section("Step 3: Get Trajectory")
        try:
            traj = client.get_trajectory(run_id)
            print(f"Trajectory status: {traj.get('status')}")
            print(f"Steps completed: {traj.get('steps', 'N/A')}")
        except Exception as e:
            print(f"Failed to get trajectory: {e}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SWE-agent API Test Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --host localhost --port 11400 --test
  %(prog)s --host localhost --port 11400 --demo
  %(prog)s --help
""",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="API server host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=11400,
        help="API server port (default: 11400)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run basic health check test",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run full demo sequence",
    )
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=300,
        help="Timeout in seconds for waiting for runs (default: 300)",
    )

    args = parser.parse_args()

    # Create client
    client = SWEAgentAPIClient(host=args.host, port=args.port)

    print_section("SWE-agent API Client")
    print(f"Base URL: {client.base_url}")

    # Run selected test
    if args.test:
        success = test_health_check(client)
        return 0 if success else 1

    if args.demo:
        run_full_demo(client)
        return 0

    # Default: show help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
