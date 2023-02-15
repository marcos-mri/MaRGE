"""
session_controller.py
@author:    José Miguel Algarín
@email:     josalggui@i3m.upv.es
@affiliation:MRILab, i3M, CSIC, Valencia, Spain
"""
from ui.session_window import SessionWindow
from controller.mainviewcontroller import MainViewController
import os
import sys


class SessionController(SessionWindow):
    def __init__(self):
        super(SessionController, self).__init__()
        self.launch_gui_action.triggered.connect(self.runMainGui)
        self.close_action.triggered.connect(self.close)

    def runMainGui(self):
        self.updateSessionDict()

        # Create folder
        self.session['directory'] = 'experiments/acquisitions/%s/%s' % (
            self.session['project'], self.session['subject_id'])
        if not os.path.exists('experiments/acquisitions/%s/%s' % (self.session['project'], self.session['subject_id'])):
            os.makedirs(self.session['directory'])

        # Open the main gui
        main_gui = MainViewController(self.session)
        self.hide()
        main_gui.show()

    def closeEvent(self, *args, **kwargs):
        os.system('ssh root@192.168.1.101 "killall marcos_server"')
        print('GUI closed successfully!')

    def close(self):
        os.system('ssh root@192.168.1.101 "killall marcos_server"')
        print('GUI closed successfully!')
        sys.exit()

    def updateSessionDict(self):
        self.session = {
            'project': self.project_combo_box.currentText(),
            'study': self.study_combo_box.currentText(),
            'side': self.side_combo_box.currentText(),
            'orientation': self.orientation_combo_box.currentText(),
            'subject_id': self.id_line_edit.text(),
            'subject_name': self.name_line_edit.text(),
            'subject_surname': self.surname_line_edit.text(),
            'subject_birthday': self.birthday_line_edit.text(),
            'subject_weight': self.weight_line_edit.text(),
            'subject_height': self.height_line_edit.text(),
            'scanner': self.scanner_line_edit.text(),
            'rf_coil': self.rf_coil_combo_box.currentText(),
        }