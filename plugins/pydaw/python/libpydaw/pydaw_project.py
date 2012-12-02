# -*- coding: utf-8 -*-
"""
A class that contains methods and data for a PyDAW project.
"""

import os
from shutil import copyfile, move
from time import sleep

#from lms_session import lms_session #deprecated
from dssi_gui import dssi_gui
from pydaw_git import pydaw_git_repo
pydaw_terminating_char = "\\"

pydaw_bad_chars = ["|", "\\", "~", "."]

def pydaw_remove_bad_chars(a_str):
    """ Remove any characters that have special meaning to PyDAW """
    f_str = str(a_str)
    for f_char in pydaw_bad_chars:
        f_str = f_str.replace(f_char, "")
    f_str = f_str.replace(' ', '_')
    return f_str

beat_fracs = ['1/16', '1/8', '1/4', '1/3', '1/2', '1/1']

def beat_frac_text_to_float(f_index):
    if f_index == 0:
        return 0.0625
    elif f_index == 1:
        return 0.125
    elif f_index == 2:
        return 0.25
    elif f_index == 3:
        return 0.33333333
    elif f_index == 4:
        return 0.5
    elif f_index == 5:
        return 1.0
    else:
        return 0.25

int_to_note_array = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def note_num_to_string(a_note_num):    
    f_note = int(a_note_num) % 12
    f_octave = (int(a_note_num) / 12) - 2
    return int_to_note_array[f_note] + str(f_octave)

def bool_to_int(a_bool):
    """ For sending OSC messages """
    if a_bool:
        return "1"
    else:
        return "0"


def time_quantize_round(a_input):
    """Properly quantize time values from QDoubleSpinBoxes that measure beats"""
    if round(a_input) == round(a_input, 2):
        return round(a_input)
    else:
        return round(a_input, 4)

