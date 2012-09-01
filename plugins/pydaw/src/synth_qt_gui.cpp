/* -*- c-basic-offset: 4 -*-  vi:set ts=8 sts=4 sw=4: */

/* synth_qt_gui.cpp

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

*/


#include "synth_qt_gui.h"

#include <QApplication>
#include <QTextStream>
#include <QTimer>
#include <iostream>
#include <unistd.h>

#include <QPixmap>
#include <QFile>
#include <QDir>
#include <QMessageBox>

#include <stdlib.h>

#include "synth.h"
#include "meta.h"

#ifdef Q_WS_X11
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <X11/SM/SMlib.h>

static int handle_x11_error(Display *dpy, XErrorEvent *err)
{
    char errstr[256];
    XGetErrorText(dpy, err->error_code, errstr, 256);
    if (err->error_code != BadWindow) {
	std::cerr << "synth_qt_gui: X Error: "
		  << errstr << " " << err->error_code
		  << "\nin major opcode:  " << err->request_code << std::endl;
    }
    return 0;
}
#endif

using std::endl;

lo_server osc_server = 0;

static QTextStream cerr(stderr);



SynthGUI::SynthGUI(const char * host, const char * port,
		   QByteArray controlPath, QByteArray midiPath, QByteArray programPath,
		   QByteArray exitingPath, QWidget *w) :
    QFrame(w),
    m_controlPath(controlPath),
    m_midiPath(midiPath),
    m_programPath(programPath),
    m_exitingPath(exitingPath),
    m_suppressHostUpdate(true),
    m_hostRequestedQuit(false),
    m_ready(false)
{
    m_host = lo_address_new(host, port);
    
    this->setWindowTitle(QString("LMS Modulex - Modular Effects Unit"));
    
    /*Set the CSS style that will "cascade" on the other controls.  Other control's styles can be overridden by running their own setStyleSheet method*/
    this->setStyleSheet("QPushButton {background-color: black; border-style: outset; border-width: 2px; border-radius: 10px;border-color: white;font: bold 14px; min-width: 10em; padding: 6px; color:white;}  QAbstractItemView {outline: none;} QComboBox{border:1px solid white;border-radius:3px; padding:1px;background-color:black;color:white} QComboBox::drop-down{color:white;background-color:black;padding:2px;border-radius:2px;} QDial{background-color:rgb(152, 152, 152);} QFrame{background-color:rgb(0,0,0);} QGroupBox {color: white; border: 2px solid gray;  border-radius: 10px;  margin-top: 1ex; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px;} QMessageBox{color:white;background-color:black;}");

    m_main_layout = new LMS_main_layout(this);
    
    LMS_style_info * f_info = new LMS_style_info(60);
    f_info->LMS_set_label_style("QLabel{background-color: white; border: 1px solid black;  border-radius: 6px;}", 60);
    f_info->LMS_set_value_style(QString("color : white; background-color: rgba(0,0,0,0);"), 64);
        
    QTimer *myTimer = new QTimer(this);
    connect(myTimer, SIGNAL(timeout()), this, SLOT(oscRecv()));
    myTimer->setSingleShot(false);
    myTimer->start(0);
    
    m_suppressHostUpdate = false;

}

void SynthGUI::lms_set_value(float val, LMS_control * a_ctrl)
{
    m_suppressHostUpdate = true;
    a_ctrl->lms_set_value(int(val));
    m_suppressHostUpdate = false;
}

//void SynthGUI::setFX0knob0(float val){ lms_set_value(val, m_fx0->lms_knob1); }

void SynthGUI::lms_value_changed(int a_value, LMS_control * a_ctrl)
{
    a_ctrl->lms_value_changed(a_value);

    if (!m_suppressHostUpdate) {
        lo_send(m_host, m_controlPath, "if", (a_ctrl->lms_port), float(a_value));
    }
}

//void SynthGUI::fx0knob0Changed(int value){ lms_value_changed(value, m_fx0->lms_knob1); }

