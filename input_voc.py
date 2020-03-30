import gi
import csv

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class Handler:
    def __init__(self, builder):
        print('[*] Init')
        self.builder = builder
        self.submit_queue = []
        self.history = self._get_by_id('history')
        self.history.set_buffer(Gtk.TextBuffer())
        self._set_status('Wating for input...')

    def onDestroy(self, *args):
        print('[*] Quit')
        Gtk.main_quit()

    def onUndo(self, button):
        print('[*] Undo')

        if len(self.submit_queue) == 0:
            self._set_status('Nothing to undo')
        else:
            deleted = self.submit_queue.pop()
            self._update_history()
            self._set_status('Removed {}'.format(deleted))

    def onSubmit(self, button):
        print('[*] Submit')

        english = self._get_by_id('input_english').get_text()
        pinyin = self._get_by_id('input_pinyin').get_text()
        hanzi = self._get_by_id('input_hanzi').get_text()

        if english == '' or pinyin == '' or hanzi == '':
            self._set_status('One or more inputs empty. Nothing submitted')

        else:
            to_submit = {'english': english, 'pinyin': pinyin, 'hanzi': hanzi}
            self.submit_queue.append(to_submit)
            self._update_history()
            self._set_status('Added {}'.format(to_submit))

            english = self._get_by_id('input_english').set_text('')
            pinyin = self._get_by_id('input_pinyin').set_text('')
            hanzi = self._get_by_id('input_hanzi').set_text('')

        self._get_by_id('input_english').grab_focus()

    def onSubmitEnglish(self, button):
        print('[*] Enter English')

        self._get_by_id('input_pinyin').grab_focus()

    def onSubmitPinyin(self, button):
        print('[*] Enter Pinyin')

        self._get_by_id('input_hanzi').grab_focus()

    def onSave(self, button):
        print('[*] Save')

        with open('vocabulary.csv', 'a', newline='') as csv_out:
            csv_writer = csv.writer(csv_out)
            for voc in self.submit_queue:
                csv_writer.writerow([voc['english'], voc['pinyin'], voc['hanzi'], 0, 0, 0])

            self.submit_queue = []
            self._update_history()
            self._set_status('Added vocabulary to file.')


    def _update_history(self):
        self.submit_queue.reverse()
        text = self.submit_queue.__str__().replace('}, {', '}\n{').replace('[', '').replace(']', '').replace('{', '').replace('}', '')
        self.history.get_buffer().set_text(text)
        self.submit_queue.reverse()

    def _set_status(self, message):
        self._get_by_id('status_label').set_label(message)

    def _get_by_id(self, id):
        return self.builder.get_object(id)


def run():
    builder = Gtk.Builder()
    builder.add_from_file("voc_input.glade")
    builder.connect_signals(Handler(builder))

    window = builder.get_object('main_window')
    window.show_all()

    Gtk.main()

run()