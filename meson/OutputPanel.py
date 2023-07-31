from . import utils
from pathlib import Path
from typing import IO, Dict, List, Mapping, Optional
import os
import sublime


class OutputPanelStream(IO[str]):
	def __init__(self, name: str, panel: sublime.View):
		self.__name = name
		self.panel = panel
	
	def isatty(self) -> bool:
		return False
	
	def readable(self) -> bool:
		return False
	
	def seekable(self) -> bool:
		return False
	
	def writable(self) -> bool:
		return True
	
	def mode(self) -> str:
		return 'w'
	
	def name(self) -> str:
		return self.__name
	
	def fileno(self) -> int:
		return -1
	
	def flush(self) -> None:
		pass
	
	def write(self, s: str) -> int:
		self.panel.run_command('append',
			{ 'characters': s, 'force': True, 'scroll_to_end': True }
		)
		return len(s)
	
	def writelines(self, lines: List[str]) -> None:
		for s in lines:
			self.write(s)
			self.write('\n')
	
	def __enter__(self) -> IO[str]:        raise NotImplementedError
	def __exit__(self, *_) -> None:        raise NotImplementedError
	def close(self) -> None:               raise NotImplementedError
	def closed(self) -> bool:              raise NotImplementedError
	def read(self, *_) -> str:             raise NotImplementedError
	def readline(self, *_) -> str:         raise NotImplementedError
	def readlines(self, *_) -> List[str]:  raise NotImplementedError
	def seek(self, *_) -> int:             raise NotImplementedError
	def tell(self) -> int:                 raise NotImplementedError
	def truncate(self, *_) -> int:         raise NotImplementedError

class OutputPanel:
	__SYNTAX_FILES: Dict[str, str] = {
		'Meson': 'meson-output.sublime-syntax',
	}
	
	__slots__ = ('output')
	
	def __init__(self, name: str, *, clear: bool = False):
		assert(len(name) > 0)
		wnd: sublime.Window = sublime.active_window()
		
		# check if the panel exists to avoid having the view cleared
		tmp_panel: Optional[sublime.View] = None if clear else wnd.find_output_panel(name)
		
		self.output = OutputPanelStream('output.' + name,
			tmp_panel or wnd.create_output_panel(name)
		)
		
		if tmp_panel is not None:
			return # panel already existed
		self.write_start_line(utils.Project(wnd).get_name())
		
		syntax_path: Optional[str] = self.__SYNTAX_FILES.get(name)
		if syntax_path is not None:
			panel: sublime.View = self.output.panel
			panel.set_syntax_file(f'Packages/{utils.PKG_NAME}/{syntax_path}')
	
	def show(self):
		sublime.active_window().run_command('show_panel', { 'panel': self.output.name() })
	
	def hide(self):
		sublime.active_window().run_command('hide_panel', { 'panel': self.output.name() })
	
	def toggle(self):
		wnd = sublime.active_window()
		if wnd.active_panel() == self.output.name():
			wnd.run_command('hide_panel')
		else:
			self.show()
	
	def write_start_line(self, project_name: str):
		at: str = '@' if len(project_name) != 0 else ''
		
		# Python 3.9 adds the option to do this instead:
		# project_name = project_name.removesuffix('.sublime-project')
		suffix='.sublime-project'
		if suffix and project_name.endswith(suffix):
			project_name = project_name[:-len(suffix)]
		
		self.output.write(f'>>> {self.output.name()}{at}{project_name}:# ')
	
	def run_process(self, args: List[str], *,
		env: Mapping = os.environ, cwd: Optional[Path] = None
	) -> int:
		project: utils.Project = utils.Project()
		command: str = ' '.join(args)
		
		self.show()
		self.output.write(f'{command}\n')
		
		utils.log(f'Process began with {args}')
		if cwd is None: cwd = project.get_folder()
		
		import subprocess as sp
		proc: sp.Popen[bytes] = utils.execute_process(args, cwd, env, 0)
		
		streamList = [stream
			for stream in (proc.stdout, proc.stderr)
			if stream is not None
		]
		utils.pipe_streams_in_parallel(streamList, self.output)
		proc.communicate() # for the return code to be 0, this line is necessary
		self.write_start_line(project.get_name())
		
		utils.log(f'Process ended with exit code {proc.returncode}')
		return proc.returncode
