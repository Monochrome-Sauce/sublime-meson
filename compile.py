import sublime, sublime_plugin
import json, subprocess, importlib
from pathlib import Path
from typing import Optional, List
from . import utils

build_dirs: List[Path] = []

def get_build_dir_names() -> List[str]:
	return [path.stem for path in build_dirs]

importlib.import_module('Meson')

class MesonCompileInputHandler(sublime_plugin.ListInputHandler):
	def name(self):
		return 'selected_option'
	
	def list_items(self):
		self.clear_build_dir_lists()
		for file_path in utils.introspection_data_files():
			try:
				with open(file_path) as file:
					introspection_data = json.load(file)
				loaded_build_dir = Path(introspection_data['directories']['build'])
				build_dirs.append(loaded_build_dir)
			except Exception as e:
				raise e
		
		return get_build_dir_names()
	
	def clear_build_dir_lists(self):
		del build_dirs[:]
	
	def validate(self, value):
		return len(value.strip()) > 0

class MesonCompileCommand(sublime_plugin.WindowCommand):
	def run(self, build_dir: Optional[str], selected_option: str):
		print(f'{build_dir=}\n{selected_option=}')
		if build_dir is None:
			selected_index = get_build_dir_names().index(selected_option)
			build_dir = str(build_dirs[selected_index])
		
		assert(type(build_dir) == str) # silence LSP about the type possibly being `None`
		self.build_dir: Path = Path(build_dir)
		sublime.set_timeout_async(self.__run_async, 0)
	
	def __run_async(self):
		utils.display_status_message(f'Compiling from: {self.build_dir}')
		command_args: List[Path | str] = [utils.MESON_BINARY, 'compile', '-C', self.build_dir]
		
		def cmd_action(panel: sublime.View, env):
			process = subprocess.Popen(
				command_args, stdout=subprocess.PIPE, shell=True,
				cwd=utils.project_folder_path(), env=env, bufsize=0
			)
			if process and process.stdout is not None:
				process.stdout.flush()
				for line in iter(process.stdout.readline, b''):
					panel.run_command('append',
						{
							'characters': line.decode('utf-8'),
							'force': True,
							'scroll_to_end': True
						}
					)
					process.stdout.flush()
				process.communicate()
			
			status_msg: str = 'Project failed to compile, please refer to output panel'
			if process.returncode == 0:
				status_msg = 'Project compiled successfully'
			utils.display_status_message(status_msg)
		
		utils.update_output_panel(lambda panel, env: cmd_action(panel, env))
	
	def input(self, args):
		if 'selected_option' not in args:
			return MesonCompileInputHandler()
