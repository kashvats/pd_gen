flowchart TD

subgraph group_interface["Desktop Interface"]
  node_app_main["Application Entry<br/>[main.py]"]
  node_main_window["Main Window<br/>[main_window.py]"]
  node_script_editor["Script Editor<br/>[script_editor.py]"]
  node_audio_player["Audio Player<br/>[audio_player.py]"]
end

subgraph group_projects["Projects And Scripts"]
  node_project_manager["Project Manager<br/>[manager.py]"]
  node_markdown_parser["Markdown Parser<br/>[markdown_parser.py]"]
  node_project_store[("Project Files<br/>[manager.py]")]
end

subgraph group_speech["Speech Planning"]
  node_context_builder["Context Builder<br/>[context.py]"]
  node_speech_director["Speech Director<br/>[director.py]"]
  node_pronunciation["Pronunciation Rules<br/>[pronunciation.py]"]
  node_pause_calculator["Pause Calculator<br/>[pauses.py]"]
end

subgraph group_audio["Audio Production"]
  node_audio_generator["Audio Generator<br/>[generator.py]"]
  node_audio_cache[("Audio Cache<br/>[cache.py]")]
  node_audio_assembler["Audio Assembler<br/>[assembler.py]"]
  node_rendered_audio[("Rendered Audio<br/>[assembler.py]")]
end

subgraph group_voices["Voices And Runtime"]
  node_tts_registry["TTS Registry<br/>[registry.py]"]
  node_kokoro_provider["Offline Kokoro<br/>[kokoro_provider.py]"]
  node_edge_provider["Edge Voices<br/>[edge_provider.py]"]
  node_cloud_providers["Cloud Providers"]
  node_voice_library[("Voice Library<br/>[library.py]")]
  node_voice_quality["Voice Quality<br/>[quality.py]"]
  node_resource_manager["Resource Manager<br/>[resources.py]"]
end

node_user(("Studio User"))
node_online_speech["Online Speech Service"]

node_user -->|"uses studio"| node_main_window
node_app_main -->|"launches window"| node_main_window
node_main_window -->|"hosts editor"| node_script_editor
node_main_window -->|"manages projects"| node_project_manager
node_script_editor -->|"updates Markdown"| node_project_manager
node_project_manager -->|"parses script"| node_markdown_parser
node_project_manager -->|"lists voices"| node_voice_library
node_project_manager -->|"writes projects"| node_project_store
node_main_window -->|"starts generation"| node_audio_generator
node_audio_generator -->|"builds context"| node_context_builder
node_audio_generator -->|"applies substitutions"| node_pronunciation
node_audio_generator -->|"composes delivery"| node_speech_director
node_audio_generator -->|"calculates pauses"| node_pause_calculator
node_audio_generator -->|"selects provider"| node_tts_registry
node_audio_generator -->|"checks cache"| node_audio_cache
node_audio_generator -->|"synthesizes speech"| node_kokoro_provider
node_audio_generator -.->|"synthesizes speech"| node_edge_provider
node_audio_generator -.->|"synthesizes speech"| node_cloud_providers
node_edge_provider -.->|"sends script"| node_online_speech
node_audio_generator -->|"writes takes"| node_rendered_audio
node_audio_generator -->|"encodes audio"| node_audio_assembler
node_audio_assembler -->|"writes formats"| node_rendered_audio
node_audio_player -->|"reads audio"| node_rendered_audio
node_main_window -->|"controls playback"| node_audio_player
node_main_window -->|"checks references"| node_voice_quality
node_main_window -->|"checks resources"| node_resource_manager
node_resource_manager -->|"prunes cache"| node_audio_cache

click node_app_main "https://github.com/kashvats/pd_gen/blob/main/app/main.py"
click node_main_window "https://github.com/kashvats/pd_gen/blob/main/app/ui/main_window.py"
click node_script_editor "https://github.com/kashvats/pd_gen/blob/main/app/ui/script_editor.py"
click node_audio_player "https://github.com/kashvats/pd_gen/blob/main/app/ui/audio_player.py"
click node_project_manager "https://github.com/kashvats/pd_gen/blob/main/app/projects/manager.py"
click node_markdown_parser "https://github.com/kashvats/pd_gen/blob/main/app/parser/markdown_parser.py"
click node_project_store "https://github.com/kashvats/pd_gen/blob/main/app/projects/manager.py"
click node_context_builder "https://github.com/kashvats/pd_gen/blob/main/app/speech/context.py"
click node_speech_director "https://github.com/kashvats/pd_gen/blob/main/app/speech/director.py"
click node_pronunciation "https://github.com/kashvats/pd_gen/blob/main/app/speech/pronunciation.py"
click node_pause_calculator "https://github.com/kashvats/pd_gen/blob/main/app/speech/pauses.py"
click node_audio_generator "https://github.com/kashvats/pd_gen/blob/main/app/audio/generator.py"
click node_audio_cache "https://github.com/kashvats/pd_gen/blob/main/app/audio/cache.py"
click node_audio_assembler "https://github.com/kashvats/pd_gen/blob/main/app/audio/assembler.py"
click node_rendered_audio "https://github.com/kashvats/pd_gen/blob/main/app/audio/assembler.py"
click node_tts_registry "https://github.com/kashvats/pd_gen/blob/main/app/tts/registry.py"
click node_kokoro_provider "https://github.com/kashvats/pd_gen/blob/main/app/tts/kokoro_provider.py"
click node_edge_provider "https://github.com/kashvats/pd_gen/blob/main/app/tts/edge_provider.py"
click node_cloud_providers "https://github.com/kashvats/pd_gen/tree/main/app/tts"
click node_voice_library "https://github.com/kashvats/pd_gen/blob/main/app/voices/library.py"
click node_voice_quality "https://github.com/kashvats/pd_gen/blob/main/app/voices/quality.py"
click node_resource_manager "https://github.com/kashvats/pd_gen/blob/main/app/system/resources.py"

classDef toneNeutral fill:#f8fafc,stroke:#334155,stroke-width:1.5px,color:#0f172a
classDef toneBlue fill:#dbeafe,stroke:#2563eb,stroke-width:1.5px,color:#172554
classDef toneAmber fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
classDef toneMint fill:#dcfce7,stroke:#16a34a,stroke-width:1.5px,color:#14532d
classDef toneRose fill:#ffe4e6,stroke:#e11d48,stroke-width:1.5px,color:#881337
classDef toneIndigo fill:#e0e7ff,stroke:#4f46e5,stroke-width:1.5px,color:#312e81
classDef toneTeal fill:#ccfbf1,stroke:#0f766e,stroke-width:1.5px,color:#134e4a
class node_app_main,node_main_window,node_script_editor,node_audio_player,node_user toneBlue
class node_project_manager,node_markdown_parser,node_project_store toneAmber
class node_context_builder,node_speech_director,node_pronunciation,node_pause_calculator toneMint
class node_audio_generator,node_audio_cache,node_audio_assembler,node_rendered_audio toneRose
class node_tts_registry,node_kokoro_provider,node_edge_provider,node_cloud_providers,node_voice_library,node_voice_quality,node_resource_manager,node_online_speech toneIndigo
