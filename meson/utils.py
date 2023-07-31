from __future__ import annotations
from pathlib import Path
from typing import IO, Any, Callable, Dict, Iterable, Optional, List, Sequence
import enum, glob, os
import sublime


# decorator for adding static variables in a function
def static_vars(**kwargs: Any):
	def decorate(func: Callable):
		for key, val in kwargs.items():
			setattr(func, key, val)
		return func
	return decorate

BUILD_CONFIG_NAME: str = 'meson.build'
PKG_NAME: str = 'Meson'



def _test_paths_for_executable(paths: Iterable[Path], executable: str) -> Optional[Path]:
	for directory in paths:
		file_path: Path = directory / executable
		if file_path.exists() and os.access(file_path, os.X_OK):
			return file_path

def _find_binary(binary_name: str) -> Optional[Path]:
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

MESON_BINARY: Path = _find_binary('meson') or Path()
assert(MESON_BINARY.is_file())
del _test_paths_for_executable
del _find_binary



@static_vars(value=None)
def default_settings() -> Dict[str, Any]:
	if default_settings.value is None:
		resource: str = sublime.load_resource(f'Packages/{PKG_NAME}/meson.sublime-settings')
		default_settings.value = sublime.decode_value(resource)
		assert(type(default_settings.value) == dict)
	return default_settings.value

def log(s: Any):
	print(f'[{PKG_NAME}] {s}')

def get_info_files(data: MesonInfo) -> Iterable[Path]:
	config_path: Optional[Path] = Project().get_config_path()
	if config_path is None: return []
	
	file: Path = config_path / '*/meson-info' / data.value
	log(f'get_info_files: {file=}')
	data_files: List[str] = glob.glob(str(file))
	log(f'get_info_files: {data_files=}')
	return map(Path, data_files)

def _pipe_streams(streams: List[IO[bytes]], output: IO[str]):
	toRemove: List[int] = []
	for ind, stream in enumerate(streams):
		stream.flush()
		line = stream.readline()
		
		if line == b'':
			toRemove.append(ind)
		else:
			output.write(line.decode())
	
	for i in toRemove:
		del streams[i]

def pipe_streams_in_parallel(streams: Sequence[IO[bytes]], output: IO[str]):
	streams = list(streams)
	while len(streams):
		_pipe_streams(streams, output)


class MesonInfo(enum.Enum):
	INTRO_BENCHMARKS = Path('intro-benchmarks.json')
	INTRO_BUILDOPTIONS = Path('intro-buildoptions.json')
	INTRO_BUILDSYSTEM_FILES = Path('intro-buildsystem-files.json')
	INTRO_DEPENDENCIES = Path('intro-dependencies.json')
	INTRO_INSTALLED = Path('intro-installed.json')
	INTRO_INSTALL_PLAN = Path('intro-install-plan.json')
	INTRO_PROJECTINFO = Path('intro-projectinfo.json')
	INTRO_TARGETS = Path('intro-targets.json')
	INTRO_TESTS = Path('intro-tests.json')
	MESON_INFO = Path('meson-info.json')

class Project:
	def __init__(self, window: Optional[sublime.Window] = None) -> None:
		if window is None: window = sublime.active_window()
		self.window: sublime.Window = window
	
	def get_path(self) -> Optional[Path]:
		path: Optional[str] = self.window.project_file_name()
		if path is not None: return Path(path)
	
	def get_folder(self) -> Optional[Path]:
		path: Optional[str] = self.window.project_file_name();
		if path is not None: return Path(os.path.dirname(path))
	
	def get_name(self) -> str:
		path: Optional[str] = self.window.project_file_name();
		return '' if path is None else os.path.basename(path)
	
	def get_settings(self) -> Dict[str, Any]:
		view: Optional[sublime.View] = self.window.active_view()
		if view is None: return {}
		
		settings: Any = view.settings().get(PKG_NAME, {})
		return settings if type(settings) == dict else {}
	
	def get_config_path(self) -> Optional[Path]:
		KEY: str = "build_folder"
		default: str = default_settings()[KEY]
		
		build_folder = self.get_settings().get(KEY)
		if type(build_folder) != type(default):
			build_folder = default
		
		project_folder: Optional[Path] = self.get_folder()
		if project_folder is None: return
		
		assert(type(build_folder) == str)
		config_path: Path = project_folder / build_folder
		log(f'get_config_path: {config_path}')
		if config_path.is_dir(): return config_path
	
	def status_message(self, message: str):
		self.window.status_message(f'{PKG_NAME}: {message}')