class pydaw_project:
    def save_project(self):
        self.this_dssi_gui.pydaw_save_tracks()
        sleep(3)
        self.git_repo.git_add(self.instrument_folder + "/*")
        self.git_repo.git_commit("-a", "Saved plugin state")
    
    def record_stop_git_commit(self):
        """ This should be called once recording has stopped to catch-up Git """
        self.git_repo.git_add(self.regions_folder + "/*")
        self.git_repo.git_add(self.items_folder + "/*")
        self.git_repo.git_commit("-a", "Save recorded items/regions")
        
    def save_project_as(self, a_file_name):
        f_file_name = str(a_file_name)
        print("Saving project as " + f_file_name + " ...")
        f_new_project_folder = os.path.dirname(f_file_name)
        f_cmd = "cp -r " + self.project_folder + "/* " + f_new_project_folder + "/"
        os.popen(f_cmd)
        print(f_new_project_folder + "/" + self.project_file + " | " + a_file_name)
        move(f_new_project_folder + "/" + self.project_file + ".pydaw", a_file_name)
        self.set_project_folders(f_file_name)
        self.this_dssi_gui.pydaw_open_song(self.project_folder)
        self.git_repo.repo_dir = self.project_folder

    def set_project_folders(self, a_project_file):
        self.project_folder = os.path.dirname(a_project_file)
        self.project_file = os.path.splitext(os.path.basename(a_project_file))[0]
        self.instrument_folder = self.project_folder + "/instruments"
        self.regions_folder = self.project_folder + "/regions"
        self.items_folder = self.project_folder + "/items"

    def open_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)
        if not os.path.exists(a_project_file):
            print("project file " + a_project_file + " does not exist, creating as new project")
            self.new_project(a_project_file)
        else:
            self.git_repo = pydaw_git_repo(self.project_folder)
        if a_notify_osc:
            self.this_dssi_gui.pydaw_open_song(self.project_folder)
        
    def new_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)

        project_folders = [
            self.project_folder,
            self.instrument_folder,
            self.regions_folder,
            self.items_folder
            ]

        for project_dir in project_folders:
            if not os.path.isdir(project_dir):
                os.makedirs(project_dir)
        if not os.path.exists(a_project_file):
            f_file = open(a_project_file, 'w')
            f_file.write("This file does is not supposed to contain any data, it is only a placeholder for saving and opening the project :)")
            f_file.close()
            
        f_pysong_file = self.project_folder + "/default.pysong"
        if not os.path.exists(f_pysong_file):
            f_file = open(f_pysong_file, 'w')
            f_file.write(pydaw_terminating_char)
            f_file.close()
        f_pytransport_file = self.project_folder + "/default.pytransport"
        if not os.path.exists(f_pytransport_file):
            f_file = open(f_pytransport_file, 'w')
            f_file.write("140|None|0|0|0\n\\")
            f_file.close()        
        f_pytracks_file = self.project_folder + "/default.pytracks"
        if not os.path.exists(f_pytracks_file):
            f_file = open(f_pytracks_file, 'w')
            for i in range(16):
                f_file.write(str(i) + "|0|0|0|0|track" + str(i + 1) + "|0\n")
            f_file.write(pydaw_terminating_char)
            f_file.close()
        self.git_repo = pydaw_git_repo(self.project_folder)
        self.git_repo.git_init()
        self.git_repo.git_add(f_pysong_file)
        self.git_repo.git_add(f_pytracks_file)
        self.git_repo.git_add(f_pytransport_file)
        self.git_repo.git_add(a_project_file)
        self.git_repo.git_commit("-a", "Created new project")
        if a_notify_osc:
            self.this_dssi_gui.pydaw_open_song(self.project_folder)

    def get_song_string(self):
        try:
            f_file = open(self.project_folder + "/default.pysong", "r")
        except:
            return pydaw_terminating_char
        f_result = f_file.read()
        f_file.close()
        return f_result

    def get_song(self):
        return pydaw_song.from_str(self.get_song_string())

    def get_region_string(self, a_region_name):
        try:
            f_file = open(self.regions_folder + "/" + a_region_name + ".pyreg", "r")
        except:
            return ""
        f_result = f_file.read()
        f_file.close()
        return f_result

    def get_region(self, a_region_name):
        return pydaw_region.from_str(a_region_name, self.get_region_string(a_region_name))

    def get_item_string(self, a_item_name):
        try:
            f_file = open(self.items_folder + "/" + a_item_name + ".pyitem", "r")
        except:
            return ""
        f_result = f_file.read()
        f_file.close()
        return f_result

    def get_item(self, a_item_name):
        return pydaw_item.from_str(self.get_item_string(a_item_name))

    def get_tracks_string(self):
        try:
            f_file = open(self.project_folder + "/default.pytracks", "r")
        except:
            return pydaw_terminating_char
        f_result = f_file.read()
        f_file.close()
        return f_result

    def get_tracks(self):
        return pydaw_tracks.from_str(self.get_tracks_string())
        
    def get_transport(self):
        try:
            f_file = open(self.project_folder + "/default.pytransport", "r")
        except:
            return pydaw_transport()  #defaults
        f_str = f_file.read()
        f_file.close()
        return pydaw_transport.from_str(f_str)
    
    def save_transport(self, a_transport):
        if not self.suppress_updates:
            f_file_name = self.project_folder + "/default.pytransport"
            f_file = open(f_file_name, "w")
            f_file.write(a_transport.__str__())
            f_file.close()        
            self.git_repo.git_commit(f_file_name, "Save transport settings...")

    def create_empty_region(self, a_region_name):
        #TODO:  Check for uniqueness, from a pydaw_project.check_for_uniqueness method...
        f_file_name = self.regions_folder + "/" + a_region_name + ".pyreg"
        f_file = open(f_file_name, 'w')
        f_file.write(pydaw_terminating_char)
        f_file.close()
        self.git_repo.git_add(f_file_name)
        self.git_repo.git_commit(f_file_name, "Created empty region " + a_region_name)

    def create_empty_item(self, a_item_name):
        #TODO:  Check for uniqueness, from a pydaw_project.check_for_uniqueness method...
        f_file_name = self.items_folder + "/" + a_item_name + ".pyitem"
        f_file = open(f_file_name, 'w')
        f_file.write(pydaw_terminating_char)
        f_file.close()
        self.git_repo.git_add(f_file_name)
        self.git_repo.git_commit(f_file_name, "Created empty item " + a_item_name)
        
    def copy_region(self, a_old_region, a_new_region):
        f_new_file = self.regions_folder + "/" + str(a_new_region) + ".pyreg"
        copyfile(self.regions_folder + "/" + str(a_old_region) + ".pyreg", f_new_file)        
        self.git_repo.git_add(f_new_file)
        self.git_repo.git_commit(f_new_file, "Created new region " + a_new_region + " copying from " + a_old_region)

    def copy_item(self, a_old_item, a_new_item):
        f_new_file = self.items_folder + "/" + str(a_new_item) + ".pyitem"
        copyfile(self.items_folder + "/" + str(a_old_item) + ".pyitem", f_new_file)
        self.git_repo.git_add(f_new_file)
        self.git_repo.git_commit(f_new_file, "Created new item " + a_new_item + " copying from " + a_old_item)
        
    def save_item(self, a_name, a_item):
        if not self.suppress_updates:
            f_name = str(a_name)
            f_file_name = self.items_folder + "/" + f_name + ".pyitem"
            f_file = open(f_file_name, 'w')
            f_file.write(a_item.__str__())
            f_file.close()
            self.this_dssi_gui.pydaw_save_item(f_name)
            self.git_repo.git_commit(f_file_name, "Edited item " + f_name)

    def save_region(self, a_name, a_region):
        if not self.suppress_updates:
            f_name = str(a_name)
            f_file_name = self.regions_folder + "/" + f_name + ".pyreg"
            f_file = open(f_file_name, 'w')
            f_file.write(a_region.__str__())
            f_file.close()        
            self.this_dssi_gui.pydaw_save_region(f_name)
            self.git_repo.git_commit(f_file_name, "Edited region " + f_name)

    def save_song(self, a_song):
        if not self.suppress_updates:
            f_file_name = self.project_folder + "/default.pysong"
            f_file = open(f_file_name, 'w')
            f_file.write(a_song.__str__())
            f_file.close()
            self.this_dssi_gui.pydaw_save_song()
            self.git_repo.git_commit(f_file_name, "Edited song")

    def save_tracks(self, a_tracks):
        if not self.suppress_updates:
            f_file_name = self.project_folder + "/default.pytracks"
            f_file = open(f_file_name, 'w')
            f_file.write(a_tracks.__str__())
            f_file.close()    
            #Is there a need for a configure message here?        
            self.git_repo.git_commit('-a', "Edited tracks")

    def get_next_default_item_name(self):
        self.last_item_number -= 1
        for i in range(self.last_item_number, 10000):
            f_result = self.items_folder + "/item-" + str(i) + ".pyitem"
            if not os.path.isfile(f_result):
                self.last_item_number = i
                return "item-" + str(i)

    def get_next_default_region_name(self):
        self.last_region_number -= 1
        for i in range(self.last_region_number, 10000):
            f_result = self.regions_folder + "/region-" + str(i) + ".pyreg"
            if not os.path.isfile(f_result):
                self.last_item_number = i
                return "region-" + str(i)

    def get_item_list(self):
        f_result = []
        for files in os.listdir(self.items_folder):
            if files.endswith(".pyitem"):
                f_result.append(files.split(".pyitem")[0])
        f_result.sort()
        return f_result

    def get_region_list(self):
        f_result = []
        for files in os.listdir(self.regions_folder):
            if files.endswith(".pyreg"):
                f_result.append(files.split(".pyreg")[0])
        f_result.sort()
        return f_result
        
    def quit_handler(self):
        #self.session_mgr.quit_hander() #deprecated
        self.this_dssi_gui.stop_server()        

    def __init__(self, a_osc_url=None):
        self.last_item_number = 1
        self.last_region_number = 1
        self.this_dssi_gui = dssi_gui(a_osc_url)
        self.suppress_updates = False

