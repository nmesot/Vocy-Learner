import gi
import csv
from random import shuffle

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class Handler:
    def __init__(self, builder):
        print('[*] Init')
        self.running = False
        self.builder = builder
        self.mode = 'Pinyin and Hanzi to English'
        self._load_vocabulary()

    def _flip_sensitivity(self):
        sensitive_while_stopped = ['sr_btn', 'sr_val', 'streak_btn', 'streak_val',\
            'h_e', 'ph_e', 'p_e', 'e_p', 'e_h', 'h_p', 'p_h']

        sensitive_while_running = ['output', 'next_btn']

        for o in sensitive_while_stopped:
            self.builder.get_object(o).set_sensitive(self.running)

        for o in sensitive_while_running:
            self.builder.get_object(o).set_sensitive(not self.running)

    def _load_vocabulary(self):
        print('[**] Load vocabulary')

        vocabulary = []
        with open('vocabulary.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            next(csv_reader)
            for row in csv_reader:
                row_formatted = [row[0], row[1], row[2], int(row[3]), int(row[4]), int(row[5])]
                vocabulary.append(row_formatted)

        self.vocabulary = vocabulary

    def _store_vocabulary(self):
        print('[**] Store vocabulary')

        with open('vocabulary.csv', 'w', newline='') as csv_out:
            csv_writer = csv.writer(csv_out)
            csv_writer.writerow(['english','pinyin','hanzi','correct','wrong','streak'])
            csv_writer.writerows(self.vocabulary)


    def _get_valid_idxs(self):
        idxs = []
        for voc, idx in zip(self.vocabulary, range(len(self.vocabulary))):
            i, o = self._get_relevant_voc(voc)
            if i is not None and o is not None:
                idxs.append(idx)

        shuffle(idxs)
        print(idxs)
        return idxs

    def _get_relevant_voc(self, voc):
        i, o = None, None
        correct, wrong, streak_voc = int(voc[3]), int(voc[4]), int(voc[5])
        if streak_voc <= self.streak and (correct+wrong==0 or correct/(correct+wrong) >= self.sr):
            english, pinyin, hanzi = voc[0], voc[1], voc[2]
            if self.mode == 'Pinyin and Hanzi to English':
                i = '{}  -  {}'.format(pinyin, hanzi)
                o = english
            elif self.mode == 'Hanzi to English':
                i = hanzi
                o = english
            elif self.mode == 'Pinyin to English': 
                i = pinyin
                o = english
            elif self.mode == 'English to Pinyin':
                i = english
                o = pinyin
            elif self.mode == 'Hanzi to Pinyin':
                i = hanzi
                o = pinyin
            elif self.mode == 'English to Hanzi':
                i = english
                o = hanzi
            elif self.mode == 'Pinyin to Hanzi':
                i = pinyin
                o = hanzi

        return i, o

    def _check_if_correct(self, output):
        output = self.builder.get_object('output').get_text()
        input_previous, should = self._get_relevant_voc(self.vocabulary[self.valid_idxs[self.index-1]])
        if should != output:
            print('[**] Wrong: {} != {}, {} == {}'.format(input_previous, output, input_previous, should))

            self.vocabulary[self.valid_idxs[self.index-1]][4] += 1
            self.vocabulary[self.valid_idxs[self.index-1]][5] = 0
            self.incorrect += 1
            self.builder.get_object('correct_incorrect').set_markup('<span foreground=\'red\'>Incorrect - {}</span>'.format(should))
        else:
            print('[**] Correct: {} == {}'.format(input_previous, output))

            self.vocabulary[self.valid_idxs[self.index-1]][3] += 1
            self.vocabulary[self.valid_idxs[self.index-1]][5] += 1
            self.correct += 1
            self.builder.get_object('correct_incorrect').set_markup('<span foreground=\'green\'>Correct</span>')

        fraction_correct = 0 if self.correct + self.incorrect == 0 else self.correct / (self.correct+self.incorrect)
        self.builder.get_object('success_rate_label').set_label('{}% correct'.format(int(fraction_correct*100)))

        fraction_progress = self.index / len(self.valid_idxs)
        self.builder.get_object('progress_bar').set_fraction(fraction_progress)


    def _process_next(self):
        #finish run
        if self.index == len(self.valid_idxs) + 1:
            self._stop()
            return

        #reached end of vocabulary
        if self.index == len(self.valid_idxs):
            output = self.builder.get_object('output').get_text()
            self._check_if_correct(output)
            self.builder.get_object('next_btn').set_label('Finish')
            self.builder.get_object('all_time_correct_lbl').set_label('')
            self.builder.get_object('streak_lbl').set_label('')
            self.index += 1
            return

        #first vocabulary, no need to check previous vocabulary
        if self.index == 0:
            voc = self.vocabulary[self.valid_idxs[self.index]]
            i, _ = self._get_relevant_voc(voc)
            corr, inc, streak = voc[3], voc[4], voc[5]
            perf = 0 if corr+inc==0 else corr/(corr+inc)
            self._set_input(i, int(100*perf), streak)
            self.index += 1
        else:
            #check if last vocabulary was correct
            output = self.builder.get_object('output').get_text()
            self._check_if_correct(output)

            #clear input field
            self.builder.get_object('output').set_text('')

            #set new input
            voc = self.vocabulary[self.valid_idxs[self.index]]
            i, _ = self._get_relevant_voc(voc)
            corr, inc, streak = voc[3], voc[4], voc[5]
            perf = 0 if corr+inc==0 else corr/(corr+inc)
            input_next, _ = self._get_relevant_voc(voc)
            self._set_input(input_next, int(100*perf), streak)
            self.index += 1

    def _set_input(self, i, perf, streak):
        self.builder.get_object('input').set_markup('<big><big><big><big><big><big><big>{}</big></big></big></big></big></big></big>'.format(i))
        self.builder.get_object('all_time_correct_lbl').set_label('All time performance: {}%'.format(perf))
        self.builder.get_object('streak_lbl').set_label('Current Streak: {}'.format(streak))

    def _start(self):
        print('[*] Start')

        sr, streak = 0.75, 3

        if not self.builder.get_object('sr_btn').get_active(): sr=0
        else:
            try:
                sr = float(self.builder.get_object('sr_val').get_text())
            except:
                print('Input valid number for success rate. Must be float.')
                return

        if not self.builder.get_object('streak_btn').get_active(): streak=999999999
        else:
            try:
                streak = int(self.builder.get_object('streak_val').get_text())
            except:
                print('Input valid number for streak length. Must be int')
                return

        self.sr = sr
        self.streak = streak

        self._flip_sensitivity()
        self.running = True
        self.builder.get_object('start_btn').set_label('Stop')

        self.index = 0
        self.valid_idxs = self._get_valid_idxs()
        if len(self.valid_idxs) == 0:
            self._stop()
            return
        self.correct, self.incorrect = 0, 0
        self._process_next()

    def _stop(self):
        self._flip_sensitivity()
        fraction_correct = 0 if self.correct + self.incorrect == 0 else self.correct / (self.correct+self.incorrect)
        self.builder.get_object('input').set_label('{}% correct\n-- Press Start --'.format(int(fraction_correct*100)))
        self.running = False
        self.builder.get_object('start_btn').set_label('Start')
        self.builder.get_object('next_btn').set_label('Enter/Next')
        self.builder.get_object('success_rate_label').set_label('')
        self.builder.get_object('progress_bar').set_fraction(0)
        self.builder.get_object('output').set_text('')
        self.builder.get_object('correct_incorrect').set_markup('')
        self.index = 0

        self._store_vocabulary()

        print('[*] Stop')

    def onDestroy(self, *args):
        print('[*] Quit')
        Gtk.main_quit()

    def onStartButtonPressed(self, button):
        if not self.running:
            self._start()
        else:
            self._stop()

    def onNextButtonPressed(self, button):
        print('[*] Next')

        self._process_next()

    def onButtonToggled(self, button):
        if button.get_active():
            print('[*] Toggle Mode')
            self.mode = button.get_label()

def run():
    builder = Gtk.Builder()
    builder.add_from_file("gui.glade")
    builder.connect_signals(Handler(builder))

    window = builder.get_object('main_window')
    window.show_all()

    Gtk.main()

run()