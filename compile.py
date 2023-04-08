from . import utils
from pathlib import Path
from typing import Dict, List, MutableMapping, Optional
import importlib, json, subprocess
import sublime, sublime_plugin

importlib.import_module('Meson')


build_dirs: List[Path] = []

def get_build_dir_names() -> List[str]:
	return [path.stem for path in build_dirs]


class MesonCompileInputHandler(sublime_plugin.ListInputHandler):
	def name(self):
		return 'selected_option'
	
	def list_items(self) -> List[str]:
		del build_dirs[:]
		for file_path in utils.introspection_data_files():
			with open(file_path) as file:
				introspection_data = json.load(file)
			loaded_build_dir = Path(introspection_data['directories']['build'])
			build_dirs.append(loaded_build_dir)
		
		return get_build_dir_names()

class MesonCompileCommand(sublime_plugin.WindowCommand):
	def run(self, selected_option: Optional[str]):
		if selected_option is None:
			if len(build_dirs) == 0: # the user didn't have anything to select
				sublime.message_dialog('Meson compile: no build directories found.')
			return
		
		self.build_dir: Path = build_dirs[get_build_dir_names().index(selected_option)]
		sublime.set_timeout_async(self.__run_async, delay=0)
	
	def input(self, args: Dict[str, str]):
		if 'selected_option' not in args:
			return MesonCompileInputHandler()
	
	def __run_async(self):
		utils.display_status_message(f'Compiling from: {self.build_dir}')
		utils.OutputPanel('Meson').update(lambda panel, env: self.__execute_meson(panel, env))
	
	def __execute_meson(self, panel: utils.OutputPanel, env: MutableMapping):
		args: List[str] = [str(utils.MESON_BINARY), 'compile', '-C', str(self.build_dir)]
		process: subprocess.Popen[bytes] = utils.run_shell_command(args, env)
		
		if process and process.stdout is not None:
			utils.process_to_panel(process, panel)
		
		status_msg: str = 'Compilation failed, please refer to output panel'
		if process.returncode == 0:
			status_msg = 'Project compiled successfully'
		utils.display_status_message(status_msg)
