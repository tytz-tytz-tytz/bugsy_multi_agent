from __future__ import annotations

import argparse

from bugsy_multi_agent.config.settings import settings
from bugsy_multi_agent.data_access.json_io import read_json
from bugsy_multi_agent.llm.prompts_ontology import build_ontology_retriever_prompt
from bugsy_multi_agent.llm.prompts_attributes import build_attribute_generator_prompt
from bugsy_multi_agent.models.testing_context import TestingContext


def print_ontology_prompt(query_id: str) -> None:
    """
    Печатает промпт для OntologyRAGRetrieverAgent для указанного query_id.
    Берёт сырой контекст из data/contexts/{query_id}.json.
    """
    settings.ensure_dirs()
    path = settings.contexts_dir / f"{query_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Raw context file not found: {path}")

    raw = read_json(path)

    # Тут мы не вытаскиваем display_query вручную, потому что
    # ontology_retriever_agent сам его берёт из queries.json.
    # Для чистоты проверки промпт-билдеру можно передать то, что использует агент.
    # Но раз у нас есть queries.json, проще буквально повторить логику.
    from bugsy_multi_agent.data_access.query_mapping import get_query_text

    display_query = get_query_text(settings, query_id, fallback=raw.get("query", ""))

    prompt = build_ontology_retriever_prompt(raw, query_override=display_query)
    print(prompt)


def print_attribute_prompt(query_id: str) -> None:
    """
    Печатает промпт для AttributeGeneratorAgent для указанного query_id.
    Берёт TestingContext из data/outputs/ontologyRAG_retriever/{query_id}.json.
    """
    settings.ensure_dirs()
    path = settings.ontology_retriever_dir / f"{query_id}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"TestingContext file not found: {path}. "
            f"Сначала запусти ontology retriever для этого query_id."
        )

    raw = read_json(path)
    ctx = TestingContext.from_dict(raw)

    from bugsy_multi_agent.data_access.query_mapping import get_query_text

    display_query = get_query_text(settings, query_id, fallback=ctx.query)

    prompt = build_attribute_generator_prompt(ctx, query_override=display_query)
    print(prompt)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Debug utility: print LLM prompts for agents."
    )

    parser.add_argument(
        "agent",
        choices=["ontology", "attributes"],
        help="Для какого агента печатать промпт.",
    )
    parser.add_argument(
        "query_id",
        help="Идентификатор запроса (имя файла без .json в data/contexts/).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.agent == "ontology":
        print_ontology_prompt(args.query_id)
    elif args.agent == "attributes":
        print_attribute_prompt(args.query_id)
    else:
        parser.error(f"Unknown agent: {args.agent}")


if __name__ == "__main__":
    main()
