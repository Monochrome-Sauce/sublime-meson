from . import utils
from pathlib import Path
from typing import Iterable, List, Optional
import importlib, json, subprocess
import sublime, sublime_plugin

importlib.import_module('Meson')


build_dirs: List[Path] = []

def get_build_dir_names() -> List[str]:
	return [path.stem for path in build_dirs]


class MesonCompileInputHandler(sublime_plugin.ListInputHandler):
	def name(self):
		return 'selected_option'
	
	def list_items(self) -> Iterable[str]:
		self.__clear_build_dirs_list()
		for file_path in utils.introspection_data_files():
			with open(file_path) as file:
				introspection_data = json.load(file)
			loaded_build_dir = Path(introspection_data['directories']['build'])
			build_dirs.append(loaded_build_dir)
		
		return get_build_dir_names()
	
	def __clear_build_dirs_list(self):
		del build_dirs[:]

class MesonCompileCommand(sublime_plugin.WindowCommand):
	def run(self, selected_option: Optional[str]):
		if selected_option is None:
			print(f'Meson compile: nothing to do ({selected_option=}).')
			return
		
		self.build_dir: Path = build_dirs[get_build_dir_names().index(selected_option)]
		sublime.set_timeout_async(self.__run_async, 0)
	
	def input(self, args):
		if 'selected_option' not in args:
			return MesonCompileInputHandler()
	
	def __run_async(self):
		utils.display_status_message(f'Compiling from: {self.build_dir}')
		utils.update_output_panel(lambda panel, env:
			self.__execute_meson(panel, env, self.build_dir)
		)
	
	@staticmethod
	def __execute_meson(panel: sublime.View, env, build_directory: Path):
		cmd_arg: str = f'{utils.MESON_BINARY} compile -C {build_directory}'
		process = subprocess.Popen(
			cmd_arg, stdout=subprocess.PIPE, shell=True,
			cwd=utils.project_folder_path(), env=env, bufsize=0
		)
		if process and process.stdout is not None:
			process.stdout.flush()
			for line in iter(process.stdout.readline, b''):
				utils.write_to_output_panel(panel, utf8data=line)
				process.stdout.flush()
			process.communicate()
		
		status_msg: str = 'Project failed to compile, please refer to output panel'
		if process.returncode == 0:
			status_msg = 'Project compiled successfully'
		utils.display_status_message(status_msg)
