#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import os

from PyQt4 import QtGui, QtCore
from libpydaw import *
from mkplugins import *

from libpydaw.pydaw_util import *
from libpydaw.pydaw_widgets import *
from libpydaw.translate import _
import libpydaw.strings
import libmk


def set_tooltips_enabled(a_enabled):
    """ Set extensive tooltips as an alternative to
        maintaining a separate user manual
    """
    libmk.TOOLTIPS_ENABLED = a_enabled

    f_list = [WAVE_EDITOR, TRANSPORT,]
    for f_widget in f_list:
        f_widget.set_tooltips(a_enabled)


def pydaw_scale_to_rect(a_to_scale, a_scale_to):
    """ Returns a tuple that scales one QRectF to another """
    f_x = (a_scale_to.width() / a_to_scale.width())
    f_y = (a_scale_to.height() / a_to_scale.height())
    return (f_x, f_y)


class WaveNextOsc(libmk.AbstractIPC):
    def __init__(self, a_with_audio=False,
             a_configure_path="/musikernel/wavenext"):
        libmk.AbstractIPC.__init__(self, a_with_audio, a_configure_path)

    def pydaw_wn_playback(self, a_mode):
        self.send_configure("wnp", str(a_mode))

    def pydaw_set_plugin(
    self, a_track_num, a_index, a_plugin_index, a_uid, a_on):
        self.send_configure(
            "pi", "|".join(str(x) for x in
            (a_track_num, a_index, a_plugin_index,
             a_uid, bool_to_int(a_on))))

    def pydaw_save_tracks(self):
        self.send_configure("st", "")

    def pydaw_we_export(self, a_file_name):
        self.send_configure("wex", "{}".format(a_file_name))

    def pydaw_ab_open(self, a_file):
        self.send_configure("abo", str(a_file))

    def pydaw_we_set(self, a_val):
        self.send_configure("we", str(a_val))

    def pydaw_panic(self):
        self.send_configure("panic", "")

    def save_audio_inputs(self):
        self.send_configure("ai", "")

wavenext_folder = os.path.join("projects", "wavenext")
wavenext_folder_tracks = os.path.join(wavenext_folder, "tracks")
pydaw_file_wave_editor_bookmarks = os.path.join(
    wavenext_folder, "bookmarks.txt")
pydaw_file_notes = os.path.join(wavenext_folder, "notes.txt")
pydaw_file_pyinput = os.path.join(wavenext_folder, "input.txt")


class WaveNextProject(libmk.AbstractProject):
    def __init__(self, a_with_audio):
        self.wn_osc = WaveNextOsc(a_with_audio)
        self.suppress_updates = False

    def save_track_plugins(self, a_uid, a_track):
        f_folder = wavenext_folder_tracks
        if not self.suppress_updates:
            self.save_file(f_folder, str(a_uid), str(a_track))

    def set_project_folders(self, a_project_file):
        #folders
        self.project_folder = os.path.dirname(a_project_file)
        self.project_file = os.path.splitext(
            os.path.basename(a_project_file))[0]
        self.wn_track_pool_folder = os.path.join(
            self.project_folder, wavenext_folder_tracks)
        #files
        self.pynotes_file = os.path.join(
            self.project_folder, pydaw_file_notes)
        self.pywebm_file = os.path.join(
            self.project_folder, pydaw_file_wave_editor_bookmarks)
        self.audio_inputs_file = os.path.join(
            self.project_folder, pydaw_file_pyinput)

        self.project_folders = [
            self.project_folder, self.wn_track_pool_folder,]

    def open_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)
        if not os.path.exists(a_project_file):
            print("project file {} does not exist, creating as "
                "new project".format(a_project_file))
            self.new_project(a_project_file)

#        if a_notify_osc:
#            self.wn_osc.pydaw_open_song(self.project_folder)

    def new_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)

        for project_dir in self.project_folders:
            print(project_dir)
            if not os.path.isdir(project_dir):
                os.makedirs(project_dir)

#        self.commit("Created project")
#        if a_notify_osc:
#            self.wn_osc.pydaw_open_song(self.project_folder)

    def get_notes(self):
        if os.path.isfile(self.pynotes_file):
            return pydaw_read_file_text(self.pynotes_file)
        else:
            return ""

    def write_notes(self, a_text):
        pydaw_write_file_text(self.pynotes_file, a_text)

    def set_we_bm(self, a_file_list):
        f_list = [x for x in sorted(a_file_list) if len(x) < 1000]
        pydaw_write_file_text(self.pywebm_file, "\n".join(f_list))

    def get_we_bm(self):
        if os.path.exists(self.pywebm_file):
            f_list = pydaw_read_file_text(self.pywebm_file).split("\n")
            return [x for x in f_list if x]
        else:
            return []

    def get_track_plugins(self,  a_track_num):
        f_folder = self.wn_track_pool_folder
        f_path = os.path.join(*(str(x) for x in (f_folder, a_track_num)))
        if os.path.isfile(f_path):
            with open(f_path) as f_handle:
                f_str = f_handle.read()
            return libmk.pydaw_track_plugins.from_str(f_str)
        else:
            return None

    def save_audio_inputs(self, a_tracks):
        if not self.suppress_updates:
            self.save_file("", pydaw_file_pyinput, str(a_tracks))

    def get_audio_inputs(self):
        if os.path.isfile(self.audio_inputs_file):
            with open(self.audio_inputs_file) as f_file:
                f_str = f_file.read()
            return libmk.mk_project.AudioInputTracks.from_str(f_str)
        else:
            return libmk.mk_project.AudioInputTracks()


def normalize_dialog():
    def on_ok():
        f_window.f_result = f_db_spinbox.value()
        f_window.close()

    def on_cancel():
        f_window.close()

    f_window = QtGui.QDialog(MAIN_WINDOW)
    f_window.f_result = None
    f_window.setWindowTitle(_("Normalize"))
    f_window.setFixedSize(150, 90)
    f_layout = QtGui.QVBoxLayout()
    f_window.setLayout(f_layout)
    f_hlayout = QtGui.QHBoxLayout()
    f_layout.addLayout(f_hlayout)
    f_hlayout.addWidget(QtGui.QLabel("dB"))
    f_db_spinbox = QtGui.QDoubleSpinBox()
    f_hlayout.addWidget(f_db_spinbox)
    f_db_spinbox.setRange(-18.0, 0.0)
    f_db_spinbox.setDecimals(1)
    f_db_spinbox.setValue(0.0)
    f_ok_button = QtGui.QPushButton(_("OK"))
    f_ok_cancel_layout = QtGui.QHBoxLayout()
    f_layout.addLayout(f_ok_cancel_layout)
    f_ok_cancel_layout.addWidget(f_ok_button)
    f_ok_button.pressed.connect(on_ok)
    f_cancel_button = QtGui.QPushButton(_("Cancel"))
    f_ok_cancel_layout.addWidget(f_cancel_button)
    f_cancel_button.pressed.connect(on_cancel)
    f_window.exec_()
    return f_window.f_result

