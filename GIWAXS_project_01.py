import sys

# import modules
import sys
import string
import numpy as np
import time
import asyncio
import ctypes
#from ctypes import *
from ctypes import windll, c_double
#from ctypes import windll, c_double, create_string_buffer

# Imports "JSON" library
import json
# Imports "requests" library
import requests
# import pillow
from PIL import Image
# io is part of python basic installation
from io import BytesIO

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PyQt6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# COM port of the OWIS controller for the vertical Z stage
COM_PORT_Z_MOTOR = 7
# COM port of the OWIS controller for the tilt stage
COM_PORT_TILT_MOTOR = 4

class ImageCanvas(FigureCanvasQTAgg):
    """A matplotlib canvas that shows a single 2D image with a colorbar."""

    def __init__(self, title, parent=None):
        self.fig = Figure(figsize=(5, 4), tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self.title = title
        self.colorbar = None
        self.clear()

    def clear(self):
        self.ax.clear()
        self.ax.set_title(self.title)
        self.ax.set_xlabel("x (pixel)")
        self.ax.set_ylabel("y (pixel)")
        self.draw_idle()

    def show_image(self, data, extent=None):
        self.ax.clear()
        im = self.ax.imshow(data, cmap="viridis", origin="upper",
                            extent=extent, aspect="equal")
        self.ax.set_title(self.title)
        self.ax.set_xlabel("x (pixel)")
        self.ax.set_ylabel("y (pixel)")
        if self.colorbar is None:
            self.colorbar = self.fig.colorbar(im, ax=self.ax)
        else:
            self.colorbar.update_normal(im)
        self.draw_idle()

class ScanPlot2(FigureCanvasQTAgg):
    """XY plot of ROI intensity versus Z position, updated point by point."""
 
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 4), tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self.line = None
        self.clear_plot()
 
    def clear_plot(self):
        self.ax.clear()
        self.ax.set_title("Rocking curve - linear Z")
        self.ax.set_xlabel("Z position [mm]")
        self.ax.set_ylabel("ROI intensity (counts)")
        self.ax.grid(True, alpha=0.3)
        (self.line,) = self.ax.plot([], [], "o-", markersize=4)
        self.draw()
 
    def set_data(self, z_values, intensities):
        self.line.set_data(z_values, intensities)
        self.ax.relim()
        self.ax.autoscale_view()
        self.draw()

class ScanPlot3(FigureCanvasQTAgg):
    """XY plot of ROI intensity versus Z position, updated point by point."""
 
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 4), tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self.line = None
        self.clear_plot()
 
    def clear_plot(self):
        self.ax.clear()
        self.ax.set_title("Rocking curve - tilt")
        self.ax.set_xlabel("Tilt angle [deg]")
        self.ax.set_ylabel("ROI intensity (counts)")
        self.ax.grid(True, alpha=0.3)
        (self.line,) = self.ax.plot([], [], "o-", markersize=4)
        self.draw()
 
    def set_data(self, z_values, intensities):
        self.line.set_data(z_values, intensities)
        self.ax.relim()
        self.ax.autoscale_view()
        self.draw()

class ScanPlot4(FigureCanvasQTAgg):
    """XY plot of ROI intensity versus Z position, updated point by point."""
 
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 4), tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self.line = None
        self.clear_plot()
 
    def clear_plot(self):
        self.ax.clear()
        self.ax.set_title("Rocking curve - linear Z")
        self.ax.set_xlabel("Z position [mm]")
        self.ax.set_ylabel("1/(ROI intensity - intensity_half)^2 (a.u.)")
        self.ax.grid(True, alpha=0.3)
        (self.line,) = self.ax.plot([], [], "o-", markersize=4)
        self.draw()
 
    def set_data(self, z_values, intensities):
        self.line.set_data(z_values, intensities)
        self.ax.relim()
        self.ax.autoscale_view()
        self.draw()

