from . import utils
from pathlib import Path
from typing import Dict, List, Optional
import importlib
import sublime, sublime_plugin

importlib.import_module('Meson')


class MesonSetupInputHandler(sublime_plugin.TextInputHandler):
	@staticmethod
	def name() -> str: return 'build_dir'
	
	@staticmethod
	def placeholder() -> str: return 'Build directory name'

class MesonSetupCommand(sublime_plugin.WindowCommand):
	def run(self, *, build_dir: str) -> None:
		self._build_dir: Path = Path(build_dir)
		
		self._build_config_path: Optional[Path] = utils.build_config_path()
		if self._build_config_path is None:
			return
		
		sublime.set_timeout_async(self.__run_async, delay=0)
	
	def input(self, args: Dict[str, str]) -> Optional[sublime_plugin.TextInputHandler]:
		if MesonSetupInputHandler.name() not in args:
			return MesonSetupInputHandler()
	
	def __run_async(self) -> None:
		if self._build_dir.is_absolute():
			if not sublime.ok_cancel_dialog(
				f'"{self._build_dir}" is relative to root!\nDo you want to setup anyway?',
				ok_title='Continue'
			): return
		utils.set_status_message(f'Setting up: {self._build_dir}')
		
		args: List[str] = [str(utils.MESON_BINARY), 'setup', str(self._build_dir)]
		if utils.OutputPanel('Meson').run_process(args) == 0:
			utils.set_status_message('Project setup complete')
		else:
			utils.set_status_message('Failed to setup project, please refer to output panel')