class AudioInput:
    def __init__(self, a_num, a_layout, a_callback, a_count):
        self.input_num = int(a_num)
        self.callback = a_callback
        a_layout.addWidget(QtGui.QLabel(str(a_num)), a_num + 1, 21)
        self.name_lineedit = QtGui.QLineEdit(str(a_num))
        self.name_lineedit.editingFinished.connect(self.name_update)
        a_num += 1
        a_layout.addWidget(self.name_lineedit, a_num, 0)
        self.rec_checkbox = QtGui.QCheckBox("")
        self.rec_checkbox.clicked.connect(self.update_engine)
        a_layout.addWidget(self.rec_checkbox, a_num, 1)

        self.monitor_checkbox = QtGui.QCheckBox(_(""))
        self.monitor_checkbox.clicked.connect(self.update_engine)
        a_layout.addWidget(self.monitor_checkbox, a_num, 2)

        self.vol_layout = QtGui.QHBoxLayout()
        a_layout.addLayout(self.vol_layout, a_num, 3)
        self.vol_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.vol_slider.setRange(-240, 240)
        self.vol_slider.setValue(0)
        self.vol_slider.setMinimumWidth(240)
        self.vol_slider.valueChanged.connect(self.vol_changed)
        self.vol_slider.sliderReleased.connect(self.update_engine)
        self.vol_layout.addWidget(self.vol_slider)
        self.vol_label = QtGui.QLabel("0.0dB")
        self.vol_label.setMinimumWidth(64)
        self.vol_layout.addWidget(self.vol_label)
        self.stereo_combobox = QtGui.QComboBox()
        a_layout.addWidget(self.stereo_combobox, a_num, 4)
        self.stereo_combobox.setMinimumWidth(72)
        self.stereo_combobox.addItems([_("None")] +
            [str(x) for x in range(a_count + 1)])
        self.stereo_combobox.currentIndexChanged.connect(self.update_engine)
        self.suppress_updates = False

    def name_update(self, a_val=None):
        self.update_engine(a_notify=False)

    def update_engine(self, a_val=None, a_notify=True):
        if not self.suppress_updates:
            self.callback(a_notify)

    def vol_changed(self):
        f_vol = self.get_vol()
        self.vol_label.setText("{}dB".format(f_vol))
        if not self.suppress_updates:
            libmk.IPC.audio_input_volume(self.input_num, f_vol)

    def get_vol(self):
        return round(self.vol_slider.value() * 0.1, 1)

    def get_name(self):
        return str(self.name_lineedit.text())

    def get_value(self):
        f_on = 1 if self.rec_checkbox.isChecked() else 0
        f_vol = self.get_vol()
        f_monitor = 1 if self.monitor_checkbox.isChecked() else 0
        f_stereo = self.stereo_combobox.currentIndex() - 1
        return libmk.mk_project.AudioInputTrack(
            f_on, f_monitor, f_vol, 0,
            f_stereo, 0, self.name_lineedit.text())

    def set_value(self, a_val):
        self.suppress_updates = True
        f_rec = True if a_val.rec else False
        f_monitor = True if a_val.monitor else False
        self.name_lineedit.setText(a_val.name)
        self.rec_checkbox.setChecked(f_rec)
        self.monitor_checkbox.setChecked(f_monitor)
        self.vol_slider.setValue(int(a_val.vol * 10.0))
        self.stereo_combobox.setCurrentIndex(a_val.stereo + 1)
        self.suppress_updates = False


class AudioInputWidget:
    def __init__(self):
        self.widget = QtGui.QWidget()
        self.main_layout = QtGui.QVBoxLayout(self.widget)
        self.layout = QtGui.QGridLayout()
        self.main_layout.addWidget(QtGui.QLabel(_("Audio Inputs")))
        self.main_layout.addLayout(self.layout)
        f_labels = (
            _("Name"), _("Rec."), _("Mon."), _("Gain"), _("Stereo"))
        for f_i, f_label in zip(range(len(f_labels)), f_labels):
            self.layout.addWidget(QtGui.QLabel(f_label), 0, f_i)
        self.inputs = []
        f_count = 0
        if "audioInputs" in pydaw_util.global_device_val_dict:
            f_count = int(pydaw_util.global_device_val_dict["audioInputs"])
        for f_i in range(f_count):
            f_input = AudioInput(f_i, self.layout, self.callback, f_count - 1)
            self.inputs.append(f_input)

    def callback(self, a_notify):
        f_result = libmk.mk_project.AudioInputTracks()
        for f_i, f_input in zip(range(len(self.inputs)), self.inputs):
            f_result.add_track(f_i, f_input.get_value())
        PROJECT.save_audio_inputs(f_result)
        if a_notify:
            PROJECT.wn_osc.save_audio_inputs()

    def active(self):
        return [x.get_value() for x in self.inputs
            if x.rec_checkbox.isChecked()]

    def open_project(self):
        f_audio_inputs = PROJECT.get_audio_inputs()
        for k, v in f_audio_inputs.tracks.items():
            if k < len(self.inputs):
                self.inputs[k].set_value(v)


