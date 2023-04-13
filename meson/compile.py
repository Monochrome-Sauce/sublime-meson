from . import utils
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import sublime, sublime_plugin


class MesonCompileInputHandler(sublime_plugin.ListInputHandler):
	_last_path: str = ''
	
	@staticmethod
	def name() -> str: return 'build_dir'
	
	@staticmethod
	def placeholder() -> str: return 'Meson project to compile'
	
	@classmethod
	def list_items(cls) -> List[sublime.ListInputItem]:
		build_paths: List[sublime.ListInputItem] = []
		for file_path in utils.get_info_files(utils.MesonInfo.MESON_INFO):
			with open(file_path) as file:
				meson_info = json.load(file)
			path: str = meson_info['directories']['build']
			build_paths.append(sublime.ListInputItem(Path(path).stem, path))
		utils.log(f'{build_paths=}')
		
		cls._last_path = ''
		if len(build_paths) == 1:
			cls._last_path = build_paths[-1].value
			build_paths.pop()
		return build_paths

class MesonCompileCommand(sublime_plugin.WindowCommand):
	def run(self, *, build_dir: Optional[str]) -> None:
		default: str = MesonCompileInputHandler._last_path
		self.__build_dir: Path = Path(build_dir if build_dir is not None else default)
		
		if build_dir is None and len(default) == 0:
			# the user didn't have anything to select
			sublime.message_dialog('Meson compile: no build directories found.')
		else:
			utils.log(f'{self.__build_dir=}')
			sublime.set_timeout_async(self.__run_async, delay=0)
	
	def input(self, args: Dict[str, Any]) -> Optional[sublime_plugin.ListInputHandler]:
		if MesonCompileInputHandler.name() not in args:
			return MesonCompileInputHandler()
	
	def __run_async(self) -> None:
		project = utils.Project()
		project.status_message(f'Project compilation started')
		args: List[str] = [str(utils.MESON_BINARY), 'compile', '-C', str(self.__build_dir)]
		
		if utils.OutputPanel('Meson').run_process(args) == 0:
			project.status_message('Project compiled successfully')
		else:
			project.status_message('Compilation failed, please refer to output panel')