class pydaw_song:
    def add_region_ref(self, a_pos, a_region_name):
        self.regions[int(a_pos)] = str(a_region_name)

    def remove_region_ref(self, a_pos):
        if a_pos in self.regions:
            del self.regions[a_pos]

    def __init__(self):
        self.regions = {}

    def __str__(self):
        f_result = ""
        for k, v in self.regions.iteritems():
            f_result += str(k) + "|" + v + "\n"
        f_result += pydaw_terminating_char
        return f_result
    @staticmethod
    def from_str(a_str):
        f_result = pydaw_song()
        f_arr = a_str.split("\n")
        for f_line in f_arr:
            if f_line == pydaw_terminating_char:
                break
            else:
                f_region = f_line.split("|")
                f_result.add_region_ref(int(f_region[0]), f_region[1])
        return f_result

class pydaw_region:
    def add_item_ref(self, a_track_num, a_bar_num, a_item_name):
        self.remove_item_ref(a_track_num, a_bar_num)
        self.items.append(pydaw_region.region_item(a_track_num, a_bar_num, a_item_name))

    def remove_item_ref(self, a_track_num, a_bar_num):
        for f_item in self.items:
            if f_item.bar_num == a_bar_num and f_item.track_num == a_track_num:
                self.items.remove(f_item)
                print("remove_item_ref removed bar: " + str(f_item.bar_num) + ", track: " + str(f_item.track_num))

    def __init__(self, a_name):
        self.items = []
        self.name = a_name
        self.region_length_bars = 0  #0 == default length for project

    def __str__(self):
        f_result = ""
        if self.region_length_bars > 0:
            f_result += "L|" + str(self.region_length_bars) + "|0\n"
        for f_item in self.items:
            f_result += str(f_item.track_num) + "|" + str(f_item.bar_num) + "|" + f_item.item_name + "\n"
        f_result += pydaw_terminating_char
        return f_result

    @staticmethod
    def from_str(a_name, a_str):
        f_result = pydaw_region(a_name)
        f_arr = a_str.split("\n")
        for f_line in f_arr:
            if f_line == pydaw_terminating_char:
                break
            else:
                f_item_arr = f_line.split("|")
                if f_item_arr[0] == "L":
                    f_result.region_length_bars = int(f_item_arr[1])
                    continue
                f_result.add_item_ref(int(f_item_arr[0]), int(f_item_arr[1]), f_item_arr[2])
        return f_result

    class region_item:
        def __init__(self, a_track_num, a_bar_num, a_item_name):
            self.track_num = a_track_num
            self.bar_num = a_bar_num
            self.item_name = a_item_name

