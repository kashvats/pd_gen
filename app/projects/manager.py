"""Manages project persistence, directory structures, auto-save, and loading."""

import json
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from app.config.settings import PROJECTS_DIR
from app.config.characters import CharacterDefaults
from app.models.project import Project, SpeakerProfile
from app.parser.markdown_parser import MarkdownScriptParser
from app.parser.speaker_detector import detect_speakers
from app.voices.library import VoiceLibrary


class ProjectManager:
    """Handles saving, loading, creating, and listing local projects."""

    def __init__(self, root_dir: Path = PROJECTS_DIR, voice_library: Optional[VoiceLibrary] = None):
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.voice_library = voice_library or VoiceLibrary()

    def get_project_dir(self, project_id: str) -> Path:
        p_dir = self.root_dir / project_id
        p_dir.mkdir(parents=True, exist_ok=True)
        (p_dir / "audio" / "segments").mkdir(parents=True, exist_ok=True)
        (p_dir / "audio" / "takes").mkdir(parents=True, exist_ok=True)
        return p_dir

    def create_project(self, name: str = "New Podcast Episode", initial_markdown: str = "") -> Project:
        """Creates and initializes a new project."""
        project = Project(name=name, markdown=initial_markdown)
        if initial_markdown:
            self.sync_markdown_to_project(project, initial_markdown)
        self.save_project(project)
        return project

    def sync_markdown_to_project(self, project: Project, markdown_text: str) -> None:
        """Parses markdown, detects new characters, and assigns global or library voice defaults."""
        project.markdown = markdown_text
        nodes = MarkdownScriptParser.parse(markdown_text)
        # Preserve IDs for unchanged turns, including duplicate occurrences, across edits.
        from collections import defaultdict, deque
        matches = defaultdict(deque)
        for old in project.script_nodes:
            key = (old.get("type"), old.get("speaker"), old.get("text"),
                   json.dumps(old.get("directives", {}), sort_keys=True))
            matches[key].append(old["id"])
        for node in nodes:
            raw = node.to_dict()
            key = (raw.get("type"), raw.get("speaker"), raw.get("text"),
                   json.dumps(raw.get("directives", {}), sort_keys=True))
            if matches[key]:
                node.id = matches[key].popleft()
        project.script_nodes = [n.to_dict() for n in nodes]

        detected = detect_speakers(nodes)
        saved_voices = self.voice_library.list_voices()

        for speaker in detected:
            if speaker not in project.speakers:
                # 1. Check global character defaults
                default_info = CharacterDefaults.get_for_speaker(speaker)
                if default_info:
                    sp = SpeakerProfile(
                        name=speaker,
                        voice_name=default_info.get("voice_name", "Studio Voice"),
                        provider=default_info.get("provider", "kokoro"),
                        voice_id=default_info.get("voice_id", "af_heart"),
                        preset=default_info.get("preset", "Natural Conversation"),
                        direction_prompt=default_info.get("direction", ""),
                    )
                    if "delivery" in default_info:
                        from app.models.voice import VoiceDelivery
                        sp.delivery = VoiceDelivery.from_dict(default_info["delivery"])
                    project.speakers[speaker] = sp
                else:
                    # 2. Assign from dynamic diverse voice palette
                    from app.tts.kokoro_provider import VOICES
                    dynamic_palette = [(name, "kokoro", vid, "Natural Conversation")
                                       for vid, name in VOICES.items()]
                    used = {(profile.provider, profile.voice_id) for profile in project.speakers.values()}
                    remaining = [voice for voice in dynamic_palette if (voice[1], voice[2]) not in used]
                    idx = len(project.speakers) % len(dynamic_palette)
                    v_name, prov, v_id, prst = remaining[0] if remaining else dynamic_palette[idx]
                    project.speakers[speaker] = SpeakerProfile(
                        name=speaker,
                        voice_name=v_name,
                        provider=prov,
                        voice_id=v_id,
                        preset=prst,
                        direction_prompt=f"Authentic, natural conversational {speaker}.",
                    )



    def save_project(self, project: Project) -> Path:
        """Persists project and writes script.md."""
        p_dir = self.get_project_dir(project.id)
        proj_file = p_dir / "project.json"
        script_file = p_dir / "script.md"

        import datetime
        project.updated_at = datetime.datetime.now().isoformat()

        with open(proj_file, "w", encoding="utf-8") as f:
            json.dump(project.to_dict(), f, indent=2)

        if project.markdown:
            script_file.write_text(project.markdown, encoding="utf-8")

        return p_dir

    def load_project(self, project_id: str) -> Optional[Project]:
        """Loads a project from disk."""
        p_dir = self.root_dir / project_id
        proj_file = p_dir / "project.json"
        if not proj_file.exists():
            return None

        try:
            with open(proj_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Project.from_dict(data)
        except Exception:
            return None

    def list_projects(self) -> List[Tuple[str, str, str]]:
        """Returns list of (id, name, updated_at)."""
        projects = []
        for folder in self.root_dir.iterdir():
            if folder.is_dir():
                proj_file = folder / "project.json"
                if proj_file.exists():
                    try:
                        with open(proj_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            projects.append((
                                data.get("id", folder.name),
                                data.get("name", "Untitled Episode"),
                                data.get("updated_at", ""),
                            ))
                    except Exception:
                        pass
        return sorted(projects, key=lambda x: x[2], reverse=True)

    def delete_project(self, project_id: str) -> bool:
        """Deletes project directory from local storage."""
        p_dir = self.root_dir / project_id
        if p_dir.exists():
            shutil.rmtree(p_dir, ignore_errors=True)
            return True
        return False
