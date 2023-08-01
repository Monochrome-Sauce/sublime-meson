from . import MesonCommands
from . import MesonOutput
from . import utils
from pathlib import Path
from typing import Any, Dict, List, Optional
import sublime, sublime_plugin


class MesonSetupInputHandler(sublime_plugin.TextInputHandler):
	@staticmethod
	def name() -> str: return 'build_dir'
	
	@staticmethod
	def placeholder() -> str: return 'Build directory name'

class MesonSetupCommand(sublime_plugin.WindowCommand):
	def run(self, *, build_dir: str) -> None:
		self.__build_dir: Path = Path(build_dir)
		
		self.__build_config_path: Optional[Path] = utils.Project().get_config_path()
		if self.__build_config_path is None:
			sublime.message_dialog(
				'The meson.build file wasn\'t found, check if'
				+'\n- your Meson settings in the sublime-project are correct.'
			)
			return
		
		sublime.set_timeout_async(self.__run_async, delay=0)
	
	def input(self, args: Dict[str, Any]) -> Optional[sublime_plugin.TextInputHandler]:
		if MesonSetupInputHandler.name() not in args:
			return MesonSetupInputHandler()
	
	def __run_async(self) -> None:
		if self.__build_dir.is_absolute():
			if not sublime.ok_cancel_dialog(
				f'"{self.__build_dir}" is relative to root!\nDo you want to setup anyway?',
				ok_title='Continue'
			): return
		
		project = utils.Project()
		project.status_message(f'Setting up: {self.__build_dir}')
		
		args: List[str] = MesonCommands.setup(self.__build_dir)
		if MesonOutput.Panel('Meson').run_process(args, cwd=self.__build_config_path) == 0:
			project.status_message('Project setup complete')
		else:
			project.status_message('Failed to setup project, please refer to output panel')