class transport_widget(libmk.AbstractTransport):
    def __init__(self):
        self.suppress_osc = True
        self.copy_path_to_clipboard = True
        self.start_region = 0
        self.last_bar = 0
        self.last_open_dir = global_home
        self.group_box = QtGui.QGroupBox()
        self.group_box.setObjectName("transport_panel")
        self.vlayout = QtGui.QVBoxLayout(self.group_box)
        self.hlayout1 = QtGui.QHBoxLayout()
        self.vlayout.addLayout(self.hlayout1)

        self.playback_menu_button = QtGui.QPushButton("")
        self.playback_menu_button.setMaximumWidth(21)
        self.playback_menu_button.setSizePolicy(
            QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.hlayout1.addWidget(self.playback_menu_button)

        self.playback_menu = QtGui.QMenu(self.playback_menu_button)
        self.playback_menu_button.setMenu(self.playback_menu)
        self.playback_widget_action = QtGui.QWidgetAction(self.playback_menu)
        self.playback_widget = QtGui.QWidget()
        self.playback_widget_action.setDefaultWidget(self.playback_widget)
        self.playback_vlayout = QtGui.QVBoxLayout(self.playback_widget)
        self.playback_menu.addAction(self.playback_widget_action)

        self.audio_inputs = AudioInputWidget()
        self.playback_vlayout.addWidget(self.audio_inputs.widget)

        self.hlayout1.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))

        self.suppress_osc = False

    def open_project(self):
        self.audio_inputs.open_project()

    def on_panic(self):
        pass
        #PROJECT.wn_osc.pydaw_panic()

    def set_time(self, f_text):
        #f_text = "{}:{}.{}".format(f_minutes, str(f_seconds).zfill(2), f_frac)
        libmk.TRANSPORT.set_time(f_text)

    def on_play(self):
        if not WAVE_EDITOR.current_file:
            return False
        WAVE_EDITOR.on_play()
        PROJECT.wn_osc.pydaw_wn_playback(1)
        return True

    def on_stop(self):
        PROJECT.wn_osc.pydaw_wn_playback(0)
        WAVE_EDITOR.on_stop()
        self.playback_menu_button.setEnabled(True)
        if libmk.IS_RECORDING:
            self.show_rec_dialog()

    def on_rec(self):
        if not self.audio_inputs.active():
            QtGui.QMessageBox.warning(
                self.group_box, _("Error"),
                _("No audio inputs are active, cannot record.  "
                "Enable one or more inputs in the transport drop-down.\n"
                "If there are no inputs in the drop-down, you will need "
                "to open the Menu->File->HardwareSettings in the \n"
                "transport and set the number of audio inputs to 1 or more"))
            return False
        PROJECT.wn_osc.pydaw_wn_playback(2)
        self.playback_menu_button.setEnabled(False)
        return True

    def show_rec_dialog(self):
        def on_ok():
            f_txt = str(f_name_lineedit.text()).strip()
            if not f_txt:
                QtGui.QMessageBox.warning(
                    MAIN_WINDOW, _("Error"), _("Name cannot be empty"))
                return
            for x in ("\\", "/", "~", "|"):
                if x in f_txt:
                    QtGui.QMessageBox.warning(
                        MAIN_WINDOW, _("Error"),
                        _("Invalid char '{}'".format(x)))
                    return
            for f_i, f_ai in zip(
            range(len(self.audio_inputs.inputs)), self.audio_inputs.inputs):
                f_val = f_ai.get_value()
                if f_val.rec:
                    f_path = os.path.join(
                        libmk.PROJECT.audio_tmp_folder, "{}.wav".format(f_i))
                    if os.path.isfile(f_path):
                        f_file_name = "-".join(
                            str(x) for x in (f_txt, f_i, f_ai.get_name()))
                        f_new_path = os.path.join(
                            libmk.PROJECT.audio_rec_folder, f_file_name)
                        if f_new_path.lower().endswith(".wav"):
                            f_new_path = f_new_path[:-4]
                        if os.path.exists(f_new_path + ".wav"):
                            for f_i in range(10000):
                                f_tmp = "{}-{}.wav".format(f_new_path, f_i)
                                if not os.path.exists(f_tmp):
                                    f_new_path = f_tmp
                                    break
                        else:
                            f_new_path += ".wav"
                        shutil.move(f_path, f_new_path)
                    else:
                        print("Error, path did not exist: {}".format(f_path))
            self.copy_path_to_clipboard = f_copy_path_checkbox.isChecked()
            if self.copy_path_to_clipboard:
                f_clipboard = libmk.APP.clipboard()
                f_clipboard.setText(libmk.PROJECT.audio_rec_folder)
            f_window.close()

        def on_cancel():
            for f_file in os.listdir(libmk.PROJECT.audio_tmp_folder):
                if f_file.endswith(".wav"):
                    f_path = os.path.join(
                        libmk.PROJECT.audio_tmp_folder, f_file)
                    os.remove(f_path)
            f_window.close()

        def dialog_close_event(a_event):
            QtGui.QDialog.closeEvent(f_window, a_event)

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.closeEvent = dialog_close_event
        f_window.setWindowTitle(_("Save Recorded Audio"))
        #f_window.setFixedSize(420, 90)
        f_layout = QtGui.QVBoxLayout()
        f_window.setLayout(f_layout)
        f_hlayout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_hlayout)
        f_hlayout.addWidget(QtGui.QLabel("Name"))
        f_name_lineedit = QtGui.QLineEdit()
        f_name_lineedit.setMinimumWidth(330)
        f_hlayout.addWidget(f_name_lineedit)
        f_copy_path_checkbox = QtGui.QRadioButton(
            _("Copy directory to clipboard?"))
        f_layout.addWidget(f_copy_path_checkbox)
        if self.copy_path_to_clipboard:
            f_copy_path_checkbox.setChecked(True)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_ok_button.pressed.connect(on_ok)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_cancel_button.pressed.connect(on_cancel)
        f_window.exec_()

    def set_tooltips(self, a_enabled):
        pass

class pydaw_audio_item(MkAudioItem):
    def clone(self):
        return pydaw_audio_item.from_arr(str(self).strip("\n").split("|"))

    @staticmethod
    def from_str(f_str):
        return pydaw_audio_item.from_arr(f_str.split("|"))

    @staticmethod
    def from_arr(a_arr):
        f_result = pydaw_audio_item(*a_arr)
        return f_result

