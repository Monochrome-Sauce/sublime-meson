from __future__ import annotations
from pathlib import Path
from typing import IO, Any, Dict, Iterable, Mapping, Optional, List
import enum, glob, os, subprocess as sp
import sublime


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


def project_folder_path() -> Optional[Path]:
	file: Optional[str] = sublime.active_window().project_file_name();
	log(f'Project file path = {file}')
	if file: return Path(os.path.dirname(file))

def project_file_name(window: Optional[sublime.Window] = None) -> str:
		if window is None: window = sublime.active_window()
		
		project_path: Optional[str] = window.project_file_name()
		return '' if project_path is None else Path(project_path).stem

def build_config_path() -> Optional[Path]:
	project: Optional[Path] = project_folder_path()
	if project is not None:
		config_path: Path = project / BUILD_CONFIG_NAME
		if config_path.is_file(): return config_path

def set_status_message(message: str, window: Optional[sublime.Window] = None):
	if window is None:
		window = sublime.active_window()
	window.status_message(f'{PKG_NAME}: {message}')

def log(s: Any):
	print(f'[{PKG_NAME}] {s}')

def get_info_files(data: MesonInfo) -> Iterable[Path]:
	project: Optional[Path] = project_folder_path()
	if project is None:
		return []
	
	file: Path = Path(data.name.lower().replace('_', '-')).with_suffix('.json')
	file = project / '*/meson-info' / file
	data_files: List[str] = glob.glob(str(file))
	return map(Path, data_files)


class MesonInfo(enum.Enum):
	INTRO_BENCHMARKS = enum.auto()
	INTRO_BUILDOPTIONS = enum.auto()
	INTRO_BUILDSYSTEM_FILES = enum.auto()
	INTRO_DEPENDENCIES = enum.auto()
	INTRO_INSTALLED = enum.auto()
	INTRO_INSTALL_PLAN = enum.auto()
	INTRO_PROJECTINFO = enum.auto()
	INTRO_TARGETS = enum.auto()
	INTRO_TESTS = enum.auto()
	MESON_INFO = enum.auto()

class OutputPanel:
	_SYNTAX_FILES: Dict[str, str] = {
		'Meson': 'meson-output.sublime-syntax',
	}
	
	def __init__(self, name: str, *, clear: bool = False):
		assert(len(name) > 0)
		wnd: sublime.Window = sublime.active_window()
		
		# check if the panel exists to avoid having the view cleared
		tmp_panel: Optional[sublime.View] = None if clear else wnd.find_output_panel(name)
		self._panel = tmp_panel or wnd.create_output_panel(name)
		self._name = 'output.' + name
		
		if tmp_panel is None: # panel was just created
			syntax_path: Optional[str] = self._SYNTAX_FILES.get(name)
			if syntax_path is not None:
				self._panel.set_syntax_file(f'Packages/{PKG_NAME}/{syntax_path}')
	
	def write(self, message: str):
		self._panel.run_command('append',
			{ 'characters': message, 'force': True, 'scroll_to_end': True }
		)
	
	def show(self):
		sublime.active_window().run_command('show_panel', { 'panel': self._name })
	
	def hide(self):
		sublime.active_window().run_command('hide_panel', { 'panel': self._name })
	
	def toggle(self):
		wnd = sublime.active_window()
		if wnd.active_panel() == self._name:
			wnd.run_command('hide_panel')
		else:
			self.show()
	
	def run_process(self, args: List[str], *, env: Mapping = os.environ) -> int:
		project_name: str = project_file_name(sublime.active_window())
		at: str = '@' if len(project_name) != 0 else ''
		command: str = ' '.join(args)
		
		self.show()
		self.write(f'>>> {self._name}{at}{project_name}:# {command}\n')
		
		log(f'Process began with {args}')
		proc: sp.Popen[bytes] = sp.Popen(command, env=env,
			cwd=project_folder_path(), stdout=sp.PIPE, stderr=sp.PIPE, shell=True, bufsize=0
		)
		
		if proc.stdout is not None:
			self._write_io(proc.stdout)
		if proc.stderr is not None:
			self._write_io(proc.stderr)
		proc.communicate() # for the return code to be 0, this line is necessary
		
		log(f'Process ended with exit code {proc.returncode}')
		return proc.returncode
	
	def _write_io(self, stream: IO[bytes]):
		stream.flush()
		for line in iter(stream.readline, b''):
			self.write(line.decode('utf-8'))
			stream.flush()
