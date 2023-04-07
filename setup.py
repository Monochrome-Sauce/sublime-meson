from collections.abc import MutableMapping
from . import utils
from pathlib import Path
from typing import Dict, List, Optional
import importlib, subprocess as sp
import sublime, sublime_plugin


class Requests:
	BUILD_DIR: Dict[str, str] = {
		'arg': 'build_dir',
		'placeholder': 'Build directory path',
	}

importlib.import_module('Meson')

class MesonSetupInputHandler(sublime_plugin.TextInputHandler):
	def __init__(self, request: Dict[str, str]):
		self._name: str = request['arg']
		self._placeholder: str = request['placeholder']
	
	def name(self):
		return self._name
	
	def placeholder(self):
		return self._placeholder

class MesonSetupCommand(sublime_plugin.WindowCommand):
	def run(self, build_dir: str):
		self.build_dir: Path = Path(build_dir)
		
		self.build_config_path: Optional[Path] = utils.build_config_path()
		if self.build_config_path is None:
			return None
		
		sublime.set_timeout_async(self.__run_async, 0)
	
	def __run_async(self):
		utils.display_status_message(f'Setting up from: {self.build_dir}')
		utils.OutputPanel('Meson').update(self.__execute_meson)
	
	def __execute_meson(self, panel: utils.OutputPanel, env: MutableMapping):
		arg_list: List[str] = [str(utils.MESON_BINARY), 'setup', str(self.build_dir)]
		
		process: sp.Popen[bytes] = utils.run_shell_command(arg_list, env)
		if process and process.stdout is not None:
			utils.process_to_panel(process, panel)
		
		status_msg: str = 'Failed to setup project, please refer to output panel'
		if process.returncode == 0:
			status_msg = 'Project setup complete'
		utils.display_status_message(status_msg)
	
	def input(self, args):
		input_requests: List[Dict[str, str]] = []
		if 'build_dir' not in args:
			input_requests.append(Requests.BUILD_DIR)
		
		for input_request in input_requests:
			return MesonSetupInputHandler(input_request)