class pydaw_main_window(QtGui.QScrollArea):
    def __init__(self):
        QtGui.QScrollArea.__init__(self)
        self.first_offline_render = True
        self.last_offline_dir = global_home
        self.copy_to_clipboard_checked = True

        self.setObjectName("plugin_ui")
        self.widget = QtGui.QWidget()
        self.widget.setObjectName("plugin_ui")
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.setMargin(2)
        self.widget.setLayout(self.main_layout)

        #The tabs
        self.main_tabwidget = QtGui.QTabWidget()
        self.main_layout.addWidget(self.main_tabwidget)

        self.main_tabwidget.addTab(WAVE_EDITOR.widget, _("Wave Editor"))

        self.notes_tab = QtGui.QTextEdit(self)
        self.notes_tab.setAcceptRichText(False)
        self.notes_tab.leaveEvent = self.on_edit_notes
        self.main_tabwidget.addTab(self.notes_tab, _("Project Notes"))

    def on_offline_render(self, a_val=None):
        WAVE_EDITOR.on_export()

    def on_edit_notes(self, a_event=None):
        QtGui.QTextEdit.leaveEvent(self.notes_tab, a_event)
        PROJECT.write_notes(self.notes_tab.toPlainText())

    def configure_callback(self, path, arr):
        f_pc_dict = {}
        f_ui_dict = {}
        f_cc_dict = {}
        for f_line in arr[0].split("\n"):
            if f_line == "":
                break
            a_key, a_val = f_line.split("|", 1)
            if a_key == "pc":
                f_plugin_uid, f_port, f_val = a_val.split("|")
                f_pc_dict[(f_plugin_uid, f_port)] = f_val
            elif a_key == "cur":
                if libmk.IS_PLAYING:
                    f_region, f_bar, f_beat = a_val.split("|")
                    TRANSPORT.set_pos_from_cursor(f_region, f_bar, f_beat)
                    for f_editor in (AUDIO_SEQ, REGION_EDITOR):
                        f_editor.set_playback_pos(f_bar, f_beat)
            elif a_key == "peak":
                global_update_peak_meters(a_val)
            elif a_key == "cc":
                f_track_num, f_cc, f_val = a_val.split("|")
                f_cc_dict[(f_track_num, f_cc)] = f_val
            elif a_key == "ui":
                f_plugin_uid, f_name, f_val = a_val.split("|", 2)
                f_ui_dict[(f_plugin_uid, f_name)] = f_val
            elif a_key == "mrec":
                MREC_EVENTS.append(a_val)
            elif a_key == "ne":
                f_state, f_note = a_val.split("|")
                PIANO_ROLL_EDITOR.highlight_keys(f_state, f_note)
            elif a_key == "ml":
                libmk.PLUGIN_UI_DICT.midi_learn_control[0].update_cc_map(
                    a_val, libmk.PLUGIN_UI_DICT.midi_learn_control[1])
            elif a_key == "wec":
                if libmk.IS_PLAYING:
                    WAVE_EDITOR.set_playback_cursor(float(a_val))
            elif a_key == "ready":
                pass
        #This prevents multiple events from moving the same control,
        #only the last goes through
        for k, f_val in f_ui_dict.items():
            f_plugin_uid, f_name = k
            if int(f_plugin_uid) in libmk.PLUGIN_UI_DICT:
                libmk.PLUGIN_UI_DICT[int(f_plugin_uid)].ui_message(
                    f_name, f_val)
        for k, f_val in f_pc_dict.items():
            f_plugin_uid, f_port = (int(x) for x in k)
            if f_plugin_uid in libmk.PLUGIN_UI_DICT:
                libmk.PLUGIN_UI_DICT[f_plugin_uid].set_control_val(
                    f_port, float(f_val))
        for k, f_val in f_cc_dict.items():
            f_track_num, f_cc = (int(x) for x in k)
            for f_plugin_uid in \
            TRACK_PANEL.tracks[f_track_num].get_plugin_uids():
                if f_plugin_uid in libmk.PLUGIN_UI_DICT:
                    libmk.PLUGIN_UI_DICT[f_plugin_uid].set_cc_val(f_cc, f_val)

    def prepare_to_quit(self):
        WAVE_EDITOR.sample_graph.scene.clear()

def global_update_peak_meters(a_val):
    for f_val in a_val.split("|"):
        f_list = f_val.split(":")
        f_index = int(f_list[0])
        if f_index in ALL_PEAK_METERS:
            for f_pkm in ALL_PEAK_METERS[f_index]:
                f_pkm.set_value(f_list[1:])
        else:
            print("{} not in ALL_PEAK_METERS".format(f_index))


class pydaw_wave_editor_widget:
    def __init__(self):
        self.widget = QtGui.QWidget()
        self.layout = QtGui.QVBoxLayout(self.widget)
        self.right_widget = QtGui.QWidget()
        self.vlayout = QtGui.QVBoxLayout(self.right_widget)
        self.file_browser = pydaw_widgets.pydaw_file_browser_widget()
        self.file_browser.load_button.pressed.connect(self.on_file_open)
        self.file_browser.list_file.itemDoubleClicked.connect(
            self.on_file_open)
        self.file_browser.preview_button.pressed.connect(self.on_preview)
        self.file_browser.stop_preview_button.pressed.connect(
            self.on_stop_preview)
        self.file_browser.list_file.setSelectionMode(
            QtGui.QListWidget.SingleSelection)
        self.layout.addWidget(self.file_browser.hsplitter)
        self.file_browser.hsplitter.addWidget(self.right_widget)
        self.file_hlayout = QtGui.QHBoxLayout()

        self.menu = QtGui.QMenu(self.widget)
        self.menu_button = QtGui.QPushButton(_("Menu"))
        self.menu_button.setMenu(self.menu)
        self.file_hlayout.addWidget(self.menu_button)
        self.export_action = self.menu.addAction(_("Export..."))
        self.export_action.triggered.connect(self.on_export)
        self.menu.addSeparator()
        self.copy_action = self.menu.addAction(_("Copy File to Clipboard"))
        self.copy_action.triggered.connect(self.copy_file_to_clipboard)
        self.copy_action.setShortcut(QtGui.QKeySequence.Copy)
