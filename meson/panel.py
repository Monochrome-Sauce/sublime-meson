from . import MesonOutput
import sublime_plugin


class MesonTogglePanelCommand(sublime_plugin.WindowCommand):
	def run(self):
		MesonOutput.Panel('Meson').toggle()

class MesonClearPanelCommand(sublime_plugin.WindowCommand):
	def run(self):
		MesonOutput.Panel('Meson', clear=True)
