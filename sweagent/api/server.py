"""Flask API server for SWE-agent.

This module provides a Flask-based API server that allows the SWE-agent
to be used as a backend for a GUI interface.

Default port: 8000
"""

from __future__ import annotations

import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Flask, jsonify, request

# Add the parent directory to the path so we can import sweagent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import required modules
from sweagent import PACKAGE_DIR
from sweagent.run.run_single import RunSingle, RunSingleConfig
from sweagent.agent.agents import AgentConfig, get_agent_from_config
from sweagent.environment.swe_env import EnvironmentConfig, SWEEnv
from sweagent.agent.problem_statement import (
    EmptyProblemStatement,
    ProblemStatement,
    ProblemStatementConfig,
)
from sweagent.run.hooks.apply_patch import SaveApplyPatchHook

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "swe-agent-api"})


@app.route("/version", methods=["GET"])
def get_version():
    """Get the SWE-agent version."""
    from sweagent import __version__

    return jsonify({"version": __version__})


def run_swe_agent(problem_statement: str, instance_id: str, config_path: str | None = None) -> str:
    """Run the SWE-agent on a problem statement.

    Args:
        problem_statement: The issue description
        instance_id: Unique identifier for this run
        config_path: Optional path to config file

    Returns:
        Result string from the agent run
    """
    from sweagent.utils.config import load_environment_variables

    # Create a temporary output directory
    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "trajectories" / "api" / instance_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create problem statement config
        problem_config = EmptyProblemStatement()
        problem_config = ProblemStatement.model_validate(
            {"description": problem_statement, "id": instance_id}
        )

        # Create agent config (default)
        agent_config = AgentConfig()

        # Create environment config (default)
        env_config = EnvironmentConfig()

        # Create run config
        run_config = RunSingleConfig(
            env=env_config,
            agent=agent_config,
            problem_statement=problem_config,
            output_dir=output_dir,
        )

        # Load environment variables if config path provided
        if config_path:
            load_environment_variables(Path(config_path))

        # Create and run the agent
        run_single = RunSingle.from_config(run_config)
        run_single.add_hook(SaveApplyPatchHook(apply_patch_locally=False))
        run_single.run()

        # Return result
        return f"Completed successfully. Output directory: {output_dir}"


@app.route("/run", methods=["POST"])
def run_agent():
    """Run the SWE-agent on a problem statement.

    Expected JSON payload:
    {
        "problem_statement": "The issue description",
        "config": "Optional configuration string",
        "instance_id": "Optional instance identifier"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        problem_statement = data.get("problem_statement")
        if not problem_statement:
            return jsonify({"error": "problem_statement is required"}), 400

        instance_id = data.get("instance_id", "default-instance")
        config_path = data.get("config", None)

        try:
            # Run the agent
            result = run_swe_agent(
                problem_statement=problem_statement,
                instance_id=instance_id,
                config_path=config_path,
            )

            return jsonify({
                "status": "success",
                "instance_id": instance_id,
                "result": result
            })

        except Exception as e:
            return jsonify({
                "status": "error",
                "instance_id": instance_id,
                "error": str(e)
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/batch-run", methods=["POST"])
def run_batch_agent():
    """Run the SWE-agent on multiple problem statements.

    Expected JSON payload:
    {
        "problems": [
            {"problem_statement": "...", "instance_id": "..."},
            ...
        ]
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        problems = data.get("problems", [])

        if not isinstance(problems, list) or len(problems) == 0:
            return jsonify({"error": "problems must be a non-empty list"}), 400

        results = []
        for i, problem in enumerate(problems):
            problem_statement = problem.get("problem_statement")
            instance_id = problem.get("instance_id", f"instance-{i}")

            try:
                result = run_swe_agent(
                    problem_statement=problem_statement,
                    instance_id=instance_id,
                )
                results.append({
                    "instance_id": instance_id,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                results.append({
                    "instance_id": instance_id,
                    "status": "error",
                    "error": str(e)
                })

        return jsonify({
            "status": "batch-complete",
            "total": len(results),
            "results": results
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/info", methods=["GET"])
def get_info():
    """Get information about the SWE-agent setup."""
    from sweagent import __version__

    return jsonify({
        "service": "swe-agent-api",
        "version": __version__,
        "endpoints": {
            "/health": "GET - Health check",
            "/version": "GET - Get version",
            "/run": "POST - Run agent on problem",
            "/batch-run": "POST - Run agent on multiple problems",
            "/info": "GET - Get this info"
        }
    })


def get_parser():
    """Get the argument parser for the API server."""
    parser = ArgumentParser(description="Run SWE-agent API server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    return parser


def run_from_cli(args: list[str] | None = None):
    """Run the API server from command line arguments."""
    parsed_args = get_parser().parse_args(args)

    app.run(
        host=parsed_args.host,
        port=parsed_args.port,
        debug=parsed_args.debug
    )


if __name__ == "__main__":
    run_from_cli()