class pydaw_item:
    def add_note(self, a_note):
        for note in self.notes:
            if note.overlaps(a_note):
                return False  #TODO:  return -1 instead of True, and the offending editor_index when False
        self.notes.append(a_note)
        self.notes.sort()
        return True
        
    def remove_note(self, a_note):
        for i in range(0, len(self.notes)):
            if self.notes[i] == a_note:
                self.notes.pop(i)
                break
            
    def transpose(self, a_semitones, a_octave=0, a_notes=None):
        f_total = a_semitones + (a_octave * 12)
        f_notes = []
        
        if a_notes is None:
            f_notes = self.notes
        else:
            for i in range(len(a_notes)):
                for f_note in self.notes:
                    if f_note == a_notes[i]:
                        f_notes.append(f_note)
                        break
        
        for note in f_notes:                
            note.note_num += f_total
            if note.note_num < 0:
                note.note_num = 0
            elif note.note_num > 127:
                note.note_num = 127
           
    def length_shift(self, a_length, a_min_max=0.5, a_notes=None):
        """ Note lengths are clipped at up to a_min_max if a_length > 0, or down to a_min_max if a_length < 0"""
        f_notes = []
        
        if a_notes is None:
            f_notes = self.notes
        else:
            for i in range(len(a_notes)):
                for f_note in self.notes:
                    if f_note == a_notes[i]:
                        f_notes.append(f_note)
                        break

        f_length = float(a_length)
        f_min_max = float(a_min_max)
        
        for f_note in f_notes:
            f_note.length += f_length
            if f_length < 0 and f_note.length < f_min_max:
                f_note.length = f_min_max
            elif f_length > 0 and f_note.length > f_min_max:
                f_note.length = f_min_max
        self.fix_overlaps()
                
    def fix_overlaps(self):
        """ Truncate the lengths of any notes that overlap the start of another note """
        for f_note in self.notes:
            for f_note2 in self.notes:
                if f_note != f_note2:
                    if f_note.note_num == f_note2.note_num and f_note2.start > f_note.start:
                        f_note_end = f_note.start + f_note.length
                        if f_note_end > f_note2.start:
                            f_note.length = f_note2.start - f_note.start
            
    def time_shift(self, a_shift, a_events_move_with_item=False, a_notes=None):
        """ Move all items forward or backwards by a_shift number of beats, wrapping if before or after the item"""
        f_shift = float(a_shift)
        if f_shift < -4.0:
            f_shift = -4.0
        elif f_shift > 4.0:
            f_shift = 4.0
            
        f_notes = []
        f_ccs = []
        f_pbs = []
        
        if a_notes is None:
            f_notes = self.notes
            f_ccs = self.ccs
            f_pbs = self.pitchbends
        else:
            for i in range(len(a_notes)):
                for f_note in self.notes:
                    if f_note == a_notes[i]:
                        if a_events_move_with_item:
                            f_start = f_note.start
                            f_end = f_note.start + f_note.length
                            for f_cc in self.ccs:
                                if f_cc.start >= f_start and f_cc.start <= f_end:
                                    f_ccs.append(f_cc)
                            for f_pb in self.pitchbends:
                                if f_pb.start >= f_start and f_pb.start <= f_end:
                                    f_pbs.append(f_pb)
                        f_notes.append(f_note)
                        break            
            
        for note in f_notes:
            note.start += f_shift
            if note.start < 0.0:
                note.start += 4.0
            elif note.start > 4.0:
                note.start -= 4.0
        if a_events_move_with_item:
            for cc in f_ccs:
                cc.start += f_shift
                if cc.start < 0.0:
                    cc.start += 4.0
                elif cc.start > 4.0:
                    cc.start -= 4.0
            for pb in f_pbs:
                pb.start += f_shift
                if pb.start < 0.0:
                    pb.start += 4.0
                elif pb.start > 4.0:
                    pb.start -= 4.0
            
    def get_next_default_note(self):
        pass

    def add_cc(self, a_cc):
        for cc in self.ccs:
            if a_cc == cc:
                return False #TODO:  return -1 instead of True, and the offending editor_index when False
        self.ccs.append(a_cc)
        self.ccs.sort()
        return True
        
    def remove_cc(self, a_cc):
        for i in range(0, len(self.ccs)):
            if self.ccs[i] == a_cc:
                self.ccs.pop(i)
                break
            
    #TODO:  A maximum number of events per line?
    def draw_cc_line(self, a_cc, a_start, a_start_val, a_end, a_end_val, a_curve=0):
        f_cc = int(a_cc)        
        f_start = float(a_start)
        f_start_val = int(a_start_val)
        f_end = float(a_end)
        f_end_val = int(a_end_val)
        #Pop any events that would overlap
        f_to_be_removed = []
        for cc in self.ccs:
            if cc.cc_num == f_cc and cc.start >= f_start and cc.start <= f_end:
                f_to_be_removed.append(cc)
        for cc in f_to_be_removed:
            self.ccs.remove(cc)
        
        f_start_diff = f_end - f_start
        f_val_diff = abs(f_end_val - f_start_val)
        if f_start_val > f_end_val:
            f_inc = -1
        else:
            f_inc = 1
        f_time_inc = abs(f_start_diff/float(f_val_diff))
        for i in range(0, (f_val_diff + 1)):
            self.ccs.append(pydaw_cc(round(f_start, 4), f_cc, f_start_val))
            f_start_val += f_inc
            f_start += f_time_inc
        self.ccs.sort()
    
    def add_pb(self, a_pb):
        for pb in self.pitchbends:
            if a_pb == pb:
                return False #TODO:  return -1 instead of True, and the offending editor_index when False
        self.pitchbends.append(a_pb)
        self.pitchbends.sort()
        return True
        
    def remove_pb(self, a_pb):
        for i in range(0, len(self.pitchbends)):
            if self.pitchbends[i] == a_pb:
                self.pitchbends.pop(i)
                break                       

    def draw_pb_line(self, a_start, a_start_val, a_end, a_end_val, a_curve=0):
        f_start = float(a_start)
        f_start_val = float(a_start_val)
        f_end = float(a_end)
        f_end_val = float(a_end_val)
        #Pop any events that would overlap
        f_to_be_removed = []
        for pb in self.pitchbends:
            if pb.start >= f_start and pb.start <= f_end:
                f_to_be_removed.append(pb)
        for pb in f_to_be_removed:
            self.pitchbends.remove(pb)
        
        f_start_diff = f_end - f_start        
        f_val_diff = abs(f_end_val - f_start_val)
        if f_start_val > f_end_val:
            f_inc = -0.05
        else:
            f_inc = 0.05
        f_time_inc = abs(f_start_diff/(float(f_val_diff) * 20.0))
        for i in range(0, int((f_val_diff * 20) + 1)):
            self.pitchbends.append(pydaw_pitchbend(round(f_start, 4), f_start_val))
            f_start_val += f_inc
            f_start += f_time_inc
        self.pitchbends.sort()
            
    def get_next_default_cc(self):
        pass

    @staticmethod
    def from_str(a_str):
        f_result = pydaw_item()
        f_arr = a_str.split("\n")
        for f_event_str in f_arr:
            if f_event_str == pydaw_terminating_char:
                break
            else:
                f_event_arr = f_event_str.split("|")
                if f_event_arr[0] == "n":
                    f_result.add_note(pydaw_note.from_arr(f_event_arr))
                elif f_event_arr[0] == "c":
                    f_result.add_cc(pydaw_cc.from_arr(f_event_arr))
                elif f_event_arr[0] == "p":
                    f_result.add_pb(pydaw_pitchbend.from_arr(f_event_arr))
        return f_result

    def __init__(self):
        self.notes = []
        self.ccs = []
        self.pitchbends = []

    def __str__(self):
        f_result = ""
        self.notes.sort()
        self.ccs.sort()
        self.pitchbends.sort()
        for note in self.notes:
            f_result += note.__str__()
        for cc in self.ccs:
            f_result += cc.__str__()
        for pb in self.pitchbends:
            f_result += pb.__str__()
        f_result += pydaw_terminating_char
        return f_result

