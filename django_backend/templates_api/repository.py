"""Read locked templates and field definitions from email_templates/."""

import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

from django.conf import settings


class TemplateRepositoryError(RuntimeError):
    pass


class TemplateRepository:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or settings.EMAIL_TEMPLATE_ROOT).resolve()

    def _read_json(self, path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TemplateRepositoryError(f"Unable to read template data: {path.name}") from exc

    def _write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            temporary_path.replace(path)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise TemplateRepositoryError(
                f"Unable to save template data: {path.name}"
            ) from exc

    def _template_directory(self, directory: str) -> Path:
        path = (self.root / directory).resolve()
        if self.root not in path.parents:
            raise TemplateRepositoryError("Invalid template directory.")
        return path

    def list_templates(self, include_inactive: bool = False) -> list[dict]:
        registry = self._read_json(self.root / "templates.json")
        if not isinstance(registry, list):
            raise TemplateRepositoryError("Template registry must contain a list.")

        templates = []
        for item in registry:
            if not include_inactive and not item.get("active", False):
                continue

            directory = self._template_directory(item["directory"])
            html_path = directory / "template.html"
            fields_path = directory / "fields.json"
            if not html_path.is_file() or not fields_path.is_file():
                continue

            field_definition = self._read_json(fields_path)
            template = dict(item)
            template["field_count"] = len(field_definition.get("fields", []))
            templates.append(template)

        return templates

    def get_template(self, template_id: str, include_inactive: bool = False) -> dict:
        template = next(
            (
                item
                for item in self.list_templates(include_inactive=include_inactive)
                if item.get("id") == template_id
            ),
            None,
        )
        if template is None:
            raise TemplateRepositoryError("Template not found.")

        directory = self._template_directory(template["directory"])
        field_definition = self._read_json(directory / "fields.json")
        result = dict(template)
        result["fields"] = field_definition.get("fields", [])
        try:
            result["html"] = (directory / "template.html").read_text(encoding="utf-8")
        except OSError as exc:
            raise TemplateRepositoryError("Unable to read template HTML.") from exc
        return result

    def create_template(self, data: dict) -> dict:
        registry = self._read_json(self.root / "templates.json")
        if any(item.get("id") == data["id"] for item in registry):
            raise TemplateRepositoryError("A template with this ID already exists.")
        return self._save_template(registry, data)

    def update_template(self, template_id: str, data: dict) -> dict:
        registry = self._read_json(self.root / "templates.json")
        if not any(item.get("id") == template_id for item in registry):
            raise TemplateRepositoryError("Template not found.")
        if data["id"] != template_id:
            raise TemplateRepositoryError("A template ID cannot be changed.")
        return self._save_template(registry, data)

    def delete_template(self, template_id: str) -> Path:
        registry = self._read_json(self.root / "templates.json")
        template = next(
            (item for item in registry if item.get("id") == template_id),
            None,
        )
        if template is None:
            raise TemplateRepositoryError("Template not found.")

        directory = self._template_directory(template["directory"])
        if not directory.is_dir():
            raise TemplateRepositoryError("Template files were not found.")

        archive_root = (self.root / ".trash").resolve()
        if self.root not in archive_root.parents:
            raise TemplateRepositoryError("Invalid template archive directory.")
        archive_root.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive_path = archive_root / f"{template_id}-{timestamp}-{uuid4().hex[:8]}"
        updated_registry = [
            item for item in registry if item.get("id") != template_id
        ]

        try:
            directory.replace(archive_path)
            self._write_text(
                self.root / "templates.json",
                json.dumps(updated_registry, indent=2, ensure_ascii=False) + "\n",
            )
        except (OSError, TemplateRepositoryError) as exc:
            if archive_path.exists() and not directory.exists():
                archive_path.replace(directory)
            if isinstance(exc, TemplateRepositoryError):
                raise
            raise TemplateRepositoryError("Unable to delete template.") from exc

        return archive_path

    def _save_template(self, registry: list[dict], data: dict) -> dict:
        template_id = data["id"]
        registry_item = {
            "id": template_id,
            "name": data["name"],
            "description": data.get("description", ""),
            "directory": template_id,
            "allowed_groups": data.get("allowed_groups", []),
            "active": data.get("active", True),
        }
        updated_registry = [
            registry_item if item.get("id") == template_id else item
            for item in registry
        ]
        if not any(item.get("id") == template_id for item in registry):
            updated_registry.append(registry_item)

        field_definition = {
            "id": template_id,
            "name": data["name"],
            "allowed_groups": data.get("allowed_groups", []),
            "fields": data["fields"],
        }
        directory = self._template_directory(template_id)
        self._write_text(directory / "template.html", data["html"])
        self._write_text(
            directory / "fields.json",
            json.dumps(field_definition, indent=2, ensure_ascii=False) + "\n",
        )
        self._write_text(
            self.root / "templates.json",
            json.dumps(updated_registry, indent=2, ensure_ascii=False) + "\n",
        )
        return self.get_template(template_id, include_inactive=True)

