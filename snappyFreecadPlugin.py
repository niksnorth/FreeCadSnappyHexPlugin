# -*- coding: utf-8 -*-
# Mesh with SnappyHexMesh inside of FreeCAD
# Author: Nishant Singh
#

# CONFIGURATION - EDIT THE FOLLOWING LINE TO MATCH YOUR SnappyHex BINARY
snappy_bin_linux = "/usr/bin/snappy"
snappy_bin_windwos = "C:\\Program Files\\blueCFD-Core-2017\\OpenFOAM-5.x\\platforms\\mingw_w64GccDPInt32Opt\\bin\\snappyHexMesh.exe"
snappy_bin_other = "/usr/bin/snappy"
# END CONFIGURATION

# START OF MACRO
from PySide import QtGui, QtCore
import Fem
import FemGui
import FemAnalysis
import FreeCAD
import FreeCADGui
import ImportGui
import Mesh
import subprocess
import sys
import tempfile
from platform import system
if system() == "Linux":
    snappy_bin = snappy_bin_linux
    path_sep = "/"
elif system() == "Windows":
    snappy_bin = snappy_bin_windwos
    path_sep = "\\"
else:
    snappy_bin = snappy_bin_other
    path_sep = "/"

class MeshSnappy(QtGui.QWidget):
    def __init__(self):
        super(MeshSnappy, self).__init__()
        self.initUI()

    def __del__(self):
        return

    def initUI(self):
        # Mesh dimension
        self.rb_1D = QtGui.QRadioButton("   1D", self)
        self.rb_2D = QtGui.QRadioButton("   2D", self)
        self.rb_3D = QtGui.QRadioButton("   3D", self)
        self.rb_3D.setChecked(QtCore.Qt.Checked)
        # Optimized:
        self.cb_optimized = QtGui.QCheckBox("    Optimized", self)
        self.cb_optimized.setChecked(QtCore.Qt.Checked)
        # Create Mechanical Analysis from mesh
        self.cb_mec_anal = QtGui.QCheckBox("    Create Mechanical Analysis from mesh",self)
        #self.cb_mec_anal.setChecked(QtCore.Qt.Checked)
        # Algorithm:
        self.l_algorithm = QtGui.QLabel("Algorithm ", self)
        self.cmb_algorithm = QtGui.QComboBox(self)
        self.algorithm_list = [self.tr('iso'), self.tr('netgen'), self.tr('tetgen'), self.tr('meshadapt'), ]
        self.cmb_algorithm.addItems(self.algorithm_list)
        self.cmb_algorithm.setCurrentIndex(1)
        # Format:
        self.l_format = QtGui.QLabel("Format ", self)
        self.cmb_format = QtGui.QComboBox(self)
        self.format_list = [self.tr('unv'), self.tr('stl'), self.tr('med')]
        self.cmb_format.addItems(self.format_list)
        self.cmb_format.setCurrentIndex(0)
        self.stored_cmb_format_index = 0
        # Element max size:
        self.cb_max_elme_size = QtGui.QCheckBox("  Set maximum mesh element size",self)
        self.cb_max_elme_size.setChecked(QtCore.Qt.Checked)
        self.sb_max_element_size = QtGui.QDoubleSpinBox(self)
        self.sb_max_element_size.setValue(5.0)
        self.sb_max_element_size.setMaximum(10000000.0)
        self.sb_max_element_size.setMinimum(0.00000001)
        # Element min size:
        self.cb_min_elme_size = QtGui.QCheckBox("  Set minimum mesh element size",self)
        self.sb_min_element_size = QtGui.QDoubleSpinBox(self)
        self.sb_min_element_size.setValue(1.0)
        self.sb_min_element_size.setMaximum(10000000.0)
        self.sb_min_element_size.setMinimum(0.00000001)
        self.sb_min_element_size.setEnabled(False)
        # Set Mesh Order:
        self.cb_mesh_order = QtGui.QCheckBox("  mesh order",self)
        self.cb_mesh_order.setChecked(QtCore.Qt.Checked)
        self.sb_mesh_order = QtGui.QSpinBox(self)
        self.sb_mesh_order.setValue(2)
        self.sb_mesh_order.setMaximum(5)
        self.sb_mesh_order.setMinimum(1)
        # Other Snappy commands:
        self.l_cmd_line_opt = QtGui.QLabel("Custom Snappy options ", self)
        self.le_cmd_line_opt = QtGui.QLineEdit(self)
        self.le_cmd_line_opt.setToolTip("Those option will be appended to Snappy command line call")
        # Ok buttons:
        self.okbox = QtGui.QDialogButtonBox(self)
        self.okbox.setOrientation(QtCore.Qt.Horizontal)
        self.okbox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        # Web button
        self.pb_web = QtGui.QPushButton(self)
        self.pb_web.setText("Snappy options (web)")
        # Layout:
        layout = QtGui.QGridLayout()
        layout.addWidget(self.rb_1D, 1, 0)
        layout.addWidget(self.rb_2D, 1, 1)
        layout.addWidget(self.rb_3D, 2, 0)
        layout.addWidget(self.cb_optimized, 2, 1)
        layout.addWidget(self.l_algorithm, 3, 0)
        layout.addWidget(self.cmb_algorithm, 3, 1)
        layout.addWidget(self.l_format, 4, 0)
        layout.addWidget(self.cmb_format, 4, 1)
        layout.addWidget(self.cb_max_elme_size, 5, 0)
        layout.addWidget(self.sb_max_element_size, 5, 1)
        layout.addWidget(self.cb_min_elme_size, 6, 0)
        layout.addWidget(self.sb_min_element_size, 6, 1)
        layout.addWidget(self.cb_mesh_order, 7, 0)
        layout.addWidget(self.sb_mesh_order, 7, 1)
        layout.addWidget(self.cb_mec_anal, 8, 0)
        layout.addWidget(self.l_cmd_line_opt, 9, 0)
        layout.addWidget(self.le_cmd_line_opt, 9, 1)
        layout.addWidget(self.pb_web, 10, 0)
        layout.addWidget(self.okbox, 10, 1)
        self.setLayout(layout)
        # Connectors:
        QtCore.QObject.connect(self.okbox, QtCore.SIGNAL("accepted()"), self.proceed)
        QtCore.QObject.connect(self.okbox, QtCore.SIGNAL("rejected()"), self.cancel)
        self.pb_web.clicked.connect(self.open_snappy_options)
        self.cb_max_elme_size.stateChanged.connect(self.max_size_state)
        self.cb_min_elme_size.stateChanged.connect(self.min_size_state)
        self.cb_mesh_order.stateChanged.connect(self.mesh_order_state)
        
    def max_size_state(self, state):   
        if state == QtCore.Qt.Checked:
            self.sb_max_element_size.setEnabled(True)
        else:
            self.sb_max_element_size.setEnabled(False)

    def min_size_state(self, state):   
        if state == QtCore.Qt.Checked:
            self.sb_min_element_size.setEnabled(True)
        else:
            self.sb_min_element_size.setEnabled(False)
            
    def mesh_order_state(self, state):   
        if state == QtCore.Qt.Checked:
            self.sb_mesh_order.setEnabled(True)
        else:
            self.sb_mesh_order.setEnabled(False)

    def open_snappy_options(self):
        import webbrowser
        webbrowser.open('http://www.geuz.org/snappy/doc/texinfo/snappy.html#Command_002dline-options')

    def cancel(self):
        self.close()
        d.close()

    def proceed(self):
        temp_file = tempfile.mkstemp(suffix='.step')[1]
        selection = FreeCADGui.Selection.getSelection()
        if not selection:
            QtGui.QMessageBox.critical(None, "SnappyHexMesh macro", "An object has to be selected to run snappy!")
            return
        # Export a part in step format
        ImportGui.export(selection, temp_file)
        selection_name = selection[0].Name
        # Mesh temporaly file
        file_format = self.cmb_format.currentText()
        temp_mesh_file = tempfile.tempdir + path_sep + selection_name + '_Mesh.' + file_format
        # OPTIONS snappy:
        clmax = self.sb_max_element_size.text()
        clmin = self.sb_min_element_size.text()
        cmd_line_opt = self.le_cmd_line_opt.text()
        algo = self.cmb_algorithm.currentText()
        mesh_order = self.sb_mesh_order.text()

        if self.cb_optimized.isChecked():
            cmd_optimize = ' -optimize'
        else:
            cmd_optimize = ''

        if self.rb_3D.isChecked():
            dim = ' -3 '
        if self.rb_2D.isChecked():
            dim = ' -2 '
        if self.rb_1D.isChecked():
            dim = ' -1 '
        if self.cb_max_elme_size.isChecked():
            max_size = ' -clmax ' + clmax
        else:
            max_size = ''
        if self.cb_min_elme_size.isChecked():
            min_size = ' -clmin ' + clmin
        else:
            min_size = ''
        if self.cb_mesh_order.isChecked():
            order = ' -order ' + mesh_order
        else:
            order = ''

        options = ' -algo ' + algo + max_size + min_size + cmd_optimize + order + cmd_line_opt
        # RUN Snappy
        command = snappy_bin + ' ' + temp_file + dim + '-format ' + file_format + ' -o ' + temp_mesh_file  + '' + options
        FreeCAD.Console.PrintMessage("Running: {}".format(command))
        try:
            if system() == "Linux":
                output = subprocess.check_output([command, '-1'], shell=True, stderr=subprocess.STDOUT,)
            elif system() == "Windows":
                output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT,)
            else:
                output = subprocess.check_output([command, '-1'], shell=True, stderr=subprocess.STDOUT,)
            FreeCAD.Console.PrintMessage(output)
            if file_format in ('unv', 'med'):
                Fem.insert(temp_mesh_file, FreeCAD.ActiveDocument.Name)
            if file_format == 'stl':
                Mesh.insert(temp_mesh_file, FreeCAD.ActiveDocument.Name)
            if self.cb_mec_anal.isChecked():
              FMesh = App.activeDocument().ActiveObject
              FemAnalysis.makeFemAnalysis('MechanicalAnalysis')
              FemGui.setActiveAnalysis(App.activeDocument().ActiveObject)
              App.activeDocument().ActiveObject.Member = App.activeDocument().ActiveObject.Member + [FMesh]
            if self.rb_1D.isChecked():
              FMeshG = Gui.ActiveDocument.ActiveObject
              FMeshG.DisplayMode = "Elements & Nodes"
        except:
            FreeCAD.Console.PrintError("Unexpected error in snappyHexMesh macro: {}".format(sys.exc_info()[0]))
        finally:
            try:
                del temp_file
            except:
                pass
            try:
                del temp_mesh_file
            except:
                pass


mw = FreeCADGui.getMainWindow()
d = QtGui.QDockWidget()
d.setWidget(MeshSnappy())
d.toggleViewAction().setText("SnappyHex")
d.setAttribute(QtCore.Qt.WA_DeleteOnClose)
d.setWindowTitle(" snappyHex Mesh Generator ")
mw.addDockWidget(QtCore. Qt.RightDockWidgetArea, d)

# END OF MACRO