class Tab1(QWidget):
    """Single-image acquisition with a rectangular ROI sub-image view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.roi_patch = None

        # --- Controls ---------------------------------------------------
        # --- Detector timing (integer, seconds) --------------------
        self.count_time1 = self._make_float_box(1.0)
        self.frame_time1 = self._make_float_box(1.1)

        time_form1 = QFormLayout()
        time_form1.addRow("Count time [s]:", self.count_time1)
        time_form1.addRow("Frame time [s]:", self.frame_time1)
        time_box1 = QGroupBox("Eiger timing")
        time_box1.setLayout(time_form1)
        
        self.take_button = QPushButton("Take single image")
        self.take_button.clicked.connect(self.take_single_image)

        self.x_min = self._make_spinbox(478)
        self.x_max = self._make_spinbox(490)
        self.y_min = self._make_spinbox(491)
        self.y_max = self._make_spinbox(504)

        roi_form = QFormLayout()
        roi_form.addRow("x-min (pixel):", self.x_min)
        roi_form.addRow("x-max (pixel):", self.x_max)
        roi_form.addRow("y-min (pixel):", self.y_min)
        roi_form.addRow("y-max (pixel):", self.y_max)
        roi_box = QGroupBox("ROI")
        roi_box.setLayout(roi_form)

        self.update_button = QPushButton("Update sub-image")
        self.update_button.clicked.connect(self.update_sub_image)
        self.update_button.setEnabled(False)

        self.max_intensity = self._make_spinbox(1000000)
        self.half_intensity = self._make_spinbox(500000)

        intensity_form = QFormLayout()
        intensity_form.addRow("Maximum intensity (counts):", self.max_intensity)
        intensity_form.addRow("Half intensity (counts):", self.half_intensity)
        intensity_box = QGroupBox("Maximum and half intensity")
        intensity_box.setLayout(intensity_form)

        self.status = QLabel("No image taken.")
        self.status.setWordWrap(True)

        controls = QVBoxLayout()
        controls.addWidget(time_box1)
        controls.addWidget(self.take_button)
        controls.addWidget(roi_box)
        controls.addWidget(self.update_button)
        controls.addWidget(intensity_box)
        controls.addWidget(self.status)
        controls.addStretch()

        controls_widget = QWidget()
        controls_widget.setLayout(controls)
        controls_widget.setFixedWidth(300)

        # --- Displays ---------------------------------------------------
        self.image_canvas = ImageCanvas("GIWAXS Image", self)
        self.sub_canvas = ImageCanvas("ROI sub-image", self)

        displays = QHBoxLayout()
        displays.addWidget(self.image_canvas, stretch=1)
        displays.addWidget(self.sub_canvas, stretch=1)

        layout = QHBoxLayout(self)
        layout.addWidget(controls_widget)
        layout.addLayout(displays, stretch=1)

    @staticmethod
    def _make_spinbox(value):
        box = QSpinBox()
        box.setRange(0, 2000000000)
        box.setValue(value)
        return box

    @staticmethod    
    def _make_float_box(value):
        box = QDoubleSpinBox()
        box.setRange(-1000.0, 1000.0)
        box.setDecimals(4)
        box.setSingleStep(0.0001)
        box.setValue(value)
        return box

    # --- Acquisition ----------------------------------------------------

    def take_single_image(self):
        
        # congigure Eiger detector
        dict_data = {'value':1}
        data_json = json.dumps(dict_data)
        r = requests.put('http://10.10.10.11/detector/api/1.8.0/config/nimages', data_json)
        print(r.status_code)
        dict_data = {'value':self.count_time1.value()}
        data_json = json.dumps(dict_data)
        r = requests.put('http://10.10.10.11/detector/api/1.8.0/config/count_time', data_json)
        print(r.status_code)
        dict_data = {'value':self.frame_time1.value()}
        data_json = json.dumps(dict_data)
        r = requests.put('http://10.10.10.11/detector/api/1.8.0/config/frame_time', data_json)
        print(r.status_code)
        dict_data = {'value':8400}
        data_json = json.dumps(dict_data)
        r = requests.put('http://10.10.10.11/detector/api/1.8.0/config/photon_energy', data_json)
        print(r.status_code)
        # Print the http status code (NOTE: Only http code 200 is OK, everything else is an error)
        print("Configuration of acquition - passed")

        # Configure monitor mode
        dict_data = {'value':1000}
        data_json = json.dumps(dict_data)
        r = requests.put('http://10.10.10.11/monitor/api/1.8.0/config/buffer_size', data_json)
        print(r.status_code)
        dict_data = {'value':True}
        data_json = json.dumps(dict_data)
        r = requests.put('http://10.10.10.11/monitor/api/1.8.0/config/discard_new', data_json)
        print(r.status_code)
        dict_data = {'value':"enabled"}
        data_json = json.dumps(dict_data)
        r = requests.put('http://10.10.10.11/monitor/api/1.8.0/config/mode', data_json)
        print(r.status_code)

        print("Configuration of monitor - passed")

        # define ROI or region of interest to evaluate nanography
        # X staring pixel
        X_start_pixel=self.x_min.value()
        # X staring pixel
        X_stop_pixel=self.x_max.value()
        # Z staring pixel
        Z_start_pixel=self.y_min.value()
        # Z stop pixel
        Z_stop_pixel=self.y_max.value()
        
        r = requests.put('http://10.10.10.11/detector/api/1.8.0/command/arm')
        print(r.status_code)
        #print("Arming")

        r = requests.put('http://10.10.10.11/detector/api/1.8.0/command/trigger')
        print(r.status_code)
        print("Acquition started")
        print("Checking buffer ?")

        # wait after end of trigger 0.5 second
        time.sleep(0.5)
        r = requests.get('http://10.10.10.11:80/monitor/api/1.8.0/images/monitor')
        # convert r content to stream of bytes and read stream of bytes as image
        img = Image.open(BytesIO(r.content))
        # convert image to numpy array
        image_array = np.array(img).astype(np.int64)
        image_array[(image_array < 0) | (image_array >= 2**32 - 1)] = 0
        # sum ROI or region of interest defined in pixels
        integrated_value = np.sum(image_array[Z_start_pixel:Z_stop_pixel, X_start_pixel:X_stop_pixel])
        # insert the maximum and half intensities in spin boxes
        self.max_intensity.setValue(int(integrated_value))
        self.half_intensity.setValue(int(0.5 * integrated_value))
        # display main image in canvas
        self.image = image_array

        # Limit the ROI inputs to the image size
        ny, nx = self.image.shape
        for box in (self.x_min, self.x_max):
            box.setMaximum(nx)
        for box in (self.y_min, self.y_max):
            box.setMaximum(ny)

        self.image_canvas.show_image(self.image)
        self.roi_patch = None
        self.update_button.setEnabled(True)
        self.status.setText(f"Image taken: {nx} x {ny} pixels.")
        self.update_sub_image()

    # --- ROI ----------------------------------------------------------
    def update_sub_image(self):
        
        if self.image is None:
            return

        x0, x1 = self.x_min.value(), self.x_max.value()
        y0, y1 = self.y_min.value(), self.y_max.value()
        if x0 >= x1 or y0 >= y1:
            QMessageBox.warning(self, "Invalid ROI",
                                "x-min must be < x-max and y-min must be < y-max.")
            return

        sub = self.image[y0:y1, x0:x1]
        # extent keeps the axes in original detector pixel coordinates
        self.sub_canvas.show_image(sub, extent=(x0 - 0.5, x1 - 0.5,
                                                y1 - 0.5, y0 - 0.5))

        # Draw the ROI rectangle on the full image
        if self.roi_patch is not None:
            self.roi_patch.remove()
        self.roi_patch = Rectangle((x0 - 0.5, y0 - 0.5), x1 - x0, y1 - y0,
                                   fill=False, edgecolor="red", linewidth=1.5)
        self.image_canvas.ax.add_patch(self.roi_patch)
        self.image_canvas.draw_idle()

        self.status.setText(
            f"ROI x: {x0}-{x1}, y: {y0}-{y1}  ({x1 - x0} x {y1 - y0} px)\n"
            f"Sum: {sub.sum():.3g}   Mean: {sub.mean():.3g}"
        )

class Tab2(QWidget):
    """Rocking curve: step the vertical Z stage and sum the Tab1 ROI at each point."""

    def __init__(self, tab1, parent=None):
        super().__init__(parent)
        self.tab1 = tab1          # the ROI is taken from the boxes in Tab1
        self.z_values = []
        self.intensities2 = []
        self.reciprocal_intensities2 = []

        # --- Scan range (float) ----------------------------------------
        self.Z_start = self._make_float_box(5.0)
        self.Z_stop = self._make_float_box(7.0)
        self.Z_step = self._make_float_box(0.1)
        self.Z_step.setMinimum(0.0001)

        z_form = QFormLayout()
        z_form.addRow("Z start [mm]:", self.Z_start)
        z_form.addRow("Z stop [mm]:", self.Z_stop)
        z_form.addRow("Z step [mm]:", self.Z_step)
        z_box = QGroupBox("Vertical Z scan")
        z_box.setLayout(z_form)

        # --- Detector timing (integer, milliseconds) --------------------
        self.count_time2 = self._make_float_box(1.0)
        self.frame_time2 = self._make_float_box(1.1)

        time_form2 = QFormLayout()
        time_form2.addRow("Count time [s]:", self.count_time2)
        time_form2.addRow("Frame time [s]:", self.frame_time2)
        time_box2 = QGroupBox("Eiger timing")
        time_box2.setLayout(time_form2)

        # --- Z position at maximum  --------------------
        self.z_position_at_half_int = self._make_float_box(6.0)

        z_position_at_half_int_form = QFormLayout()
        z_position_at_half_int_form.addRow("Z position at half intensity [mm]:", self.z_position_at_half_int)
        z_position_at_half_int_box = QGroupBox("Z position at half intensity")
        z_position_at_half_int_box.setLayout(z_position_at_half_int_form)

        # --- Current z position at maximum  --------------------
        self.z_current_position_at_half_int = self._make_float_box(0.0)
        self.z_current_position_at_half_int.setReadOnly(True)

        z_current_position_at_half_int_form = QFormLayout()
        z_current_position_at_half_int_form.addRow("Current Z position at half intensity [mm]:", self.z_current_position_at_half_int)
        z_current_position_at_half_int_box = QGroupBox("Current Z position at half intensity")
        z_current_position_at_half_int_box.setLayout(z_current_position_at_half_int_form)

        # --- Buttons and status ----------------------------------------
        self.scan_button2 = QPushButton("Do vertical-Z scan")
        self.scan_button2.clicked.connect(self.start_scan2)
        self.find_half_int_button = QPushButton("Find half intensity position")
        self.find_half_int_button.clicked.connect(self.find_half_intensity_z_position)
        self.move_to_half_int_button = QPushButton("Move to half intensity position")
        self.move_to_half_int_button.clicked.connect(self.move_to_half_intensity_z_position)

        self.status2 = QLabel("Not Scanning.")
        self.status2.setWordWrap(True)

        controls = QVBoxLayout()
        controls.addWidget(z_box)
        controls.addWidget(time_box2)
        controls.addWidget(self.scan_button2)
        controls.addWidget(z_position_at_half_int_box)
        controls.addWidget(self.status2)
        controls.addWidget(self.find_half_int_button)
        controls.addWidget(self.move_to_half_int_button)
        controls.addWidget(z_current_position_at_half_int_box)
        controls.addStretch()
        
        controls_widget = QWidget()
        controls_widget.setLayout(controls)
        controls_widget.setFixedWidth(300)

        # --- Plot -------------------------------------------------------
        self.plot2 = ScanPlot2(self)
        self.plot4 = ScanPlot4(self)

        layout = QHBoxLayout(self)
        layout.addWidget(controls_widget)
        layout.addWidget(self.plot2, stretch=1)
        layout.addWidget(self.plot4, stretch=1)

    @staticmethod
    def _make_float_box(value):
        box = QDoubleSpinBox()
        box.setRange(-1000.0, 1000.0)
        box.setDecimals(4)
        box.setSingleStep(0.0001)
        box.setValue(value)
        return box

    # --- Scan -----------------------------------------------------------
    def start_scan2(self):

        # clean measurement values
        self.z_values = []
        self.intensities2 = []
        self.reciprocal_intensities2 = []
        
        # specify COM port number of Owis motor
        nComPort_Owis_motor=COM_PORT_Z_MOTOR
        # specify axis of Owis motor
        nAxis_Owis_motor=1

        # set value of Owis motor velocity
        nPosF_Owis_motor=50000

        # Z starting position
        Z_start_pos=self.Z_start.value()
        # Z stop position
        Z_stop_pos=self.Z_stop.value()
        # Z step
        Z_step=self.Z_step.value()
        # check if Z values are correct
        if Z_start_pos > Z_stop_pos:
            QMessageBox.warning(
                self,
                "Invalid scan range",
                "Z start must be less than or equal to Z stop.",
                )
            return
        else:
            # change status in label
            self.status2.setText("Scanning.")
            self.status2.setWordWrap(True)

            self.scan_button2.setEnabled(False)

            QApplication.processEvents()
        
            # calculate number of Z points
            no_Z_points=round(abs(Z_stop_pos-Z_start_pos)/Z_step)+1
            # print number of Z points
            print("Number of Z points in single vertical scan is: ", no_Z_points)
            Z_positions=np.zeros(no_Z_points)
            # fill Z positions
            for index_0 in range(no_Z_points):
                Z_positions[index_0]=Z_start_pos+Z_step*index_0
            # print Z positions
            print(Z_positions)

            # load library
            # give location of dll
            mydll = windll.LoadLibrary(r"C:\Python_Karol\GIWAXS_project_01\ps10u.dll")

            # open virtual serial interface (or serial interface via tcp/ip socket)
            if nComPort_Owis_motor==0: # find first connected control unit
                result1=mydll.PS10_SimpleConnect(1, b"") # ANSI/Unicode !!
            elif nComPort_Owis_motor==-1: # find the first connected control unit via tcp/ip socket (localhost, port=1200)
                result1=mydll.PS10_SimpleConnect(1, b"net") # ANSI/Unicode !!
            else: # connect control unit with defined COM port
                result1=mydll.PS10_Connect(1, 0, nComPort_Owis_motor, 9600,0,0,0,0)

            # initialize axis
            result1=mydll.PS10_MotorInit(1, nAxis_Owis_motor)

            # set target mode to absolute mode (0 - relative, 1 - absolute)
            result1=mydll.PS10_SetTargetMode(1, nAxis_Owis_motor, 1)

            # set velocity 
            if nPosF_Owis_motor > 0:
                result1=mydll.PS10_SetPosF(1, nAxis_Owis_motor, nPosF_Owis_motor)

            ##        # go to reference position (to start position)
            ##        result1=mydll.PS10_GoRef(1, nAxis_Owis_motor, 4)
            ##        # check move state of the axis
            ##        print("Axis is moving to reference position...")
            ##        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
            ##        while state > 0: 
            ##            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
            ##    
            ##        print("Axis is in reference position.")

            # main for loop
            for index_0 in range(no_Z_points):
                # move aboslutelly to actual Z position
                result1=mydll.PS10_MoveEx(1, nAxis_Owis_motor, c_double(Z_positions[index_0]), 1)
                # check move state of the axis
                print("Axis is moving to position...")
                state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
                while state > 0:
                    state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
                print("Axis is in position.")
                # check position
                PS10_GetPositionEx=mydll.PS10_GetPositionEx
                PS10_GetPositionEx.restype = ctypes.c_double
                result2=PS10_GetPositionEx(1, nAxis_Owis_motor)
                print( "Position=%.3f" %(result2) )
                # display currrent position
                self.z_current_position_at_half_int.setValue(result2)

                # congigure Eiger detector
                dict_data = {'value':1}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/detector/api/1.8.0/config/nimages', data_json)
                print(r.status_code)
                dict_data = {'value':self.count_time2.value()}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/detector/api/1.8.0/config/count_time', data_json)
                print(r.status_code)
                dict_data = {'value':self.frame_time2.value()}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/detector/api/1.8.0/config/frame_time', data_json)
                print(r.status_code)
                dict_data = {'value':8400}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/detector/api/1.8.0/config/photon_energy', data_json)
                print(r.status_code)
                # Print the http status code (NOTE: Only http code 200 is OK, everything else is an error)
                print("Configuration of acquition - passed")

                # Configure monitor mode
                dict_data = {'value':1000}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/monitor/api/1.8.0/config/buffer_size', data_json)
                print(r.status_code)
                dict_data = {'value':True}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/monitor/api/1.8.0/config/discard_new', data_json)
                print(r.status_code)
                dict_data = {'value':"enabled"}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/monitor/api/1.8.0/config/mode', data_json)
                print(r.status_code)

                print("Configuration of monitor - passed")

                # define ROI or region of interest to evaluate nanography
                # X staring pixel
                X_start_pixel=self.tab1.x_min.value()
                # X staring pixel
                X_stop_pixel=self.tab1.x_max.value()
                # Z staring pixel
                Z_start_pixel=self.tab1.y_min.value()
                # Z stop pixel
                Z_stop_pixel=self.tab1.y_max.value()
                
                r = requests.put('http://10.10.10.11/detector/api/1.8.0/command/arm')
                print(r.status_code)
                #print("Arming")

                r = requests.put('http://10.10.10.11/detector/api/1.8.0/command/trigger')
                print(r.status_code)
                print("Acquition started")
                print("Checking buffer ?")

                # wait after end of trigger 0.5 second
                time.sleep(0.5)
                r = requests.get('http://10.10.10.11:80/monitor/api/1.8.0/images/monitor')
                # convert r content to stream of bytes and read stream of bytes as image
                img = Image.open(BytesIO(r.content))
                # convert image to numpy array
                image_array = np.array(img).astype(np.int64)
                image_array[(image_array < 0) | (image_array >= 2**32 - 1)] = 0
                # sum ROI or region of interest defined in pixels
                integrated_value = np.sum(image_array[Z_start_pixel:Z_stop_pixel, X_start_pixel:X_stop_pixel])

                # store the point and update the plot
                self.z_values.append(float(Z_positions[index_0]))
                self.intensities2.append(float(integrated_value))
                self.plot2.set_data(self.z_values, self.intensities2)
                
                diff = float(integrated_value) - self.tab1.half_intensity.value()
                self.reciprocal_intensities2.append(1.0 / diff**2 if diff != 0 else np.nan)
                self.plot4.set_data(self.z_values, self.reciprocal_intensities2)

                self.status2.setText(f"Scanning: point {index_0 + 1} of {no_Z_points}")
                QApplication.processEvents()      # redraw plot and label now

            z_positions_array = np.asarray(self.z_values, dtype=float)
            intensities_array = np.asarray(self.intensities2, dtype=float)

            with np.errstate(divide="ignore"):
                z_scan_values = 1.0 / np.square(intensities_array - self.tab1.half_intensity.value())

            idx = int(np.argmax(z_scan_values))
            z_scan_max_value = z_scan_values[idx]
            z_position_at_max = z_positions_array[idx]
            self.z_position_at_half_int.setValue(z_position_at_max)

            # close interface
            result1=mydll.PS10_Disconnect(1)

            # change status in label
            self.status2.setText("Not Scanning.")
            self.status2.setWordWrap(True)

            self.scan_button2.setEnabled(True)

    # --- Find Z position at half intensity -----------------------------------------------------------
    def find_half_intensity_z_position(self):

        if not self.z_values:
            return
        else:
            z_positions_array = np.asarray(self.z_values, dtype=float)
            intensities_array = np.asarray(self.intensities2, dtype=float)

            with np.errstate(divide="ignore"):
                z_scan_values = 1.0 / np.square(intensities_array - self.tab1.half_intensity.value())

            idx = int(np.argmax(z_scan_values))
            z_scan_max_value = z_scan_values[idx]
            z_position_at_max = z_positions_array[idx]
            self.z_position_at_half_int.setValue(z_position_at_max)

    def move_to_half_intensity_z_position(self):

        self.move_to_half_int_button.setEnabled(False)
        
        # change status in label
        self.status2.setText("Z motor is moving.")
        self.status2.setWordWrap(True)
        
        # specify COM port number of Owis motor
        nComPort_Owis_motor=COM_PORT_Z_MOTOR
        # specify axis of Owis motor
        nAxis_Owis_motor=1

        # set value of Owis motor velocity
        nPosF_Owis_motor=50000

        # tilt target position 
        z_target_pos=self.z_position_at_half_int.value()

        # load library
        # give location of dll
        mydll = windll.LoadLibrary(r"C:\Python_Karol\GIWAXS_project_01\ps10u.dll")

        # open virtual serial interface (or serial interface via tcp/ip socket)
        if nComPort_Owis_motor==0: # find first connected control unit
            result1=mydll.PS10_SimpleConnect(1, b"") # ANSI/Unicode !!
        elif nComPort_Owis_motor==-1: # find the first connected control unit via tcp/ip socket (localhost, port=1200)
            result1=mydll.PS10_SimpleConnect(1, b"net") # ANSI/Unicode !!
        else: # connect control unit with defined COM port
            result1=mydll.PS10_Connect(1, 0, nComPort_Owis_motor, 9600,0,0,0,0)

        # initialize axis
        result1=mydll.PS10_MotorInit(1, nAxis_Owis_motor)

        # set target mode to absolute mode (0 - relative, 1 - absolute)
        result1=mydll.PS10_SetTargetMode(1, nAxis_Owis_motor, 1)

        # set velocity 
        if nPosF_Owis_motor > 0:
            result3=mydll.PS10_SetPosF(1, nAxis_Owis_motor, nPosF_Owis_motor)

##        # go to reference position (to start position)
##        result1=mydll.PS10_GoRef(1, nAxis_Owis_motor, 4)
##        # check move state of the axis
##        print("Axis is moving to reference position...")
##        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##        while state > 0: 
##            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##    
##        print("Axis is in reference position.")
            
        # move aboslutelly to actual tilt position
        result1=mydll.PS10_MoveEx(1, nAxis_Owis_motor, c_double(z_target_pos), 1)
        # check move state of the axis
        print("Axis is moving to position...")
        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        while state > 0:
            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        print("Axis is in position.")
        # check position
        PS10_GetPositionEx=mydll.PS10_GetPositionEx
        PS10_GetPositionEx.restype = ctypes.c_double
        result2=PS10_GetPositionEx(1, nAxis_Owis_motor)
        print( "Position=%.3f" %(result2) )
        # display currrent position
        self.z_current_position_at_half_int.setValue(result2)

        # close interface
        result1=mydll.PS10_Disconnect(1)

        # change status in label
        self.status2.setText("Z motor is not moving.")
        self.status2.setWordWrap(True)

        self.move_to_half_int_button.setEnabled(True)
                
class Tab3(QWidget):

    """Rocking curve: step the tilt stage and sum the Tab1 ROI at each point."""

    def __init__(self, tab1, parent=None):
        super().__init__(parent)
        self.tab1 = tab1          # the ROI is taken from the boxes in Tab1
        self.tilt_values = []
        self.intensities3 = []

        # --- Scan range (float) ----------------------------------------
        self.tilt_start = self._make_float_box(-1.0)
        self.tilt_stop = self._make_float_box(1.0)
        self.tilt_step = self._make_float_box(0.1)
        self.tilt_step.setMinimum(0.0001)

        tilt_form = QFormLayout()
        tilt_form.addRow("Tilt start [deg]:", self.tilt_start)
        tilt_form.addRow("Tilt stop [deg]:", self.tilt_stop)
        tilt_form.addRow("Tilt step [deg]:", self.tilt_step)
        tilt_box = QGroupBox("Tilt scan")
        tilt_box.setLayout(tilt_form)

        # --- Detector timing (integer, milliseconds) --------------------
        self.count_time3 = self._make_float_box(1.0)
        self.frame_time3 = self._make_float_box(1.1)

        time_form3 = QFormLayout()
        time_form3.addRow("Count time [s]:", self.count_time3)
        time_form3.addRow("Frame time [s]:", self.frame_time3)
        time_box3 = QGroupBox("Eiger timing")
        time_box3.setLayout(time_form3)

        # --- Tilt position at maximum  --------------------
        self.tilt_position_at_maximum_int = self._make_float_box(0.0)

        tilt_position_at_maximum_int_form = QFormLayout()
        tilt_position_at_maximum_int_form.addRow("Tilt position at maximum intensity [deg]:", self.tilt_position_at_maximum_int)
        tilt_position_at_maximum_int_box = QGroupBox("Tilt position at maximum intensity")
        tilt_position_at_maximum_int_box.setLayout(tilt_position_at_maximum_int_form)

        # --- Current tilt position at maximum  --------------------
        self.tilt_current_position_at_maximum_int = self._make_float_box(0.0)
        self.tilt_current_position_at_maximum_int.setReadOnly(True)

        tilt_current_position_at_maximum_int_form = QFormLayout()
        tilt_current_position_at_maximum_int_form.addRow("Current tilt position at maximum intensity [deg]:", self.tilt_current_position_at_maximum_int)
        tilt_current_position_at_maximum_int_box = QGroupBox("Current tilt position at maximum intensity")
        tilt_current_position_at_maximum_int_box.setLayout(tilt_current_position_at_maximum_int_form)

        # --- Buttons and status ----------------------------------------
        self.scan_button3 = QPushButton("Do tilt scan")
        self.scan_button3.clicked.connect(self.start_scan3)
        self.find_maximum_int_button = QPushButton("Find maximum intensity position")
        self.find_maximum_int_button.clicked.connect(self.find_maximum_intensity_tilt_position)
        self.move_to_max_int_button = QPushButton("Move to maximum intensity position")
        self.move_to_max_int_button.clicked.connect(self.move_to_maximum_intensity_tilt_position)

        self.status3 = QLabel("Not Scanning.")
        self.status3.setWordWrap(True)

        controls = QVBoxLayout()
        controls.addWidget(tilt_box)
        controls.addWidget(time_box3)
        controls.addWidget(self.scan_button3)
        controls.addWidget(tilt_position_at_maximum_int_box)
        controls.addWidget(self.status3)
        controls.addWidget(self.find_maximum_int_button)
        controls.addWidget(self.move_to_max_int_button)
        controls.addWidget(tilt_current_position_at_maximum_int_box)
        controls.addStretch()
        
        controls_widget = QWidget()
        controls_widget.setLayout(controls)
        controls_widget.setFixedWidth(300)

        # --- Plot -------------------------------------------------------
        self.plot3 = ScanPlot3(self)

        layout = QHBoxLayout(self)
        layout.addWidget(controls_widget)
        layout.addWidget(self.plot3, stretch=1)

    @staticmethod
    def _make_float_box(value):
        box = QDoubleSpinBox()
        box.setRange(-1000.0, 1000.0)
        box.setDecimals(4)
        box.setSingleStep(0.0001)
        box.setValue(value)
        return box

    # --- Scan -----------------------------------------------------------
    def start_scan3(self):

        # clean measurement values
        self.tilt_values = []
        self.intensities3 = []
        
        # specify COM port number of Owis motor
        nComPort_Owis_motor=COM_PORT_TILT_MOTOR
        # specify axis of Owis motor
        nAxis_Owis_motor=1

        # set value of Owis motor velocity
        nPosF_Owis_motor=50000

        # tilt starting position
        tilt_start_pos=self.tilt_start.value()
        # tilt stop position
        tilt_stop_pos=self.tilt_stop.value()
        # tilt step
        tilt_step=self.tilt_step.value()
##        if (tilt_start_pos <= tilt_stop_pos):
##            print("The tilt values are OK. The tilt starting value is is less or equal than tilt stop value.")
##        else:
##            print("The tilt values are not OK!!! The tilt starting value is is more than tilt stop value!!!")
##            time.sleep(300)
##            print("We are now waiting for 5 minutes.")
##            print("I recommend to close program by force!!!")
        # check if Z values are correct
        if tilt_start_pos > tilt_stop_pos:
            QMessageBox.warning(
                self,
                "Invalid scan range",
                "Tilt start must be less than or equal to tilt stop.",
                )
            return
        else:
            # change status in label
            self.status3.setText("Scanning.")
            self.status3.setWordWrap(True)

            self.scan_button3.setEnabled(False)

            QApplication.processEvents()
        
            # calculate number of tilt points
            no_tilt_points=round(abs(tilt_stop_pos-tilt_start_pos)/tilt_step)+1
            # print number of tilt points
            print("Number of tilt points in single vertical scan is: ", no_tilt_points)
            tilt_positions=np.zeros(no_tilt_points)
            # fill tilt positions
            for index_0 in range(no_tilt_points):
                tilt_positions[index_0]=tilt_start_pos+tilt_step*index_0
            # print tilt positions
            print(tilt_positions)

            # load library
            # give location of dll
            mydll = windll.LoadLibrary(r"C:\Python_Karol\GIWAXS_project_01\ps10.dll")

            # open virtual serial interface (or serial interface via tcp/ip socket)
            if nComPort_Owis_motor==0: # find first connected control unit
                result3=mydll.PS10_SimpleConnect(1, b"") # ANSI/Unicode !!
            elif nComPort_Owis_motor==-1: # find the first connected control unit via tcp/ip socket (localhost, port=1200)
                result3=mydll.PS10_SimpleConnect(1, b"net") # ANSI/Unicode !!
            else: # connect control unit with defined COM port
                result3=mydll.PS10_Connect(1, 0, nComPort_Owis_motor, 9600,0,0,0,0)

            # initialize axis
            result3=mydll.PS10_MotorInit(1, nAxis_Owis_motor)

            # set target mode to absolute mode (0 - relative, 1 - absolute)
            result3=mydll.PS10_SetTargetMode(1, nAxis_Owis_motor, 1)

            # set velocity 
            if nPosF_Owis_motor > 0:
                result3=mydll.PS10_SetPosF(1, nAxis_Owis_motor, nPosF_Owis_motor)

    ##        # go to reference position (to start position)
    ##        result3=mydll.PS10_GoRef(1, nAxis_Owis_motor, 4)
    ##        # check move state of the axis
    ##        print("Axis is moving to reference position...")
    ##        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
    ##        while state > 0: 
    ##            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
    ##    
    ##        print("Axis is in reference position.")

            # main for loop
            for index_0 in range(no_tilt_points):
                # move aboslutelly to actual tilt position
                result3=mydll.PS10_MoveEx(1, nAxis_Owis_motor, c_double(tilt_positions[index_0]), 1)
                # check move state of the axis
                print("Axis is moving to position...")
                state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
                while state > 0:
                    state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
                print("Axis is in position.")
                # check position
                PS10_GetPositionEx=mydll.PS10_GetPositionEx
                PS10_GetPositionEx.restype = ctypes.c_double
                result4=PS10_GetPositionEx(1, nAxis_Owis_motor)
                print( "Position=%.3f" %(result4) )
                # display currrent position
                self.tilt_current_position_at_maximum_int.setValue(result4)

                # congigure Eiger detector
                dict_data = {'value':1}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/detector/api/1.8.0/config/nimages', data_json)
                print(r.status_code)
                dict_data = {'value':self.count_time3.value()}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/detector/api/1.8.0/config/count_time', data_json)
                print(r.status_code)
                dict_data = {'value':self.frame_time3.value()}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/detector/api/1.8.0/config/frame_time', data_json)
                print(r.status_code)
                dict_data = {'value':8400}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/detector/api/1.8.0/config/photon_energy', data_json)
                print(r.status_code)
                # Print the http status code (NOTE: Only http code 200 is OK, everything else is an error)
                print("Configuration of acquition - passed")

                # Configure monitor mode
                dict_data = {'value':1000}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/monitor/api/1.8.0/config/buffer_size', data_json)
                print(r.status_code)
                dict_data = {'value':True}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/monitor/api/1.8.0/config/discard_new', data_json)
                print(r.status_code)
                dict_data = {'value':"enabled"}
                data_json = json.dumps(dict_data)
                r = requests.put('http://10.10.10.11/monitor/api/1.8.0/config/mode', data_json)
                print(r.status_code)

                print("Configuration of monitor - passed")

                # define ROI or region of interest to evaluate nanography
                # X staring pixel
                X_start_pixel=self.tab1.x_min.value()
                # X staring pixel
                X_stop_pixel=self.tab1.x_max.value()
                # Z staring pixel
                Z_start_pixel=self.tab1.y_min.value()
                # Z stop pixel
                Z_stop_pixel=self.tab1.y_max.value()
                
                r = requests.put('http://10.10.10.11/detector/api/1.8.0/command/arm')
                print(r.status_code)
                #print("Arming")

                r = requests.put('http://10.10.10.11/detector/api/1.8.0/command/trigger')
                print(r.status_code)
                print("Acquition started")
                print("Checking buffer ?")

                # wait after end of trigger 0.5 second
                time.sleep(0.5)
                r = requests.get('http://10.10.10.11:80/monitor/api/1.8.0/images/monitor')
                # convert r content to stream of bytes and read stream of bytes as image
                img = Image.open(BytesIO(r.content))
                # convert image to numpy array
                image_array = np.array(img).astype(np.int64)
                image_array[(image_array < 0) | (image_array >= 2**32 - 1)] = 0
                # sum ROI or region of interest defined in pixels
                integrated_value = np.sum(image_array[Z_start_pixel:Z_stop_pixel, X_start_pixel:X_stop_pixel])

                # store the point and update the plot
                self.tilt_values.append(float(tilt_positions[index_0]))
                self.intensities3.append(float(integrated_value))
                self.plot3.set_data(self.tilt_values, self.intensities3)

                self.status3.setText(f"Scanning: point {index_0 + 1} of {no_tilt_points}")
                QApplication.processEvents()      # redraw plot and label now

            tilt_positions_array = np.asarray(self.tilt_values, dtype=float)
            intensities_array = np.asarray(self.intensities3, dtype=float)

            idx = int(np.argmax(intensities_array))
            tilt_scan_max_value = intensities_array[idx]
            tilt_position_at_max = tilt_positions_array[idx]
            self.tilt_position_at_maximum_int.setValue(tilt_position_at_max)

            # close interface
            result3=mydll.PS10_Disconnect(1)

            # change status in label
            self.status3.setText("Not Scanning.")
            self.status3.setWordWrap(True)

            self.scan_button3.setEnabled(True)

    # --- Find Z position at half intensity -----------------------------------------------------------
    def find_maximum_intensity_tilt_position(self):

        if not self.tilt_values:
            return
        else:
            tilt_positions_array = np.asarray(self.tilt_values, dtype=float)
            intensities_array = np.asarray(self.intensities3, dtype=float)

            idx = int(np.argmax(intensities_array))
            tilt_scan_max_value = intensities_array[idx]
            tilt_position_at_max = tilt_positions_array[idx]
            self.tilt_position_at_maximum_int.setValue(tilt_position_at_max)
            
    def move_to_maximum_intensity_tilt_position(self):

        self.move_to_max_int_button.setEnabled(False)
        
        # change status in label
        self.status3.setText("Tilt motor is moving.")
        self.status3.setWordWrap(True)
        
        # specify COM port number of Owis motor
        nComPort_Owis_motor=COM_PORT_TILT_MOTOR
        # specify axis of Owis motor
        nAxis_Owis_motor=1

        # set value of Owis motor velocity
        nPosF_Owis_motor=50000

        # tilt target position 
        tilt_target_pos=self.tilt_position_at_maximum_int.value()

        # load library
        # give location of dll
        mydll = windll.LoadLibrary(r"C:\Python_Karol\GIWAXS_project_01\ps10.dll")

        # open virtual serial interface (or serial interface via tcp/ip socket)
        if nComPort_Owis_motor==0: # find first connected control unit
            result3=mydll.PS10_SimpleConnect(1, b"") # ANSI/Unicode !!
        elif nComPort_Owis_motor==-1: # find the first connected control unit via tcp/ip socket (localhost, port=1200)
            result3=mydll.PS10_SimpleConnect(1, b"net") # ANSI/Unicode !!
        else: # connect control unit with defined COM port
            result3=mydll.PS10_Connect(1, 0, nComPort_Owis_motor, 9600,0,0,0,0)

        # initialize axis
        result3=mydll.PS10_MotorInit(1, nAxis_Owis_motor)

        # set target mode to absolute mode (0 - relative, 1 - absolute)
        result3=mydll.PS10_SetTargetMode(1, nAxis_Owis_motor, 1)

        # set velocity 
        if nPosF_Owis_motor > 0:
            result3=mydll.PS10_SetPosF(1, nAxis_Owis_motor, nPosF_Owis_motor)

##        # go to reference position (to start position)
##        result3=mydll.PS10_GoRef(1, nAxis_Owis_motor, 4)
##        # check move state of the axis
##        print("Axis is moving to reference position...")
##        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##        while state > 0: 
##            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##    
##        print("Axis is in reference position.")
            
        # move aboslutelly to actual tilt position
        result3=mydll.PS10_MoveEx(1, nAxis_Owis_motor, c_double(tilt_target_pos), 1)
        # check move state of the axis
        print("Axis is moving to position...")
        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        while state > 0:
            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        print("Axis is in position.")
        # check position
        PS10_GetPositionEx=mydll.PS10_GetPositionEx
        PS10_GetPositionEx.restype = ctypes.c_double
        result4=PS10_GetPositionEx(1, nAxis_Owis_motor)
        print( "Position=%.3f" %(result4) )
        # display currrent position
        self.tilt_current_position_at_maximum_int.setValue(result4)

        # close interface
        result3=mydll.PS10_Disconnect(1)

        # change status in label
        self.status3.setText("Tilt motor is not moving.")
        self.status3.setWordWrap(True)

        self.move_to_max_int_button.setEnabled(True)

class Tab4(QWidget):

    def __init__(self, tab1, parent=None):
        super().__init__(parent)
        self.tab1 = tab1          # the ROI is taken from the boxes in Tab1

        # --- Scan range (float) ----------------------------------------
        self.Z_absolute_move = self._make_float_box(6.0)
        self.Z_relative_move = self._make_float_box(1.0)

        Z_move_form = QFormLayout()
        Z_move_form.addRow("Z - Move absolute [mm]:", self.Z_absolute_move)
        Z_move_form.addRow("Z - Move relative [mm]:", self.Z_relative_move)
        Z_move_box = QGroupBox("Z move")
        Z_move_box.setLayout(Z_move_form)

        # --- Current Z position  --------------------
        self.Z_current_position = self._make_float_box(0.0)
        self.Z_current_position.setReadOnly(True)

        Z_current_position_form = QFormLayout()
        Z_current_position_form.addRow("Current Z position [mm]:", self.Z_current_position)
        Z_current_position_box = QGroupBox("Current Z position")
        Z_current_position_box.setLayout(Z_current_position_form)

        # --- Buttons and status ----------------------------------------
        self.Z_absolute_move_button = QPushButton("Z move - absolute")
        self.Z_absolute_move_button.clicked.connect(self.Z_move_absolute)
        self.Z_plus_relative_move_button = QPushButton("Z Plus - move relative")
        self.Z_plus_relative_move_button.clicked.connect(self.Z_plus_move_relative)
        self.Z_minus_relative_move_button = QPushButton("Z Minus - move relative")
        self.Z_minus_relative_move_button.clicked.connect(self.Z_minus_move_relative)
        self.Z_get_position_button = QPushButton("Get position - Z [mm]")
        self.Z_get_position_button.clicked.connect(self.Z_get_position)

        self.status4 = QLabel("Not moving.")
        self.status4.setWordWrap(True)

        controls = QVBoxLayout()
        controls.addWidget(Z_move_box)
        controls.addWidget(Z_current_position_box)
        controls.addWidget(self.status4)
        controls.addWidget(self.Z_absolute_move_button)
        controls.addWidget(self.Z_plus_relative_move_button)
        controls.addWidget(self.Z_minus_relative_move_button)
        controls.addWidget(self.Z_get_position_button)
        controls.addStretch()
        
        controls_widget = QWidget()
        controls_widget.setLayout(controls)
        controls_widget.setFixedWidth(300)

        layout = QHBoxLayout(self)
        layout.addWidget(controls_widget)
        layout.addStretch()

    @staticmethod
    def _make_float_box(value):
        box = QDoubleSpinBox()
        box.setRange(-1000.0, 1000.0)
        box.setDecimals(4)
        box.setSingleStep(0.0001)
        box.setValue(value)
        return box

    def Z_move_absolute(self):

        self.Z_absolute_move_button.setEnabled(False)
        
        # change status in label
        self.status4.setText("Z motor is moving.")
        self.status4.setWordWrap(True)

        QApplication.processEvents()
        
        # specify COM port number of Owis motor
        nComPort_Owis_motor=COM_PORT_Z_MOTOR
        # specify axis of Owis motor
        nAxis_Owis_motor=1

        # set value of Owis motor velocity
        nPosF_Owis_motor=50000

        # tilt target position 
        Z_target_pos=self.Z_absolute_move.value()

        # load library
        # give location of dll
        mydll = windll.LoadLibrary(r"C:\Python_Karol\GIWAXS_project_01\ps10u.dll")

        # open virtual serial interface (or serial interface via tcp/ip socket)
        if nComPort_Owis_motor==0: # find first connected control unit
            result5=mydll.PS10_SimpleConnect(1, b"") # ANSI/Unicode !!
        elif nComPort_Owis_motor==-1: # find the first connected control unit via tcp/ip socket (localhost, port=1200)
            result5=mydll.PS10_SimpleConnect(1, b"net") # ANSI/Unicode !!
        else: # connect control unit with defined COM port
            result5=mydll.PS10_Connect(1, 0, nComPort_Owis_motor, 9600,0,0,0,0)

        # initialize axis
        result5=mydll.PS10_MotorInit(1, nAxis_Owis_motor)

        # set target mode to absolute mode (0 - relative, 1 - absolute)
        result5=mydll.PS10_SetTargetMode(1, nAxis_Owis_motor, 1)

        # set velocity 
        if nPosF_Owis_motor > 0:
            result5=mydll.PS10_SetPosF(1, nAxis_Owis_motor, nPosF_Owis_motor)

##        # go to reference position (to start position)
##        result3=mydll.PS10_GoRef(1, nAxis_Owis_motor, 4)
##        # check move state of the axis
##        print("Axis is moving to reference position...")
##        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##        while state > 0: 
##            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##    
##        print("Axis is in reference position.")
            
        # move aboslutelly to actual Z position
        result5=mydll.PS10_MoveEx(1, nAxis_Owis_motor, c_double(Z_target_pos), 1)
        # check move state of the axis
        print("Axis is moving to position...")
        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        while state > 0:
            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        print("Axis is in position.")
        # check position
        PS10_GetPositionEx=mydll.PS10_GetPositionEx
        PS10_GetPositionEx.restype = ctypes.c_double
        result6=PS10_GetPositionEx(1, nAxis_Owis_motor)
        print( "Position=%.3f" %(result6) )
        # display currrent position
        self.Z_current_position.setValue(result6)

        # close interface
        result5=mydll.PS10_Disconnect(1)

        # change status in label
        self.status4.setText("Z motor is not moving.")
        self.status4.setWordWrap(True)

        QApplication.processEvents()

        self.Z_absolute_move_button.setEnabled(True)

    def Z_plus_move_relative(self):

        self.Z_plus_relative_move_button.setEnabled(False)
        
        # change status in label
        self.status4.setText("Z motor is moving.")
        self.status4.setWordWrap(True)

        QApplication.processEvents()
        
        # specify COM port number of Owis motor
        nComPort_Owis_motor=COM_PORT_Z_MOTOR
        # specify axis of Owis motor
        nAxis_Owis_motor=1

        # set value of Owis motor velocity
        nPosF_Owis_motor=50000

        # tilt target position 
        Z_target_pos=self.Z_relative_move.value()

        # load library
        # give location of dll
        mydll = windll.LoadLibrary(r"C:\Python_Karol\GIWAXS_project_01\ps10u.dll")

        # open virtual serial interface (or serial interface via tcp/ip socket)
        if nComPort_Owis_motor==0: # find first connected control unit
            result5=mydll.PS10_SimpleConnect(1, b"") # ANSI/Unicode !!
        elif nComPort_Owis_motor==-1: # find the first connected control unit via tcp/ip socket (localhost, port=1200)
            result5=mydll.PS10_SimpleConnect(1, b"net") # ANSI/Unicode !!
        else: # connect control unit with defined COM port
            result5=mydll.PS10_Connect(1, 0, nComPort_Owis_motor, 9600,0,0,0,0)

        # initialize axis
        result5=mydll.PS10_MotorInit(1, nAxis_Owis_motor)

        # set target mode to absolute mode (0 - relative, 1 - absolute)
        result5=mydll.PS10_SetTargetMode(1, nAxis_Owis_motor, 0)

        # set velocity 
        if nPosF_Owis_motor > 0:
            result5=mydll.PS10_SetPosF(1, nAxis_Owis_motor, nPosF_Owis_motor)

##        # go to reference position (to start position)
##        result3=mydll.PS10_GoRef(1, nAxis_Owis_motor, 4)
##        # check move state of the axis
##        print("Axis is moving to reference position...")
##        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##        while state > 0: 
##            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##    
##        print("Axis is in reference position.")
            
        # move relativelly to actual Z position
        result5=mydll.PS10_MoveEx(1, nAxis_Owis_motor, c_double(Z_target_pos), 1)
        # check move state of the axis
        print("Axis is moving to position...")
        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        while state > 0:
            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        print("Axis is in position.")
        # check position
        PS10_GetPositionEx=mydll.PS10_GetPositionEx
        PS10_GetPositionEx.restype = ctypes.c_double
        result6=PS10_GetPositionEx(1, nAxis_Owis_motor)
        print( "Position=%.3f" %(result6) )
        # display currrent position
        self.Z_current_position.setValue(result6)

        # close interface
        result5=mydll.PS10_Disconnect(1)

        # change status in label
        self.status4.setText("Z motor is not moving.")
        self.status4.setWordWrap(True)

        QApplication.processEvents()

        self.Z_plus_relative_move_button.setEnabled(True)

    def Z_minus_move_relative(self):

        self.Z_minus_relative_move_button.setEnabled(False)
        
        # change status in label
        self.status4.setText("Z motor is moving.")
        self.status4.setWordWrap(True)

        QApplication.processEvents()
        
        # specify COM port number of Owis motor
        nComPort_Owis_motor=COM_PORT_Z_MOTOR
        # specify axis of Owis motor
        nAxis_Owis_motor=1

        # set value of Owis motor velocity
        nPosF_Owis_motor=50000

        # tilt target position 
        Z_target_pos=(-1.0)*self.Z_relative_move.value()

        # load library
        # give location of dll
        mydll = windll.LoadLibrary(r"C:\Python_Karol\GIWAXS_project_01\ps10u.dll")

        # open virtual serial interface (or serial interface via tcp/ip socket)
        if nComPort_Owis_motor==0: # find first connected control unit
            result5=mydll.PS10_SimpleConnect(1, b"") # ANSI/Unicode !!
        elif nComPort_Owis_motor==-1: # find the first connected control unit via tcp/ip socket (localhost, port=1200)
            result5=mydll.PS10_SimpleConnect(1, b"net") # ANSI/Unicode !!
        else: # connect control unit with defined COM port
            result5=mydll.PS10_Connect(1, 0, nComPort_Owis_motor, 9600,0,0,0,0)

        # initialize axis
        result5=mydll.PS10_MotorInit(1, nAxis_Owis_motor)

        # set target mode to absolute mode (0 - relative, 1 - absolute)
        result5=mydll.PS10_SetTargetMode(1, nAxis_Owis_motor, 0)

        # set velocity 
        if nPosF_Owis_motor > 0:
            result5=mydll.PS10_SetPosF(1, nAxis_Owis_motor, nPosF_Owis_motor)

##        # go to reference position (to start position)
##        result3=mydll.PS10_GoRef(1, nAxis_Owis_motor, 4)
##        # check move state of the axis
##        print("Axis is moving to reference position...")
##        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##        while state > 0: 
##            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##    
##        print("Axis is in reference position.")
            
        # move relativelly to actual Z position
        result5=mydll.PS10_MoveEx(1, nAxis_Owis_motor, c_double(Z_target_pos), 1)
        # check move state of the axis
        print("Axis is moving to position...")
        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        while state > 0:
            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        print("Axis is in position.")
        # check position
        PS10_GetPositionEx=mydll.PS10_GetPositionEx
        PS10_GetPositionEx.restype = ctypes.c_double
        result6=PS10_GetPositionEx(1, nAxis_Owis_motor)
        print( "Position=%.3f" %(result6) )
        # display currrent position
        self.Z_current_position.setValue(result6)

        # close interface
        result5=mydll.PS10_Disconnect(1)

        # change status in label
        self.status4.setText("Z motor is not moving.")
        self.status4.setWordWrap(True)

        QApplication.processEvents()

        self.Z_minus_relative_move_button.setEnabled(True)

    def Z_get_position(self):

        # change status in label
        self.status4.setText("Reading position - Z motor.")
        self.status4.setWordWrap(True)

        QApplication.processEvents()
   
        # specify COM port number of Owis motor
        nComPort_Owis_motor=COM_PORT_Z_MOTOR
        # specify axis of Owis motor
        nAxis_Owis_motor=1

        # load library
        # give location of dll
        mydll = windll.LoadLibrary(r"C:\Python_Karol\GIWAXS_project_01\ps10u.dll")

        # open virtual serial interface (or serial interface via tcp/ip socket)
        if nComPort_Owis_motor==0: # find first connected control unit
            result5=mydll.PS10_SimpleConnect(1, b"") # ANSI/Unicode !!
        elif nComPort_Owis_motor==-1: # find the first connected control unit via tcp/ip socket (localhost, port=1200)
            result5=mydll.PS10_SimpleConnect(1, b"net") # ANSI/Unicode !!
        else: # connect control unit with defined COM port
            result5=mydll.PS10_Connect(1, 0, nComPort_Owis_motor, 9600,0,0,0,0)

        # initialize axis
        result5=mydll.PS10_MotorInit(1, nAxis_Owis_motor)
        
        # check position
        PS10_GetPositionEx=mydll.PS10_GetPositionEx
        PS10_GetPositionEx.restype = ctypes.c_double
        result6=PS10_GetPositionEx(1, nAxis_Owis_motor)
        print( "Position=%.3f" %(result6) )
        # display currrent position
        self.Z_current_position.setValue(result6)

        # close interface
        result5=mydll.PS10_Disconnect(1)

        # change status in label
        self.status4.setText("Ending reading position - Z motor.")
        self.status4.setWordWrap(True)

        QApplication.processEvents()

class Tab5(QWidget):

    def __init__(self, tab1, parent=None):
        super().__init__(parent)
        self.tab1 = tab1          # the ROI is taken from the boxes in Tab1

        # --- Scan range (float) ----------------------------------------
        self.tilt_absolute_move = self._make_float_box(0.0)
        self.tilt_relative_move = self._make_float_box(1.0)

        tilt_move_form = QFormLayout()
        tilt_move_form.addRow("Tilt - Move absolute [deg]:", self.tilt_absolute_move)
        tilt_move_form.addRow("Tilt - Move relative [deg]:", self.tilt_relative_move)
        tilt_move_box = QGroupBox("tilt move")
        tilt_move_box.setLayout(tilt_move_form)

        # --- Current Z position  --------------------
        self.tilt_current_position = self._make_float_box(0.0)
        self.tilt_current_position.setReadOnly(True)

        tilt_current_position_form = QFormLayout()
        tilt_current_position_form.addRow("Current tilt position [deg]:", self.tilt_current_position)
        tilt_current_position_box = QGroupBox("Current tilt position")
        tilt_current_position_box.setLayout(tilt_current_position_form)

        # --- Buttons and status ----------------------------------------
        self.tilt_absolute_move_button = QPushButton("Tilt move - absolute")
        self.tilt_absolute_move_button.clicked.connect(self.tilt_move_absolute)
        self.tilt_plus_relative_move_button = QPushButton("Tilt Plus - move relative")
        self.tilt_plus_relative_move_button.clicked.connect(self.tilt_plus_move_relative)
        self.tilt_minus_relative_move_button = QPushButton("Tilt Minus - move relative")
        self.tilt_minus_relative_move_button.clicked.connect(self.tilt_minus_move_relative)
        self.tilt_get_position_button = QPushButton("Get position - tilt [deg]")
        self.tilt_get_position_button.clicked.connect(self.tilt_get_position)

        self.status5 = QLabel("Not moving.")
        self.status5.setWordWrap(True)

        controls = QVBoxLayout()
        controls.addWidget(tilt_move_box)
        controls.addWidget(tilt_current_position_box)
        controls.addWidget(self.status5)
        controls.addWidget(self.tilt_absolute_move_button)
        controls.addWidget(self.tilt_plus_relative_move_button)
        controls.addWidget(self.tilt_minus_relative_move_button)
        controls.addWidget(self.tilt_get_position_button)
        controls.addStretch()
        
        controls_widget = QWidget()
        controls_widget.setLayout(controls)
        controls_widget.setFixedWidth(300)

        layout = QHBoxLayout(self)
        layout.addWidget(controls_widget)
        layout.addStretch()

    @staticmethod
    def _make_float_box(value):
        box = QDoubleSpinBox()
        box.setRange(-1000.0, 1000.0)
        box.setDecimals(4)
        box.setSingleStep(0.0001)
        box.setValue(value)
        return box

    def tilt_move_absolute(self):

        self.tilt_absolute_move_button.setEnabled(False)
        
        # change status in label
        self.status5.setText("Tilt motor is moving.")
        self.status5.setWordWrap(True)

        QApplication.processEvents()
        
        # specify COM port number of Owis motor
        nComPort_Owis_motor=COM_PORT_TILT_MOTOR
        # specify axis of Owis motor
        nAxis_Owis_motor=1

        # set value of Owis motor velocity
        nPosF_Owis_motor=50000

        # tilt target position 
        tilt_target_pos=self.tilt_absolute_move.value()

        # load library
        # give location of dll
        mydll = windll.LoadLibrary(r"C:\Python_Karol\GIWAXS_project_01\ps10.dll")

        # open virtual serial interface (or serial interface via tcp/ip socket)
        if nComPort_Owis_motor==0: # find first connected control unit
            result7=mydll.PS10_SimpleConnect(1, b"") # ANSI/Unicode !!
        elif nComPort_Owis_motor==-1: # find the first connected control unit via tcp/ip socket (localhost, port=1200)
            result7=mydll.PS10_SimpleConnect(1, b"net") # ANSI/Unicode !!
        else: # connect control unit with defined COM port
            result7=mydll.PS10_Connect(1, 0, nComPort_Owis_motor, 9600,0,0,0,0)

        # initialize axis
        result7=mydll.PS10_MotorInit(1, nAxis_Owis_motor)

        # set target mode to absolute mode (0 - relative, 1 - absolute)
        result7=mydll.PS10_SetTargetMode(1, nAxis_Owis_motor, 1)

        # set velocity 
        if nPosF_Owis_motor > 0:
            result7=mydll.PS10_SetPosF(1, nAxis_Owis_motor, nPosF_Owis_motor)

##        # go to reference position (to start position)
##        result3=mydll.PS10_GoRef(1, nAxis_Owis_motor, 4)
##        # check move state of the axis
##        print("Axis is moving to reference position...")
##        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##        while state > 0: 
##            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##    
##        print("Axis is in reference position.")
            
        # move aboslutelly to actual tilt position
        result7=mydll.PS10_MoveEx(1, nAxis_Owis_motor, c_double(tilt_target_pos), 1)
        # check move state of the axis
        print("Axis is moving to position...")
        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        while state > 0:
            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        print("Axis is in position.")
        # check position
        PS10_GetPositionEx=mydll.PS10_GetPositionEx
        PS10_GetPositionEx.restype = ctypes.c_double
        result8=PS10_GetPositionEx(1, nAxis_Owis_motor)
        print( "Position=%.3f" %(result8) )
        # display currrent position
        self.tilt_current_position.setValue(result8)

        # close interface
        result7=mydll.PS10_Disconnect(1)
        
        # change status in label
        self.status5.setText("Tilt motor is not moving.")
        self.status5.setWordWrap(True)

        QApplication.processEvents()

        self.tilt_absolute_move_button.setEnabled(True)

    def tilt_plus_move_relative(self):

        self.tilt_plus_relative_move_button.setEnabled(False)
        
        # change status in label
        self.status5.setText("Tilt motor is moving.")
        self.status5.setWordWrap(True)

        QApplication.processEvents()
        
        # specify COM port number of Owis motor
        nComPort_Owis_motor=COM_PORT_TILT_MOTOR
        # specify axis of Owis motor
        nAxis_Owis_motor=1

        # set value of Owis motor velocity
        nPosF_Owis_motor=50000

        # tilt target position 
        tilt_target_pos=self.tilt_relative_move.value()

        # load library
        # give location of dll
        mydll = windll.LoadLibrary(r"C:\Python_Karol\GIWAXS_project_01\ps10.dll")

        # open virtual serial interface (or serial interface via tcp/ip socket)
        if nComPort_Owis_motor==0: # find first connected control unit
            result7=mydll.PS10_SimpleConnect(1, b"") # ANSI/Unicode !!
        elif nComPort_Owis_motor==-1: # find the first connected control unit via tcp/ip socket (localhost, port=1200)
            result7=mydll.PS10_SimpleConnect(1, b"net") # ANSI/Unicode !!
        else: # connect control unit with defined COM port
            result7=mydll.PS10_Connect(1, 0, nComPort_Owis_motor, 9600,0,0,0,0)

        # initialize axis
        result7=mydll.PS10_MotorInit(1, nAxis_Owis_motor)

        # set target mode to absolute mode (0 - relative, 1 - absolute)
        result7=mydll.PS10_SetTargetMode(1, nAxis_Owis_motor, 0)

        # set velocity 
        if nPosF_Owis_motor > 0:
            result7=mydll.PS10_SetPosF(1, nAxis_Owis_motor, nPosF_Owis_motor)

##        # go to reference position (to start position)
##        result3=mydll.PS10_GoRef(1, nAxis_Owis_motor, 4)
##        # check move state of the axis
##        print("Axis is moving to reference position...")
##        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##        while state > 0: 
##            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##    
##        print("Axis is in reference position.")
            
        # move relativelly to actual tilt position
        result7=mydll.PS10_MoveEx(1, nAxis_Owis_motor, c_double(tilt_target_pos), 1)
        # check move state of the axis
        print("Axis is moving to position...")
        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        while state > 0:
            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        print("Axis is in position.")
        # check position
        PS10_GetPositionEx=mydll.PS10_GetPositionEx
        PS10_GetPositionEx.restype = ctypes.c_double
        result8=PS10_GetPositionEx(1, nAxis_Owis_motor)
        print( "Position=%.3f" %(result8) )
        # display currrent position
        self.tilt_current_position.setValue(result8)

        # close interface
        result7=mydll.PS10_Disconnect(1)

        # change status in label
        self.status5.setText("Tilt motor is not moving.")
        self.status5.setWordWrap(True)

        QApplication.processEvents()

        self.tilt_plus_relative_move_button.setEnabled(True)

    def tilt_minus_move_relative(self):

        self.tilt_minus_relative_move_button.setEnabled(False)
        
        # change status in label
        self.status5.setText("Tilt motor is moving.")
        self.status5.setWordWrap(True)

        QApplication.processEvents()
        
        # specify COM port number of Owis motor
        nComPort_Owis_motor=COM_PORT_TILT_MOTOR
        # specify axis of Owis motor
        nAxis_Owis_motor=1

        # set value of Owis motor velocity
        nPosF_Owis_motor=50000

        # tilt target position 
        tilt_target_pos=(-1.0)*self.tilt_relative_move.value()

        # load library
        # give location of dll
        mydll = windll.LoadLibrary(r"C:\Python_Karol\GIWAXS_project_01\ps10.dll")

        # open virtual serial interface (or serial interface via tcp/ip socket)
        if nComPort_Owis_motor==0: # find first connected control unit
            result7=mydll.PS10_SimpleConnect(1, b"") # ANSI/Unicode !!
        elif nComPort_Owis_motor==-1: # find the first connected control unit via tcp/ip socket (localhost, port=1200)
            result7=mydll.PS10_SimpleConnect(1, b"net") # ANSI/Unicode !!
        else: # connect control unit with defined COM port
            result7=mydll.PS10_Connect(1, 0, nComPort_Owis_motor, 9600,0,0,0,0)

        # initialize axis
        result7=mydll.PS10_MotorInit(1, nAxis_Owis_motor)

        # set target mode to absolute mode (0 - relative, 1 - absolute)
        result7=mydll.PS10_SetTargetMode(1, nAxis_Owis_motor, 0)

        # set velocity 
        if nPosF_Owis_motor > 0:
            result7=mydll.PS10_SetPosF(1, nAxis_Owis_motor, nPosF_Owis_motor)

##        # go to reference position (to start position)
##        result3=mydll.PS10_GoRef(1, nAxis_Owis_motor, 4)
##        # check move state of the axis
##        print("Axis is moving to reference position...")
##        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##        while state > 0: 
##            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
##    
##        print("Axis is in reference position.")
            
        # move relativelly to actual tilt position
        result7=mydll.PS10_MoveEx(1, nAxis_Owis_motor, c_double(tilt_target_pos), 1)
        # check move state of the axis
        print("Axis is moving to position...")
        state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        while state > 0:
            state = mydll.PS10_GetMoveState(1, nAxis_Owis_motor)
        print("Axis is in position.")
        # check position
        PS10_GetPositionEx=mydll.PS10_GetPositionEx
        PS10_GetPositionEx.restype = ctypes.c_double
        result8=PS10_GetPositionEx(1, nAxis_Owis_motor)
        print( "Position=%.3f" %(result8) )
        # display currrent position
        self.tilt_current_position.setValue(result8)

        # close interface
        result7=mydll.PS10_Disconnect(1)

        # change status in label
        self.status5.setText("Tilt motor is not moving.")
        self.status5.setWordWrap(True)

        QApplication.processEvents()

        self.tilt_minus_relative_move_button.setEnabled(True)

    def tilt_get_position(self):

        # change status in label
        self.status5.setText("Reading position - tilt motor.")
        self.status5.setWordWrap(True)

        QApplication.processEvents()
        
        # specify COM port number of Owis motor
        nComPort_Owis_motor=COM_PORT_TILT_MOTOR
        # specify axis of Owis motor
        nAxis_Owis_motor=1

        # load library
        # give location of dll
        mydll = windll.LoadLibrary(r"C:\Python_Karol\GIWAXS_project_01\ps10.dll")

        # open virtual serial interface (or serial interface via tcp/ip socket)
        if nComPort_Owis_motor==0: # find first connected control unit
            result7=mydll.PS10_SimpleConnect(1, b"") # ANSI/Unicode !!
        elif nComPort_Owis_motor==-1: # find the first connected control unit via tcp/ip socket (localhost, port=1200)
            result7=mydll.PS10_SimpleConnect(1, b"net") # ANSI/Unicode !!
        else: # connect control unit with defined COM port
            result7=mydll.PS10_Connect(1, 0, nComPort_Owis_motor, 9600,0,0,0,0)

        # initialize axis
        result7=mydll.PS10_MotorInit(1, nAxis_Owis_motor)
            
        # check position
        PS10_GetPositionEx=mydll.PS10_GetPositionEx
        PS10_GetPositionEx.restype = ctypes.c_double
        result8=PS10_GetPositionEx(1, nAxis_Owis_motor)
        print( "Position=%.3f" %(result8) )
        # display currrent position
        self.tilt_current_position.setValue(result8)

        # close interface
        result7=mydll.PS10_Disconnect(1)

        # change status in label
        self.status5.setText("Ending reading position - tilt motor.")
        self.status5.setWordWrap(True)

        QApplication.processEvents()
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIWAXS_Python_project_01")
        self.resize(1300, 650)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab1 = Tab1()
        self.tabs.addTab(self.tab1, "Single image acquisition")

        self.tab2 = Tab2(self.tab1)
        self.tabs.addTab(self.tab2, "Rocking curve - linear Z")
        
        self.tab3 = Tab3(self.tab1)
        self.tabs.addTab(self.tab3, "Rocking curve - tilt")

        self.tab4 = Tab4(self.tab1)
        self.tabs.addTab(self.tab4, "Move Z")

        self.tab5 = Tab5(self.tab1)
        self.tabs.addTab(self.tab5, "Move tilt")

    def create_tab(self, name):
        """Build a tab page with a placeholder label."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(f"Content of {name}"))
        layout.addStretch()
        return page


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