class pydaw_note:
    def __eq__(self, other):
        return((self.start == other.start) and (self.note_num == other.note_num)) #The other values shouldn't need comparison if overlapping note filtering worked
    
    def __lt__(self, other):
        return self.start < other.start
    
    def __init__(self, a_start, a_length, a_note_number, a_velocity):
        self.start = float(a_start)
        self.length = float(a_length)
        self.velocity = int(a_velocity)
        self.note_num = int(a_note_number)        
        self.end = self.length + self.start
        
    def overlaps(self, other):
        if self.note_num == other.note_num:
            if other.start >= self.start and other.start < self.end:
                return True
            elif other.start < self.start and other.end > self.start:
                return True
        return False

    @staticmethod
    def from_arr(a_arr):
        f_result = pydaw_note(a_arr[1], a_arr[2], a_arr[3], a_arr[4])
        return f_result

    @staticmethod
    def from_str(a_str):
        f_arr = a_str.split("|")
        return pydaw_note.from_arr(f_arr)

    def __str__(self):
        return "n|" + str(self.start) + "|" + str(self.length) + "|" + str(self.note_num) + "|" + str(self.velocity) + "\n"

class pydaw_cc:
    def __eq__(self, other):
        return ((self.start == other.start) and (self.cc_num == other.cc_num) and (self.cc_val == other.cc_val))
        
    def __lt__(self, other):
        return self.start < other.start
    
    def __init__(self, a_start, a_cc_num, a_cc_val):
        self.start = float(a_start)
        self.cc_num = int(a_cc_num)
        self.cc_val = int(a_cc_val)

    def __str__(self):
        return "c|" + str(self.start) + "|" + str(self.cc_num) + "|" + str(self.cc_val) + "\n"

    @staticmethod
    def from_arr(a_arr):
        f_result = pydaw_cc(a_arr[1], a_arr[2], a_arr[3])
        return f_result

    @staticmethod
    def from_str(a_str):
        f_arr = a_str.split("|")
        return pydaw_note.from_arr(f_arr)

