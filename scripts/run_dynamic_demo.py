from contradiction_lab.cli import UNCERTAINTY_QUERY
from contradiction_lab.graph import ResearchEngine
from contradiction_lab.reporting import markdown_report
from contradiction_lab.schemas import ComparisonReport, ResearchRequest


if __name__ == "__main__":
    result = ResearchEngine().run(ResearchRequest(query=UNCERTAINTY_QUERY, workflow="dynamic"))
    print(markdown_report(ComparisonReport.model_validate(result["report"])))
    print(" → ".join(event["node"] + (f" [{event['route']}]" if event["route"] else "") for event in result["trace"]))
