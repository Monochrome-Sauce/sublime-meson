from . import utils
import sublime_plugin


class MesonTogglePanelCommand(sublime_plugin.WindowCommand):
	def run(self):
		utils.OutputPanel('Meson').toggle()

class MesonClearPanelCommand(sublime_plugin.WindowCommand):
	def run(self):
		utils.OutputPanel('Meson').clear()
