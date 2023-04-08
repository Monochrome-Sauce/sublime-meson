from . import utils
import sublime_plugin


class MesonTogglePanelCommand(sublime_plugin.WindowCommand):
	def run(self):
		utils.OutputPanel('Meson', print_at=False).toggle()

class MesonClearPanelCommand(sublime_plugin.WindowCommand):
	def run(self):
		utils.OutputPanel('Meson', clear=True, print_at=False)
