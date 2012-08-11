/* -*- c-basic-offset: 4 -*-  vi:set ts=8 sts=4 sw=4: */

/* synth_qt_gui.h

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

*/

#ifndef _SYNTH_QT_GUI_H_INCLUDED_
#define _SYNTH_QT_GUI_H_INCLUDED_

#include <QFrame>
#include <QDial>
#include <QLabel>
#include <QLayout>
#include <QCheckBox>
#include <QGroupBox>
#include <QComboBox>
#include <QPushButton>
#include <QPixmap>

#include <string>
#include <stdlib.h>

#include "../../libmodsynth/widgets/presets.h"
#include "../../libmodsynth/widgets/group_box.h"
#include "../../libmodsynth/widgets/lms_combobox.h"
#include "../../libmodsynth/widgets/lms_main_layout.h"
#include "../../libmodsynth/widgets/ui_modules/adsr.h"
#include "../../libmodsynth/widgets/ui_modules/oscillator.h"
#include "../../libmodsynth/widgets/ui_modules/filter.h"
#include "../../libmodsynth/widgets/ui_modules/ramp_env.h"
#include "../../libmodsynth/widgets/ui_modules/lfo.h"
#include "../../libmodsynth/widgets/ui_modules/master.h"
#include "../../libmodsynth/widgets/lms_session_manager.h"

extern "C" {
#include <lo/lo.h>
}

class SynthGUI : public QFrame
{
    Q_OBJECT

public:
    SynthGUI(const char * host, const char * port,
	     QByteArray controlPath, QByteArray midiPath, QByteArray programPath,
	     QByteArray exitingPath, QWidget *w = 0, bool a_is_session = FALSE, QString a_project_path = QString(""), QString a_instance_name = QString(""));
    virtual ~SynthGUI();

    bool ready() const { return m_ready; }
    void setReady(bool ready) { m_ready = ready; }

    void setHostRequestedQuit(bool r) { m_hostRequestedQuit = r; }
    
    
    void v_set_control(int, float);
    void v_control_changed(int, int, bool);
    int i_get_control(int);
    
    void v_print_port_name_to_cerr(int);
    
    void lms_value_changed(int, LMS_control *);
    void lms_set_value(float, LMS_control *);
    
    QString project_path;
    QString instance_name;
    
    bool is_session;
        
public slots:
    /*Event handlers for setting knob values*/
    void setAttack (float);
    void setDecay  (float);
    void setSustain(float);
    void setRelease(float);
    void setTimbre (float);
    void setRes (float);
    void setDist (float);
        
    void setFilterAttack (float);
    void setFilterDecay  (float);
    void setFilterSustain(float);
    void setFilterRelease(float);
    
    void setNoiseAmp(float);
    
    void setFilterEnvAmt(float);
    void setDistWet(float);
    void setOsc1Type(float);
    void setOsc1Pitch(float);
    void setOsc1Tune(float);
    void setOsc1Volume(float);
    void setOsc2Type(float);
    void setOsc2Pitch(float);
    void setOsc2Tune(float);
    void setOsc2Volume(float);
    void setMasterVolume(float);
    
    void setMasterUnisonVoices(float);
    void setMasterUnisonSpread(float);
    void setMasterGlide(float);
    void setMasterPitchbendAmt(float);
    
    void setPitchEnvTime(float);
    void setPitchEnvAmt(float);
    
    void setProgram(float);    
    
    void setLFOfreq(float);
    void setLFOtype(float);
    void setLFOamp(float);
    void setLFOpitch(float);
    void setLFOcutoff(float);
    
    void aboutToQuit();
    
protected slots:
    /*Event handlers for receiving changed knob values*/
    void attackChanged (int);
    void decayChanged  (int);
    void sustainChanged(int);
    void releaseChanged(int);
    void timbreChanged (int);
    void resChanged (int);
    void distChanged (int);
        
    void filterAttackChanged (int);
    void filterDecayChanged  (int);
    void filterSustainChanged(int);
    void filterReleaseChanged(int);
    
    void noiseAmpChanged(int);

    
    void filterEnvAmtChanged(int);
    void distWetChanged(int);
    void osc1TypeChanged(int);
    void osc1PitchChanged(int);
    void osc1TuneChanged(int);
    void osc1VolumeChanged(int);
    void osc2TypeChanged(int);
    void osc2PitchChanged(int);
    void osc2TuneChanged(int);
    void osc2VolumeChanged(int);
    void masterVolumeChanged(int);
    
    void masterUnisonVoicesChanged(int);
    void masterUnisonSpreadChanged(int);
    void masterGlideChanged(int);
    void masterPitchbendAmtChanged(int);
    
    void pitchEnvTimeChanged(int);
    void pitchEnvAmtChanged(int);
    
    void programChanged(int);
    void programSaved();
    
    void LFOfreqChanged(int);
    void LFOtypeChanged(int);
    void LFOampChanged(int);
    void LFOpitchChanged(int);
    void LFOcutoffChanged(int);
    
    void test_press();
    void test_release();
    void oscRecv();
    void sessionTimeout();
protected:
    
    LMS_main_layout * m_main_layout;
    
    LMS_adsr_widget * m_adsr_amp;
    LMS_adsr_widget * m_adsr_filter;
    LMS_oscillator_widget * m_osc1;
    LMS_oscillator_widget * m_osc2;    
    LMS_filter_widget * m_filter;
    LMS_knob_regular * m_filter_env_amt;
    LMS_ramp_env * m_pitch_env;
    
    LMS_lfo_widget * m_lfo;
    LMS_knob_regular *m_lfo_amp;
    LMS_knob_regular *m_lfo_pitch;
    LMS_knob_regular *m_lfo_cutoff;
    
    LMS_master_widget * m_master;
    
    LMS_group_box * m_groupbox_distortion;
    LMS_knob_regular *m_dist;
    LMS_knob_regular *m_dist_wet;
        
    LMS_group_box * m_groupbox_noise;
    LMS_knob_regular *m_noise_amp;
        
    LMS_preset_manager * m_program;
    
    lo_address m_host;
    QByteArray m_controlPath;
    QByteArray m_midiPath;
    QByteArray m_programPath;
    QByteArray m_exitingPath;

    bool m_suppressHostUpdate;
    bool m_hostRequestedQuit;
    bool m_ready;    
};


#endif