void SynthGUI::v_print_port_name_to_cerr(int a_port)
{
#ifdef LMS_DEBUG_MODE_QT
    switch (a_port) {
    case LMS_FX0_KNOB0:
	cerr << "LMS_FX1_KNOB1";
	break;
    case LMS_FX0_KNOB1:
	cerr << "LMS_FX1_KNOB2";
	break;        
    case LMS_DIST:
	cerr << "LMS_DIST";
	break;
    default:
	cerr << "Warning: received request to set nonexistent port " << a_port ;
        break;
    }
#endif
}

void SynthGUI::v_set_control(int a_port, float a_value)
{

#ifdef LMS_DEBUG_MODE_QT    
    cerr << "v_set_control called.  ";  
    v_print_port_name_to_cerr(a_port);
    cerr << "  value: " << a_value << endl;
#endif
    
    /*Add the controls you created to the control handler*/
    
    switch (a_port) 
    {
        //case LMS_FX0_KNOB0:	setFX0knob0(a_value); break;
    }
}

void SynthGUI::v_control_changed(int a_port, int a_value, bool a_suppress_host_update)
{
    
#ifdef LMS_DEBUG_MODE_QT    
    cerr << "v_control_changed called.  ";  
    v_print_port_name_to_cerr(a_port);
    cerr << "  value: " << a_value << endl;
#endif
    
    if(a_suppress_host_update)
        m_suppressHostUpdate = true;
       /*Add the controls you created to the control handler*/
    
    switch (a_port) {
        //case LMS_FX0_KNOB0:	fx0knob0Changed(a_value); break;
                
        default:
#ifdef LMS_DEBUG_MODE_QT
            cerr << "Warning: received request to set nonexistent port " << a_port << endl;
#endif
            break;
    }
    
    if(a_suppress_host_update)
        m_suppressHostUpdate = false;
}

/*TODO:  For the forseeable future, this will only be used for getting the values to write back to 
 the presets.tsv file;  It should probably return a string that can be re-interpreted into other values for
 complex controls that could have multiple ints, or string values, etc...*/
int SynthGUI::i_get_control(int a_port)
{        
    switch (a_port) {
    //case LMS_FX0_KNOB0: return m_fx0->lms_knob1->lms_get_value();
            
    default:
	cerr << "Warning: received request to get nonexistent port " << a_port << endl;
        return 0;
    }
}

void SynthGUI::oscRecv()
{
    if (osc_server) {
	lo_server_recv_noblock(osc_server, 1);
    }
}

void SynthGUI::aboutToQuit()
{
    if (!m_hostRequestedQuit) lo_send(m_host, m_exitingPath, "");
}

SynthGUI::~SynthGUI()
{
    lo_address_free(m_host);
}


void osc_error(int num, const char *msg, const char *path)
{
#ifdef LMS_DEBUG_MODE_QT
    cerr << "Error: liblo server error " << num
	 << " in path \"" << (path ? path : "(null)")
	 << "\": " << msg << endl;
#endif
}

int debug_handler(const char *path, const char *types, lo_arg **argv,
	      int argc, void *data, void *user_data)
{
    int i;
#ifdef LMS_DEBUG_MODE_QT
      cerr << "Warning: unhandled OSC message in GUI:" << endl;
#endif
    

    for (i = 0; i < argc; ++i) {
#ifdef LMS_DEBUG_MODE_QT
	cerr << "arg " << i << ": type '" << types[i] << "': ";
#endif
        lo_arg_pp((lo_type)types[i], argv[i]);
#ifdef LMS_DEBUG_MODE_QT
	cerr << endl;
#endif
    }
#ifdef LMS_DEBUG_MODE_QT
    cerr << "(path is <" << path << ">)" << endl;
#endif
    return 1;
}

int program_handler(const char *path, const char *types, lo_arg **argv,
	       int argc, void *data, void *user_data)
{
    //not implemented on this plugin
    return 0;
}

int configure_handler(const char *path, const char *types, lo_arg **argv,
		  int argc, void *data, void *user_data)
{
    return 0;
}

int rate_handler(const char *path, const char *types, lo_arg **argv,
	     int argc, void *data, void *user_data)
{
    return 0; /* ignore it */
}

int show_handler(const char *path, const char *types, lo_arg **argv,
	     int argc, void *data, void *user_data)
{
    SynthGUI *gui = static_cast<SynthGUI *>(user_data);
    while (!gui->ready()) sleep(1);
    if (gui->isVisible()) gui->raise();
    else gui->show();
    return 0;
}

