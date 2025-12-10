from __future__ import annotations

from pathlib import Path


class Settings:
    """
    Глобальные настройки проекта, в первую очередь пути к данным.
    Можно потом добавить чтение из env, конфиг-файла и т.д.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        if project_root is None:
            # Предполагаем, что этот файл лежит в src/bugsy_multi_agent/config
            # и корень проекта на три уровня выше.
            self.project_root = Path(__file__).resolve().parents[3]
        else:
            self.project_root = project_root

        self.data_dir = self.project_root / "data"
        self.contexts_dir = self.data_dir / "contexts"
        self.outputs_dir = self.data_dir / "outputs"

        self.ontology_retriever_dir = self.outputs_dir / "ontologyRAG_retriever"
        self.attribute_generator_dir = self.outputs_dir / "attribute_generator"
        self.attribute_validator_dir = self.outputs_dir / "attribute_validator"
        self.attribute_coverage_checker_dir = (
            self.outputs_dir / "attribute_coverage_checker"
        )
        self.scenario_generator_dir = self.outputs_dir / "scenario_generator"
        self.scenario_validator_dir = self.outputs_dir / "scenario_validator"
        self.scenario_coverage_checker_dir = (
            self.outputs_dir / "scenario_coverage_checker"
        )

    def ensure_dirs(self) -> None:
        """
        Создает все необходимые директории, если их нет.
        """
        self.contexts_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.ontology_retriever_dir.mkdir(parents=True, exist_ok=True)
        self.attribute_generator_dir.mkdir(parents=True, exist_ok=True)
        self.attribute_validator_dir.mkdir(parents=True, exist_ok=True)
        self.attribute_coverage_checker_dir.mkdir(parents=True, exist_ok=True)
        self.scenario_generator_dir.mkdir(parents=True, exist_ok=True)
        self.scenario_validator_dir.mkdir(parents=True, exist_ok=True)
        self.scenario_coverage_checker_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
