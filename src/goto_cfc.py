import sublime, sublime_plugin
from collections import namedtuple

GotoCfc = namedtuple('GotoCfc', 'file_path symbol')

goto_sources = []

def add_goto_source(callback):
	goto_sources.append(callback)

def get_cfcs(view, position):
	cfcs = [ ]

	for callback in goto_sources:
		gotocfc = callback(view, position)
		if gotocfc:
			cfcs.append(gotocfc)

	return cfcs

def open_file_at_symbol(view, file_path, symbol):
	index_locations = view.window().lookup_symbol_in_index(symbol)
	if file_path[1] == ":":
		file_path = "/" + file_path[0] + file_path[2:]

	for full_path, project_path, rowcol in index_locations:
		if full_path == file_path:
			row, col = rowcol
			view.window().open_file(full_path + ":" + str(row) + ":" + str(col), sublime.ENCODED_POSITION | sublime.FORCE_GROUP)
			break
	else:
		# if symbol can't be found in the index, go ahead and open the file
		view.window().open_file(file_path)

class CfmlGotoCfcCommand(sublime_plugin.TextCommand):

	def run(self, edit, event):
		pt = self.view.window_to_text((event["x"], event["y"]))
		cfcs = get_cfcs(self.view, pt)
		if len(cfcs) > 0:
			if cfcs[0].symbol:
				open_file_at_symbol(self.view, cfcs[0].file_path, cfcs[0].symbol)
			else:
				self.view.window().open_file(cfcs[0].file_path)

	def want_event(self):
			return True