#        self.copy_item_action = self.menu.addAction(_("Copy as Audio Item"))
#        self.copy_item_action.triggered.connect(self.copy_audio_item)
#        self.copy_item_action.setShortcut(
#            QtGui.QKeySequence.fromString("ALT+C"))
        self.paste_action = self.menu.addAction(
            _("Paste File from Clipboard"))
        self.paste_action.triggered.connect(self.open_file_from_clipboard)
        self.paste_action.setShortcut(QtGui.QKeySequence.Paste)
        self.open_folder_action = self.menu.addAction(
            _("Open parent folder in browser"))
        self.open_folder_action.triggered.connect(self.open_item_folder)
        self.menu.addSeparator()
        self.bookmark_action = self.menu.addAction(_("Bookmark File"))
        self.bookmark_action.triggered.connect(self.bookmark_file)
        self.bookmark_action.setShortcut(
            QtGui.QKeySequence.fromString("CTRL+D"))
        self.delete_bookmark_action = self.menu.addAction(
            _("Delete Bookmark"))
        self.delete_bookmark_action.triggered.connect(self.delete_bookmark)
        self.delete_bookmark_action.setShortcut(
            QtGui.QKeySequence.fromString("ALT+D"))
        self.menu.addSeparator()
        self.reset_markers_action = self.menu.addAction(
            _("Reset Markers"))
        self.reset_markers_action.triggered.connect(self.reset_markers)
        self.normalize_action = self.menu.addAction(
            _("Normalize (non-destructive)..."))
        self.normalize_action.triggered.connect(self.normalize_dialog)
        self.stretch_shift_action = self.menu.addAction(
            _("Time-Stretch/Pitch-Shift..."))
        self.stretch_shift_action.triggered.connect(self.stretch_shift_dialog)

        self.bookmark_button = QtGui.QPushButton(_("Bookmarks"))
        self.file_hlayout.addWidget(self.bookmark_button)

        self.history_button = QtGui.QPushButton(_("History"))
        self.file_hlayout.addWidget(self.history_button)

        self.fx_button = QtGui.QPushButton(_("Effects"))
        self.file_hlayout.addWidget(self.fx_button)

        ###############################

        self.fx_menu = QtGui.QMenu()
        self.fx_menu.aboutToShow.connect(self.open_plugins)
        self.fx_button.setMenu(self.fx_menu)
        self.track_number = 0
        self.plugins = []
        self.menu_widget = QtGui.QWidget()
        self.menu_hlayout = QtGui.QHBoxLayout(self.menu_widget)
        self.menu_gridlayout = QtGui.QGridLayout()
        self.menu_hlayout.addLayout(self.menu_gridlayout)
        self.menu_gridlayout.addWidget(QtGui.QLabel(_("Plugins")), 0, 0)
        self.menu_gridlayout.addWidget(QtGui.QLabel(_("P")), 0, 3)
        for f_i in range(10):
            f_plugin = plugin_settings_wave_editor(
                PROJECT.wn_osc.pydaw_set_plugin,
                f_i, self.track_number, self.menu_gridlayout,
                self.save_callback, self.name_callback, None)
            self.plugins.append(f_plugin)
        self.action_widget = QtGui.QWidgetAction(self.fx_menu)
        self.action_widget.setDefaultWidget(self.menu_widget)
        self.fx_menu.addAction(self.action_widget)

        ###############################

        self.menu_info = QtGui.QMenu()
        self.menu_info_button = QtGui.QPushButton(_("Info"))
        self.menu_info_button.setMenu(self.menu_info)
        self.file_hlayout.addWidget(self.menu_info_button)

        self.file_lineedit = QtGui.QLineEdit()
        self.file_lineedit.setReadOnly(True)
        self.file_hlayout.addWidget(self.file_lineedit)
        self.vlayout.addLayout(self.file_hlayout)
        self.edit_tab = QtGui.QWidget()
        self.file_browser.folders_tab_widget.addTab(self.edit_tab, _("Edit"))
        self.edit_hlayout = QtGui.QHBoxLayout(self.edit_tab)
        self.vol_layout = QtGui.QVBoxLayout()
        self.edit_hlayout.addLayout(self.vol_layout)
        self.vol_slider = QtGui.QSlider(QtCore.Qt.Vertical)
        self.vol_slider.setRange(-240, 120)
        self.vol_slider.setValue(0)
        self.vol_slider.valueChanged.connect(self.vol_changed)
        self.vol_layout.addWidget(self.vol_slider)
        self.vol_label = QtGui.QLabel("0.0db")
        self.vol_label.setMinimumWidth(75)
        self.vol_layout.addWidget(self.vol_label)
        self.peak_meter = pydaw_widgets.peak_meter(28, a_text=True)
        ALL_PEAK_METERS[0] = [self.peak_meter]
        self.edit_hlayout.addWidget(self.peak_meter.widget)
        self.ctrl_vlayout = QtGui.QVBoxLayout()
        self.edit_hlayout.addLayout(self.ctrl_vlayout)
        self.fade_in_start = QtGui.QSpinBox()
        self.fade_in_start.setRange(-50, -6)
        self.fade_in_start.setValue(-24)
        self.fade_in_start.valueChanged.connect(self.marker_callback)
        self.ctrl_vlayout.addWidget(QtGui.QLabel(_("Fade-In")))
        self.ctrl_vlayout.addWidget(self.fade_in_start)
        self.fade_out_end = QtGui.QSpinBox()
        self.fade_out_end.setRange(-50, -6)
        self.fade_out_end.setValue(-24)
        self.fade_out_end.valueChanged.connect(self.marker_callback)
        self.ctrl_vlayout.addWidget(QtGui.QLabel(_("Fade-Out")))
        self.ctrl_vlayout.addWidget(self.fade_out_end)
        self.ctrl_vlayout.addItem(
            QtGui.QSpacerItem(1, 1, vPolicy=QtGui.QSizePolicy.Expanding))
        self.edit_hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        self.sample_graph = pydaw_audio_item_viewer_widget(
            self.marker_callback, self.marker_callback,
            self.marker_callback, self.marker_callback)
        self.vlayout.addWidget(self.sample_graph)

        self.label_action = QtGui.QWidgetAction(self.menu_button)
        self.label_action.setDefaultWidget(self.sample_graph.label)
        self.menu_info.addAction(self.label_action)
        self.sample_graph.label.setFixedSize(210, 123)

        self.orig_pos = 0
        self.duration = None
        self.sixty_recip = 1.0 / 60.0
        self.playback_cursor = None
        self.time_label_enabled = False
        self.file_browser.hsplitter.setSizes([420, 9999])
        self.copy_to_clipboard_checked = True
        self.last_offline_dir = global_home
        self.open_exported = False
        self.history = []
        self.graph_object = None
        self.current_file = None
        self.callbacks_enabled = True

        self.controls_to_disable = (
            self.file_browser.load_button, self.file_browser.preview_button,
            self.file_browser.stop_preview_button, self.history_button,
            self.sample_graph, self.vol_slider, self.bookmark_button,
            self.fade_in_start, self.fade_out_end)

    def save_callback(self):
        f_result = libmk.pydaw_track_plugins()
        f_result.plugins = [x.get_value() for x in self.plugins]
        PROJECT.save_track_plugins(self.track_number, f_result)

    def open_plugins(self):
        f_plugins = PROJECT.get_track_plugins(self.track_number)
        if f_plugins:
            for f_plugin in f_plugins.plugins:
                self.plugins[f_plugin.index].set_value(f_plugin)

    def name_callback(self):
        return "Wave-Next"

    def copy_audio_item(self):
        pass