class pydaw_pitchbend:
    def __eq__(self, other):
        return ((self.start == other.start) and (self.pb_val == other.pb_val))  #TODO:  get rid of the pb_val comparison?
        
    def __lt__(self, other):
        return self.start < other.start
    
    def __init__(self, a_start, a_pb_val):
        self.start = float(a_start)        
        self.pb_val = float(a_pb_val)

    def __str__(self):
        return "p|" + str(self.start) + "|" + str(self.pb_val) + "\n"

    @staticmethod
    def from_arr(a_arr):
        f_result = pydaw_pitchbend(a_arr[1], a_arr[2])
        return f_result

    @staticmethod
    def from_str(a_str):
        f_arr = a_str.split("|")
        return pydaw_note.from_arr(f_arr)
        
class pydaw_tracks:
    def add_track(self, a_index, a_track):
        self.tracks[a_index] = a_track

    def __init__(self):
        self.tracks = {}

    def __str__(self):
        f_result = ""
        for k, v in self.tracks.iteritems():            
            f_result += str(k) + "|" + bool_to_int(v.solo) + "|" + bool_to_int(v.mute) + "|" + bool_to_int(v.rec) + "|" + str(v.vol) + "|" + v.name + "|" + str(v.inst) + "\n"
        f_result += pydaw_terminating_char
        return f_result

    @staticmethod
    def from_str(a_str):
        f_result = pydaw_tracks()
        f_arr = a_str.split("\n")
        for f_line in f_arr:
            if not f_line == pydaw_terminating_char:
                f_line_arr = f_line.split("|")
                if f_line_arr[1] == "1": f_solo = True
                else: f_solo = False
                if f_line_arr[2] == "1": f_mute = True
                else: f_mute = False
                if f_line_arr[3] == "1": f_rec = True
                else: f_rec = False
                f_result.add_track(int(f_line_arr[0]), pydaw_track(f_solo, f_mute, f_rec, int(f_line_arr[4]), f_line_arr[5], int(f_line_arr[6])))
        return f_result

class pydaw_track:
    def __init__(self, a_solo, a_mute, a_rec, a_vol, a_name, a_inst):
        self.name = a_name
        self.solo = a_solo
        self.mute = a_mute
        self.rec = a_rec
        self.vol = a_vol
        self.inst = a_inst
        
class pydaw_transport:
    def __init__(self, a_bpm=140, a_midi_keybd=None, a_loop_mode=0, a_region=0, a_bar=0):
        self.bpm = a_bpm
        self.midi_keybd = a_midi_keybd
        self.loop_mode = a_loop_mode
        self.region = a_region
        self.bar = a_bar
        
    def __str__(self):
        return str(self.bpm) + "|" + str(self.midi_keybd) + "|" + str(self.loop_mode) + "|" + str(self.region) + "|" + str(self.bar) + "\n\\"
        
    @staticmethod
    def from_str(a_str):
        f_str = a_str.split("\n")[0]
        f_arr = f_str.split("|")
        for i in range(len(f_arr)):
            if f_arr[i] == "":
                f_arr[i] = None
        return pydaw_transport(f_arr[0], f_arr[1], f_arr[2], f_arr[3], f_arr[4])