from __future__ import annotations
from pathlib import Path
from typing import IO, Any, Callable, Dict, Iterable, Mapping, Optional, List
import enum, glob, os, subprocess as sp
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

class OutputPanel:
	__SYNTAX_FILES: Dict[str, str] = {
		'Meson': 'meson-output.sublime-syntax',
	}
	
	def __init__(self, name: str, *, clear: bool = False):
		assert(len(name) > 0)
		wnd: sublime.Window = sublime.active_window()
		
		# check if the panel exists to avoid having the view cleared
		tmp_panel: Optional[sublime.View] = None if clear else wnd.find_output_panel(name)
		self.__panel = tmp_panel or wnd.create_output_panel(name)
		self.__name = 'output.' + name
		
		if tmp_panel is None: # panel was just created
			syntax_path: Optional[str] = self.__SYNTAX_FILES.get(name)
			if syntax_path is not None:
				self.__panel.set_syntax_file(f'Packages/{PKG_NAME}/{syntax_path}')
	
	def write(self, message: str):
		self.__panel.run_command('append',
			{ 'characters': message, 'force': True, 'scroll_to_end': True }
		)
	
	def show(self):
		sublime.active_window().run_command('show_panel', { 'panel': self.__name })
	
	def hide(self):
		sublime.active_window().run_command('hide_panel', { 'panel': self.__name })
	
	def toggle(self):
		wnd = sublime.active_window()
		if wnd.active_panel() == self.__name:
			wnd.run_command('hide_panel')
		else:
			self.show()
	
	def run_process(self, args: List[str], *,
		env: Mapping = os.environ, cwd: Optional[Path] = None
	) -> int:
		project: Project = Project()
		
		project_name: str = project.get_name()
		at: str = '@' if len(project_name) != 0 else ''
		command: str = ' '.join(args)
		
		self.show()
		self.write(f'>>> {self.__name}{at}{project_name}:# {command}\n')
		
		log(f'Process began with {args}')
		if cwd is None: cwd = project.get_folder()
		proc: sp.Popen[bytes] = sp.Popen(command, env=env,
			cwd=cwd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, bufsize=0
		)
		
		if proc.stdout is not None:
			self.__write_io(proc.stdout)
		if proc.stderr is not None:
			self.__write_io(proc.stderr)
		proc.communicate() # for the return code to be 0, this line is necessary
		
		log(f'Process ended with exit code {proc.returncode}')
		return proc.returncode
	
	def __write_io(self, stream: IO[bytes]):
		stream.flush()
		for line in iter(stream.readline, b''):
			self.write(line.decode('utf-8'))
			stream.flush()
