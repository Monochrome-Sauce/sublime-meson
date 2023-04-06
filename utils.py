from pathlib import Path
from typing import Any, Callable, Iterable, MutableMapping, Optional, List
import glob, os
import sublime


BUILD_CONFIG_NAME: str = 'meson.build'
STATUS_MESSAGE_PREFIX: str = 'Meson'


def _test_paths_for_executable(paths: Iterable[Path], executable: str) -> Optional[Path]:
	for directory in paths:
		file_path: Path = directory / executable
		if file_path.exists() and os.access(file_path, os.X_OK):
			return file_path

def find_binary(binary_name: str) -> Optional[Path]:
	paths: Iterable[Path] = map(Path, os.environ.get('PATH', '').split(os.pathsep))
	if os.name == 'nt':
		binary_name += '.exe'
	
	path: Optional[Path] = _test_paths_for_executable(paths, binary_name)
	if path:
		return path;
	
	# /usr/local/bin:/usr/local/meson/bin
	if os.name == 'nt':
		extra_paths = (
			os.path.join(os.environ.get('ProgramFiles', ''), 'meson', 'bin'),
			os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'meson', 'bin'),
		)
	else:
		extra_paths = ('/usr/local/bin', '/usr/local/meson/bin')
	
	return _test_paths_for_executable(map(Path, extra_paths), binary_name)

MESON_BINARY: Path = find_binary('meson') or Path()
assert(MESON_BINARY.is_file())
del _test_paths_for_executable


def project_folder_path() -> Optional[Path]:
	file: Optional[str] = sublime.active_window().project_file_name();
	if file: return Path(os.path.dirname(file))

def build_config_path() -> Optional[Path]:
	project: Optional[Path] = project_folder_path()
	if project is not None:
		config_path: Path = project / BUILD_CONFIG_NAME
		if config_path.is_file(): return config_path

def introspection_data_files() -> Iterable[Path]:
	project: Optional[Path] = project_folder_path()
	if project is None:
		return []
	
	data_files: List[str] = glob.glob(str(project / '*/meson-info/meson-info.json'))
	return map(Path, data_files)

def display_status_message(message: str):
	sublime.active_window().status_message(f'{STATUS_MESSAGE_PREFIX}: {message}')

def update_output_panel(cmd_action: Callable[[sublime.View, MutableMapping], Any]):
	panel: sublime.View = sublime.active_window().create_output_panel('Meson')
	sublime.active_window().run_command('show_panel', {'panel': 'output.Meson'})
	panel.set_read_only(False)
	
	# env = os.environ
	# env['COLORTERM'] = 'nocolor'
	res = cmd_action(panel, os.environ)
	panel.set_read_only(True)
	return res

def write_to_output_panel(panel: sublime.View, *, utf8data: bytes):
	panel.run_command('append', {
			'characters': utf8data.decode('utf-8'),
			'force': True, 'scroll_to_end': True
		}
	)