#        if self.graph_object is None:
#            return
#        f_uid = libmk.PROJECT.get_wav_uid_by_name(self.current_file)
#        f_item = self.get_audio_item(f_uid)
#        raise NotImplementedError

    def bookmark_file(self):
        if self.graph_object is None:
            return
        f_list = self.get_bookmark_list()
        if self.current_file not in f_list:
            f_list.append(self.current_file)
            PROJECT.set_we_bm(f_list)
            self.open_project()

    def get_bookmark_list(self):
        f_list = PROJECT.get_we_bm()
        f_resave = False
        for f_item in f_list[:]:
            if not os.path.isfile(f_item):
                f_resave = True
                f_list.remove(f_item)
                print("os.path.isfile({}) returned False, removing "
                    "from bookmarks".format(f_item))
        if f_resave:
            PROJECT.set_we_bm(f_list)
        return sorted(f_list)

    def open_project(self):
        f_list = self.get_bookmark_list()
        if f_list:
            f_menu = QtGui.QMenu(self.widget)
            f_menu.triggered.connect(self.open_file_from_action)
            self.bookmark_button.setMenu(f_menu)
            for f_item in f_list:
                f_menu.addAction(f_item)
        else:
            self.bookmark_button.setMenu(None)

    def delete_bookmark(self):
        if self.graph_object is None:
            return
        f_list = PROJECT.get_we_bm()
        if self.current_file in f_list:
            f_list.remove(self.current_file)
            PROJECT.set_we_bm(f_list)
            self.open_project()

    def open_item_folder(self):
        f_path = str(self.file_lineedit.text())
        self.file_browser.open_file_in_browser(f_path)

    def normalize_dialog(self):
        if self.graph_object is None or libmk.IS_PLAYING:
            return
        f_val = normalize_dialog()
        if f_val is not None:
            self.normalize(f_val)

    def normalize(self, a_value):
        f_val = self.graph_object.normalize(a_value)
        self.vol_slider.setValue(int(f_val * 10.0))

    def reset_markers(self):
        if libmk.IS_PLAYING:
            return
        self.sample_graph.reset_markers()

    def set_tooltips(self, a_on):
        if a_on:
            self.sample_graph.setToolTip(
                _("Load samples here by using the browser on the left "
                "and clicking the  'Load' button"))
            self.fx_button.setToolTip(
                _("This button shows the Modulex effects window.  "
                "Export the audio (using the menu button) to "
                "permanently apply effects."))
            self.menu_button.setToolTip(
                _("This menu can export the audio or perform "
                "various operations."))
            self.history_button.setToolTip(
                _("Use this button to view or open files that "
                "were previously opened during this session."))
        else:
            self.sample_graph.setToolTip("")
            self.fx_button.setToolTip("")
            self.menu_button.setToolTip("")
            self.history_button.setToolTip("")

    def stretch_shift_dialog(self):
        f_path = self.current_file
        if f_path is None or libmk.IS_PLAYING:
            return

        f_base_file_name = f_path.rsplit("/", 1)[1]
        f_base_file_name = f_base_file_name.rsplit(".", 1)[0]
        print(f_base_file_name)

        def on_ok(a_val=None):
            f_stretch = f_timestretch_amt.value()
            f_crispness = f_crispness_combobox.currentIndex()
            f_preserve_formants = f_preserve_formants_checkbox.isChecked()
            f_algo = f_algo_combobox.currentIndex()
            f_pitch = f_pitch_shift.value()

            f_file = QtGui.QFileDialog.getSaveFileName(
                self.widget, "Save file as...", self.last_offline_dir,
                filter="Wav File (*.wav)")
            if f_file is None:
                return
            f_file = str(f_file)
            if f_file == "":
                return
            if not f_file.endswith(".wav"):
                f_file += ".wav"
            self.last_offline_dir = os.path.dirname(f_file)

            if f_algo == 0:
                f_proc = pydaw_util.pydaw_rubberband(
                    f_path, f_file, f_stretch, f_pitch, f_crispness,
                    f_preserve_formants)
            elif f_algo == 1:
                f_proc = pydaw_util.pydaw_sbsms(
                    f_path, f_file, f_stretch, f_pitch)

            f_proc.wait()
            self.open_file(f_file)
            f_window.close()

        def on_cancel(a_val=None):
            f_window.close()

        f_window = QtGui.QDialog(self.widget)
        f_window.setMinimumWidth(390)
        f_window.setWindowTitle(_("Time-Stretch/Pitch-Shift Sample"))
        f_layout = QtGui.QVBoxLayout()
        f_window.setLayout(f_layout)

        f_time_gridlayout = QtGui.QGridLayout()
        f_layout.addLayout(f_time_gridlayout)

        f_time_gridlayout.addWidget(QtGui.QLabel(_("Pitch(semitones):")), 0, 0)
        f_pitch_shift = QtGui.QDoubleSpinBox()
        f_pitch_shift.setRange(-36, 36)
        f_pitch_shift.setValue(0.0)
        f_pitch_shift.setDecimals(6)
        f_time_gridlayout.addWidget(f_pitch_shift, 0, 1)

        f_time_gridlayout.addWidget(QtGui.QLabel(_("Stretch:")), 3, 0)
        f_timestretch_amt = QtGui.QDoubleSpinBox()
        f_timestretch_amt.setRange(0.2, 4.0)
        f_timestretch_amt.setDecimals(6)
        f_timestretch_amt.setSingleStep(0.1)
        f_timestretch_amt.setValue(1.0)
        f_time_gridlayout.addWidget(f_timestretch_amt, 3, 1)
        f_time_gridlayout.addWidget(QtGui.QLabel(_("Algorithm:")), 6, 0)
        f_algo_combobox = QtGui.QComboBox()
        f_algo_combobox.addItems(["Rubberband", "SBSMS"])
        f_time_gridlayout.addWidget(f_algo_combobox, 6, 1)

        f_groupbox = QtGui.QGroupBox(_("Rubberband Options"))
        f_layout.addWidget(f_groupbox)
        f_groupbox_layout = QtGui.QGridLayout(f_groupbox)
        f_groupbox_layout.addWidget(QtGui.QLabel(_("Crispness")), 12, 0)
        f_crispness_combobox = QtGui.QComboBox()
        f_crispness_combobox.addItems(CRISPNESS_SETTINGS)
        f_crispness_combobox.setCurrentIndex(5)
        f_groupbox_layout.addWidget(f_crispness_combobox, 12, 1)
        f_preserve_formants_checkbox = QtGui.QCheckBox("Preserve formants?")
        f_preserve_formants_checkbox.setChecked(True)
        f_groupbox_layout.addWidget(f_preserve_formants_checkbox, 18, 1)

        f_hlayout2 = QtGui.QHBoxLayout()
        f_layout.addLayout(f_hlayout2)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_button.pressed.connect(on_ok)
        f_hlayout2.addWidget(f_ok_button)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(on_cancel)
        f_hlayout2.addWidget(f_cancel_button)

        f_window.exec_()

    def open_file_from_action(self, a_action):
        self.open_file(str(a_action.text()))

    def on_export(self):
        if not self.history or libmk.IS_PLAYING:
            return

        def ok_handler():
            if str(f_name.text()) == "":
                QtGui.QMessageBox.warning(
                    f_window, _("Error"), _("Name cannot be empty"))
                return

            if f_copy_to_clipboard_checkbox.isChecked():
                self.copy_to_clipboard_checked = True
                f_clipboard = QtGui.QApplication.clipboard()
                f_clipboard.setText(f_name.text())
            else:
                self.copy_to_clipboard_checked = False

            f_file_name = str(f_name.text())
            PROJECT.wn_osc.pydaw_we_export(f_file_name)
            self.last_offline_dir = os.path.dirname(f_file_name)
            self.open_exported = f_open_exported.isChecked()
            f_window.close()
            libmk.MAIN_WINDOW.show_offline_rendering_wait_window(f_file_name)
            if self.open_exported:
                self.open_file(f_file_name)


        def cancel_handler():
            f_window.close()

        def file_name_select():
            try:
                if not os.path.isdir(self.last_offline_dir):
                    self.last_offline_dir = global_home
                f_file_name = str(QtGui.QFileDialog.getSaveFileName(
                    f_window, _("Select a file name to save to..."),
                    self.last_offline_dir))
                if not f_file_name is None and f_file_name != "":
                    if not f_file_name.endswith(".wav"):
                        f_file_name += ".wav"
                    if not f_file_name is None and not str(f_file_name) == "":
                        f_name.setText(f_file_name)
                    self.last_offline_dir = os.path.dirname(f_file_name)
            except Exception as ex:
                libmk.pydaw_print_generic_exception(ex)

        def on_overwrite(a_val=None):
            f_name.setText(self.file_lineedit.text())

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Offline Render"))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)

        f_name = QtGui.QLineEdit()
        f_name.setReadOnly(True)
        f_name.setMinimumWidth(360)
        f_layout.addWidget(QtGui.QLabel(_("File Name:")), 0, 0)
        f_layout.addWidget(f_name, 0, 1)
        f_select_file = QtGui.QPushButton(_("Select"))
        f_select_file.pressed.connect(file_name_select)
        f_layout.addWidget(f_select_file, 0, 2)

        f_overwrite_button = QtGui.QPushButton("Overwrite\nFile")
        f_layout.addWidget(f_overwrite_button, 3, 0)
        f_overwrite_button.pressed.connect(on_overwrite)

        f_layout.addWidget(QtGui.QLabel(
            libpydaw.strings.export_format), 3, 1)
        f_copy_to_clipboard_checkbox = QtGui.QCheckBox(
        _("Copy export path to clipboard? (useful for right-click pasting "
        "back into the audio sequencer)"))
        f_copy_to_clipboard_checkbox.setChecked(self.copy_to_clipboard_checked)
        f_layout.addWidget(f_copy_to_clipboard_checkbox, 4, 1)
        f_open_exported = QtGui.QCheckBox("Open exported item?")
        f_open_exported.setChecked(self.open_exported)
        f_layout.addWidget(f_open_exported, 6, 1)
        f_ok_layout = QtGui.QHBoxLayout()
        f_ok_layout.addItem(
            QtGui.QSpacerItem(10, 10,
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        f_ok = QtGui.QPushButton(_("OK"))
        f_ok.pressed.connect(ok_handler)
        f_ok_layout.addWidget(f_ok)
        f_layout.addLayout(f_ok_layout, 9, 1)
        f_cancel = QtGui.QPushButton(_("Cancel"))
        f_cancel.pressed.connect(cancel_handler)
        f_layout.addWidget(f_cancel, 9, 2)
        f_window.exec_()


    def on_reload(self):
        pass

    def vol_changed(self, a_val=None):
        f_result = round(self.vol_slider.value()  * 0.1, 1)
        self.marker_callback()
        self.vol_label.setText("{}dB".format(f_result))

    def on_preview(self):
        f_list = self.file_browser.files_selected()
        if f_list:
            libmk.IPC.pydaw_preview_audio(f_list[0])

    def on_stop_preview(self):
        libmk.IPC.pydaw_stop_preview()

    def on_file_open(self):
        if libmk.IS_PLAYING:
            return
        f_file = self.file_browser.files_selected()
        if not f_file:
            return
        f_file_str = f_file[0]
        self.open_file(f_file_str)

    def copy_file_to_clipboard(self):
        f_clipboard = QtGui.QApplication.clipboard()
        f_clipboard.setText(str(self.file_lineedit.text()))

    def open_file_from_clipboard(self):
        if libmk.IS_PLAYING:
            return
        f_clipboard = QtGui.QApplication.clipboard()
        f_text = str(f_clipboard.text()).strip()
        if len(f_text) < 1000 and os.path.isfile(f_text):
            self.open_file(f_text)
        else:
            QtGui.QMessageBox.warning(
                self.widget, _("Error"),
                _("No file path in the clipboard"))

    def open_file(self, a_file):
        f_file = str(a_file)
        if not os.path.exists(f_file):
            QtGui.QMessageBox.warning(
                self.widget, _("Error"),
                _("{} does not exist".format(f_file)))
            return
        self.clear_sample_graph()
        self.current_file = f_file
        self.file_lineedit.setText(f_file)
        self.set_sample_graph(f_file)
        self.duration = float(self.graph_object.frame_count) / float(
            self.graph_object.sample_rate)
        if f_file in self.history:
            self.history.remove(f_file)
        self.history.append(f_file)
        f_menu = QtGui.QMenu(self.history_button)
        f_menu.triggered.connect(self.open_file_from_action)
        for f_path in reversed(self.history):
            f_menu.addAction(f_path)
        self.history_button.setMenu(f_menu)
        PROJECT.wn_osc.pydaw_ab_open(a_file)
        self.marker_callback()

    def get_audio_item(self, a_uid=0):
        f_start = self.sample_graph.start_marker.value
        f_end = self.sample_graph.end_marker.value
        f_diff = f_end - f_start
        f_diff = pydaw_clip_value(f_diff, 0.1, 1000.0)
        f_fade_in = ((self.sample_graph.fade_in_marker.value - f_start) /
            f_diff) * 1000.0
        f_fade_out = 1000.0 - (((f_end -
            self.sample_graph.fade_out_marker.value) / f_diff) * 1000.0)

        return pydaw_audio_item(
            a_uid, a_sample_start=f_start, a_sample_end=f_end,
            a_vol=self.vol_slider.value() * 0.1,
            a_fade_in=f_fade_in, a_fade_out=f_fade_out,
            a_fadein_vol=self.fade_in_start.value(),
            a_fadeout_vol=self.fade_out_end.value())

    def set_audio_item(self, a_item):
        self.callbacks_enabled = False
        self.sample_graph.start_marker.set_value(a_item.sample_start)
        self.sample_graph.end_marker.set_value(a_item.sample_end)
        f_start = self.sample_graph.start_marker.value
        f_end = self.sample_graph.end_marker.value
        f_diff = f_end - f_start
        f_diff = pydaw_clip_value(f_diff, 0.1, 1000.0)
        f_fade_in = (f_diff * (a_item.fade_in / 1000.0)) + f_start
        f_fade_out = (f_diff * (a_item.fade_out / 1000.0)) + f_start
        self.sample_graph.fade_in_marker.set_value(f_fade_in)
        self.sample_graph.fade_out_marker.set_value(f_fade_out)
        self.vol_slider.setValue(int(a_item.vol * 10.0))
        self.fade_in_start.setValue(a_item.fadein_vol)
        self.fade_out_end.setValue(a_item.fadeout_vol)
        self.callbacks_enabled = True
        self.marker_callback()

    def marker_callback(self, a_val=None):
        if self.callbacks_enabled:
            f_item = self.get_audio_item()
            PROJECT.wn_osc.pydaw_we_set(
                "0|{}".format(f_item))
            f_start = self.sample_graph.start_marker.value
            self.set_time_label(f_start * 0.001, True)

    def set_playback_cursor(self, a_pos):
        if self.playback_cursor is not None:
            self.playback_cursor.setPos(
                a_pos * pydaw_widgets.AUDIO_ITEM_SCENE_WIDTH, 0.0)
        self.set_time_label(a_pos)

    def set_time_label(self, a_value, a_override=False):
        if self.history and (a_override or self.time_label_enabled):
            f_seconds = self.duration * a_value
            f_minutes = int(f_seconds * self.sixty_recip)
            f_seconds %= 60.0
            f_tenths = round(f_seconds - float(int(f_seconds)), 1)
            f_seconds = str(int(f_seconds)).zfill(2)
            libmk.TRANSPORT.set_time("{}:{}.{}".format(
                f_minutes, f_seconds, str(f_tenths)[2]))

    def on_play(self):
        for f_control in self.controls_to_disable:
            f_control.setEnabled(False)
        self.time_label_enabled = True
        self.playback_cursor = self.sample_graph.scene.addLine(
            self.sample_graph.start_marker.line.line(),
            self.sample_graph.start_marker.line.pen())

    def on_stop(self):
        for f_control in self.controls_to_disable:
            f_control.setEnabled(True)
        if self.playback_cursor is not None:
            #self.sample_graph.scene.removeItem(self.playback_cursor)
            self.playback_cursor = None
        self.time_label_enabled = False
        if self.history:
            self.set_time_label(
                self.sample_graph.start_marker.value * 0.001, True)
        if self.graph_object is not None:
            self.sample_graph.redraw_item(
                self.sample_graph.start_marker.value,
                self.sample_graph.end_marker.value,
                self.sample_graph.fade_in_marker.value,
                self.sample_graph.fade_out_marker.value)

    def set_sample_graph(self, a_file_name):
        libmk.PROJECT.delete_sample_graph_by_name(a_file_name)
        self.graph_object = libmk.PROJECT.get_sample_graph_by_name(
            a_file_name, a_cp=False)
        self.sample_graph.draw_item(
            self.graph_object, 0.0, 1000.0, 0.0, 1000.0)

    def clear_sample_graph(self):
        self.sample_graph.clear_drawn_items()

    def clear(self):
        self.clear_sample_graph()
        self.file_lineedit.setText("")


def global_close_all():
    global OPEN_ITEM_UIDS, AUDIO_ITEMS_TO_DROP
    WAVE_EDITOR.clear()

#Opens or creates a new project
def global_open_project(a_project_file):
    global PROJECT, TRACK_NAMES
    PROJECT = WaveNextProject(global_pydaw_with_audio)
    PROJECT.suppress_updates = True
    PROJECT.open_project(a_project_file, False)
    WAVE_EDITOR.last_offline_dir = libmk.PROJECT.user_folder
    PROJECT.suppress_updates = False
    MAIN_WINDOW.last_offline_dir = libmk.PROJECT.user_folder
    MAIN_WINDOW.notes_tab.setText(PROJECT.get_notes())
    WAVE_EDITOR.open_project()
    TRANSPORT.open_project()


def global_new_project(a_project_file):
    global PROJECT
    PROJECT = WaveNextProject(global_pydaw_with_audio)
    PROJECT.new_project(a_project_file)
    WAVE_EDITOR.last_offline_dir = libmk.PROJECT.user_folder
    MAIN_WINDOW.last_offline_dir = libmk.PROJECT.user_folder
    MAIN_WINDOW.notes_tab.setText("")
    WAVE_EDITOR.open_project()


PROJECT = WaveNextProject(True)

ALL_PEAK_METERS = {}

WAVE_EDITOR = pydaw_wave_editor_widget()
TRANSPORT = transport_widget()
MAIN_WINDOW = pydaw_main_window()

if libmk.TOOLTIPS_ENABLED:
    set_tooltips_enabled(libmk.TOOLTIPS_ENABLED)

CLOSE_ENGINE_ON_RENDER = False
