from .OutputPanel import OutputPanel
import sublime_plugin


class MesonTogglePanelCommand(sublime_plugin.WindowCommand):
	def run(self):
		OutputPanel('Meson').toggle()

class MesonClearPanelCommand(sublime_plugin.WindowCommand):
	def run(self):
		OutputPanel('Meson', clear=True)
