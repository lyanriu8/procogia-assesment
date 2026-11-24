import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from .config import Settings
from .graph import ResearchEngine
from .reporting import markdown_report
from .schemas import ComparisonReport, ResearchRequest


from .domain import load_domain

DEMO_QUERY = load_domain()["demo_query"]
UNCERTAINTY_QUERY = load_domain()["uncertainty_query"]
SYNONYM_QUERY = load_domain()["synonym_query"]


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Contradiction Lab: scientific evidence comparison")
    subcommands = parser.add_subparsers(dest="command", required=True)
    research = subcommands.add_parser("research")
    research.add_argument("query", nargs="?", default=DEMO_QUERY)
    research.add_argument("--workflow", choices=["static", "dynamic"], default="dynamic")
    research.add_argument("--config")
    research.add_argument("--source", choices=["corpus", "live"])
    research.add_argument("--model-backend", choices=["ollama"])
    research.add_argument("--runtime", choices=["langgraph"])
    research.add_argument("--vector-backend", choices=["chroma"])
    research.add_argument("--embedding-backend", choices=["ollama"])
    research.add_argument("--top-k", type=int)
    research.add_argument("--max-iterations", type=int)
    research.add_argument("--min-comparable-pairs", type=int)
    research.add_argument("--context", choices=["compact", "evidence-rich"])
    research.add_argument("--output", type=Path)
    research.add_argument("--json", action="store_true")
    serve = subcommands.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    evaluate = subcommands.add_parser("evaluate")
    evaluate.add_argument("--config")
    evaluate.add_argument("--quick", action="store_true")
    evaluate.add_argument("--workflow", choices=["static", "dynamic", "both"], default="both")
    evaluate.add_argument("--output-dir", type=Path, default=Path("artifacts/evaluation"))
    args = parser.parse_args()
    if args.command == "serve":
        import uvicorn

        uvicorn.run("contradiction_lab.api:app", host=args.host, port=args.port)
    elif args.command == "evaluate":
        from .evaluation.runner import evaluate

        result = evaluate(workflow=args.workflow, output_dir=args.output_dir, settings=Settings.load(args.config), compare_context_configs=not args.quick)
        print(json.dumps(result["summary"], indent=2))
    else:
        settings = Settings.load(args.config, **{name: getattr(args, name) for name in
                                 ("source", "model_backend", "runtime", "vector_backend", "embedding_backend", "min_comparable_pairs")})
        request = ResearchRequest(query=args.query, workflow=args.workflow, top_k=args.top_k,
                                  max_iterations=args.max_iterations, context_config=args.context)
        result = ResearchEngine(settings).run(request)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n")
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(markdown_report(ComparisonReport.model_validate(result["report"])))
            print("Trace: " + " → ".join(event["node"] + (f" [{event['route']}]" if event["route"] else "") for event in result["trace"]))


if __name__ == "__main__":
    main()
