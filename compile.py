from . import utils
from pathlib import Path
from typing import Dict, List, Optional
import importlib, json
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
		args: List[str] = [str(utils.MESON_BINARY), 'compile', '-C', str(self.build_dir)]
		retcode: int = utils.OutputPanel('Meson').run_process(args)
		
		if retcode == 0:
			utils.display_status_message('Project compiled successfully')
		else:
			utils.display_status_message('Compilation failed, please refer to output panel')