int hide_handler(const char *path, const char *types, lo_arg **argv,
	     int argc, void *data, void *user_data)
{
    SynthGUI *gui = static_cast<SynthGUI *>(user_data);
    gui->hide();
    return 0;
}

int quit_handler(const char *path, const char *types, lo_arg **argv,
	     int argc, void *data, void *user_data)
{
    SynthGUI *gui = static_cast<SynthGUI *>(user_data);
    gui->setHostRequestedQuit(true);
    qApp->quit();
    return 0;
}

int control_handler(const char *path, const char *types, lo_arg **argv,
		int argc, void *data, void *user_data)
{
    SynthGUI *gui = static_cast<SynthGUI *>(user_data);

    if (argc < 2) {
        
#ifdef LMS_DEBUG_MODE_QT
	cerr << "Error: too few arguments to control_handler" << endl;
#endif
	return 1;
    }

    const int port = argv[0]->i;
    const float value = argv[1]->f;

#ifdef LMS_DEBUG_MODE_QT
    cerr << "control_handler called.  port:  " << port << " , value " << value << endl;
#endif

    gui->v_set_control(port, value);  
     
    gui->v_control_changed(port, value, true);

    return 0;
}

int main(int argc, char **argv)
{
#ifdef LMS_DEBUG_MODE_QT
    cerr << "Qt GUI main() called..." << endl;
#endif
    
    QApplication application(argc, argv);

    if (application.argc() != 5) {
#ifdef LMS_DEBUG_MODE_QT
	cerr << "usage: "
	     << application.argv()[0] 
	     << " <osc url>"
	     << " <plugin dllname>"
	     << " <plugin label>"
	     << " <user-friendly id>"
	     << endl;

#endif
	return 2;
    }

#ifdef Q_WS_X11
    XSetErrorHandler(handle_x11_error);
#endif

    char *url = application.argv()[1];

    char *host = lo_url_get_hostname(url);
    char *port = lo_url_get_port(url);
    char *path = lo_url_get_path(url);

    SynthGUI gui(host, port,
		 QByteArray(path) + "/control",
		 QByteArray(path) + "/midi",
		 QByteArray(path) + "/program",
		 QByteArray(path) + "/exiting",
		 0);
 
    QByteArray myControlPath = QByteArray(path) + "/control";
    QByteArray myProgramPath = QByteArray(path) + "/program";
    QByteArray myConfigurePath = QByteArray(path) + "/configure";
    QByteArray myRatePath = QByteArray(path) + "/sample-rate";
    QByteArray myShowPath = QByteArray(path) + "/show";
    QByteArray myHidePath = QByteArray(path) + "/hide";
    QByteArray myQuitPath = QByteArray(path) + "/quit";
#ifdef LMS_DEBUG_MODE_QT
    cerr << "Adding lo server methods" << endl;
#endif
    osc_server = lo_server_new(NULL, osc_error);
    lo_server_add_method(osc_server, myControlPath, "if", control_handler, &gui);
    lo_server_add_method(osc_server, myProgramPath, "ii", program_handler, &gui);
    lo_server_add_method(osc_server, myConfigurePath, "ss", configure_handler, &gui);
    lo_server_add_method(osc_server, myRatePath, "i", rate_handler, &gui);
    lo_server_add_method(osc_server, myShowPath, "", show_handler, &gui);
    lo_server_add_method(osc_server, myHidePath, "", hide_handler, &gui);
    lo_server_add_method(osc_server, myQuitPath, "", quit_handler, &gui);
    lo_server_add_method(osc_server, NULL, NULL, debug_handler, &gui);

    lo_address hostaddr = lo_address_new(host, port);
    lo_send(hostaddr,
	    QByteArray(path) + "/update",
	    "s",
	    (QByteArray(lo_server_get_url(osc_server))+QByteArray(path+1)).data());

    QObject::connect(&application, SIGNAL(aboutToQuit()), &gui, SLOT(aboutToQuit()));

    gui.setReady(true);
    
#ifdef LMS_DEBUG_MODE_QT
    cerr << "Starting GUI now..." << endl;
#endif
    
    return application.exec();
}

