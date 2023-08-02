from __future__ import annotations
from pathlib import Path
from typing import IO, Any, Callable, Dict, Iterable, Mapping, Optional, List, Sequence
import enum, glob, os, subprocess as sp
import sublime


def static_vars(**kwargs: Any):
	'''Decorator for using static variables in a function'''
	def decorate(func: Callable):
		for key, val in kwargs.items():
			setattr(func, key, val)
		return func
	return decorate

BUILD_CONFIG_NAME: str = 'meson.build'
PKG_NAME: str = 'Meson'



@static_vars(value=None)
def default_settings() -> Dict[str, Any]:
	if default_settings.value is None:
		resource: str = sublime.load_resource(f'Packages/{PKG_NAME}/meson.sublime-settings')
		default_settings.value = sublime.decode_value(resource)
		assert(type(default_settings.value) == dict)
	return default_settings.value

def log(s: Any):
	'''Print `s` to stdout with "[`PKG_NAME`]" prefixed to it'''
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
	'''#Pipe the contents from `streams` to `output` in parallel.
	The process is as follows:
	
	- flush the stream.
	- read a single line and write it to `output`.
	- if EOL is reached - remove the stream from the list.
	- repeat on the next stream, until all streams are removed.
	'''
	streams = list(streams)
	while len(streams):
		_pipe_streams(streams, output)

def execute_process(
	args: Sequence[str], cwd: Optional[Path],
	env: Mapping = os.environ, buffer_size: int = -1
) -> sp.Popen[bytes]:
	'''#Start a process relative to `cwd` with the given `args`.
	The STDOUT and STDERR of the process are piped to `subprocess.PIPE`.
	
	`cwd` must be an absolute path.
	'''
	if cwd is not None: assert(cwd.is_absolute())
	return sp.Popen(cwd=cwd, args=args,
		env=env, shell=False,
		bufsize=buffer_size, stdout=sp.PIPE, stderr=sp.PIPE,
	)

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
	'''#Wrapper for sublime.Window objects and their project related methods
	The wrapper adds:
	
	- Directly getting the path and folder as Path objects.
	- Directly getting the name of the name.
	- Cleaner access to the project settings.
	- Setting the status message with a proper prefix.
	'''
	
	def __init__(self, window: Optional[sublime.Window] = None):
		'''
		@param window: optionally provide a window instead of the class
		automatically getting the active one.
		'''
		if window is None: window = sublime.active_window()
		self.window: sublime.Window = window
	
	def get_path(self) -> Optional[Path]:
		'''Equivalent to `sublime.Window.project_file_name()`'''
		path: Optional[str] = self.window.project_file_name()
		if path is not None: return Path(path)
	
	def get_folder(self) -> Optional[Path]:
		'''Equivalent to getting the dirname of `get_path()`'s result'''
		path: Optional[str] = self.window.project_file_name();
		if path is not None: return Path(os.path.dirname(path))
	
	def get_name(self) -> str:
		'''Equivalent to getting the basename of `get_path()`'s result'''
		path: Optional[str] = self.window.project_file_name();
		return '' if path is None else os.path.basename(path)
	
	def get_settings(self) -> Dict[str, Any]:
		'''Get the current Meson settings for the Project's active view'''
		view: Optional[sublime.View] = self.window.active_view()
		if view is None: return {}
		
		settings: Any = view.settings().get(key=PKG_NAME, default={})
		return settings if type(settings) == dict else {}
	
	def get_config_path(self) -> Optional[Path]:
		'''This is one messy function...
		#TODO: Refactor this shit.
		'''
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
		'''Set the status message with "`PKG_NAME`: " prefixed to it'''
		self.window.status_message(f'{PKG_NAME}: {message}')
