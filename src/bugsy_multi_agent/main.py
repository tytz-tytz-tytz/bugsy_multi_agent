from __future__ import annotations

import argparse

from bugsy_multi_agent.config.settings import settings
from bugsy_multi_agent.data_access.json_io import list_json_files
from bugsy_multi_agent.orchestration.pipeline import Pipeline


def cmd_list_queries() -> None:
    """
    Показывает, какие query-файлы есть в data/contexts/.
    """
    settings.ensure_dirs()
    files = list_json_files(settings.contexts_dir)
    if not files:
        print("No query JSON files found in data/contexts/")
        return

    print("Available queries:")
    for path in files:
        print(" -", path.stem)


def cmd_run(query_id: str, full: bool) -> None:
    """
    Запускает пайплайн для указанного query_id.
    """
    pipeline = Pipeline(settings=settings)

    if full:
        pipeline.run_full_pipeline(query_id)
    else:
        ctx = pipeline.run_ontology_retriever(query_id)
        print(f"OntologyRAG Retriever Agent finished for query_id={query_id}")
        print(f"Core passages: {len(ctx.core_passages)}")
        print(f"Supporting passages: {len(ctx.supporting_passages)}")
        print(
            f"Output written to: "
            f"{settings.ontology_retriever_dir / (query_id + '.json')}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="bugsy_multi_agent CLI"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "list-queries",
        help="List available query JSON files in data/contexts/",
    )

    sp_run = subparsers.add_parser(
        "run",
        help="Run pipeline for given query id",
    )
    sp_run.add_argument(
        "query_id",
        type=str,
        help="Query id (file name without .json in data/contexts/)",
    )
    sp_run.add_argument(
        "--full",
        action="store_true",
        help="Run full pipeline (currently only ontology retriever step)",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list-queries":
        cmd_list_queries()
    elif args.command == "run":
        cmd_run(args.query_id, args.full)
    else:
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
