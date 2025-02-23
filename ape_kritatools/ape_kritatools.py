# APE.Krita Tools
# by Eric Galvan (Goosifer.IO)
# https://github.com/openztcc/APE.KritaTools
# Licensed under MIT (see bottom of file)
#
# A Krita extension for importing Zoo Tycoon 1 graphics
#
# version: 1.1.1

from krita import *
import ctypes
import os
import sys

# Get current path
dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(dir_path, "inc"))

from pyape import ape
# from ape_ui import ApeUi as ui

VERSION = "1.1.1"

class APEKritaTools(Extension):

    def __init__(self, parent):
        super().__init__(parent)
        self.file_path = None
        self.pal_path = None
        self.embedded_pal_path = None
        self.ape_instance = None
        self.buffers = []
        self.frame_count = 0
        # flags
        self.graphic_error = False
        self.pal_error = False
        self.load_bg_frame_only = False
        self.has_bg_frame = False
        self.import_with_alpha_bg = True
        self.bounding_box = {"w": 0, "h": 0}
        self.krita = None

    def setup(self):
        pass

    # ------------------------------------- APE Functions ------------------------------------- #

    def load_frames(self, frame_buffer, frame_count, frames):
        """Load frames from frame buffer."""
        for i in range(0, frame_count):
            frame = frame_buffer[i].contents
            width = frame.width
            height = frame.height
            offsetX = frame.offsetX
            offsetY = frame.offsetY
            channels = frame.channels
            pixel_stream = frame.pixels

            if not pixel_stream:
                self.show_message("Error", "Error: Failed to get pixel stream.")
                return

            if width <= 0 or height <= 0:
                self.show_message("Error", "Error: Image buffer is empty.")
                return

            num_pixels = width * height * channels

            # Convert C++ pixel stream to Python bytearray
            pixel_data_ptr = ctypes.cast(pixel_stream, ctypes.POINTER(ctypes.c_uint8 * num_pixels))
            pixel_array = bytearray(pixel_data_ptr.contents)

            if channels == 4:
                for p in range(0, num_pixels, 4):
                    pixel_array[p], pixel_array[p + 2] = pixel_array[p + 2], pixel_array[p]

            frames.append((width, height, offsetX, offsetY, channels, pixel_array))
        
        # Find the true pivot (smallest x and y)
        pivot_x = min(frame[2] for frame in frames)  # Smallest offsetX
        pivot_y = min(frame[3] for frame in frames)  # Smallest offsetY

        # Adjust bounding box
        bounding_box_width = max(frame[0] + (frame[2] - pivot_x) for frame in frames)
        bounding_box_height = max(frame[1] + (frame[3] - pivot_y) for frame in frames)

        # Update bounding box
        self.bounding_box["w"] = bounding_box_width
        self.bounding_box["h"] = bounding_box_height

        # update frame count
        self.frame_count = frame_count



    def frames_to_layers(self, frames, doc):
        """Convert frames to layers."""

        # reverse frames to load in correct order
        frames.reverse()

        # if bg frame, move it to the front
        if self.has_bg_frame:
            # bg frame is last frame
            bg_frame = frames[0]
            frames = frames[1:]
            frames.insert(0, bg_frame)

        # if bg frame only, only load the last frame
        if self.load_bg_frame_only and self.has_bg_frame:
            frames = [frames[0]]
        elif self.load_bg_frame_only and not self.has_bg_frame:
            self.show_message("Error", "Error: No background frame found. Loading all frames.")

        # Remove default layer
        if doc.rootNode().childNodes():
            first_layer = doc.rootNode().childNodes()[0]
            if first_layer.name() == "Background" or first_layer.pixelData(0, 0, 1, 1) == b'\x00\x00\x00\x00':
                doc.rootNode().removeChildNode(first_layer)

        # create group for animations
        group_layer = doc.createGroupLayer("Animation")
        doc.rootNode().addChildNode(group_layer, None)

        # get document size
        canvas_width = doc.width()
        canvas_height = doc.height()

        anchorX = None
        anchorY = None

        for i, (width, height, offsetX, offsetY, channels, pixel_array) in enumerate(frames):
            print(f"Processing frame {i}/{len(frames)-1}")  # Debugging

            # Create and add the frame layer
            frame_node = doc.createNode(f"Frame {i}", "paintlayer")
            
            if not self.import_with_alpha_bg:
                # create background layer
                bg_node = doc.createNode(f"Background {i}", "paintlayer")

                # add background layer above frame
                doc.rootNode().addChildNode(bg_node, None)

                # fill background with magenta to doc size
                bg_color = bytearray([255, 0, 255, 255] * canvas_width * canvas_height)
                bg_node.setPixelData(bg_color, 0, 0, canvas_width, canvas_height) 
                # add frame to background
                doc.rootNode().addChildNode(frame_node, bg_node)

            else:
                if i == 0:
                    doc.rootNode().addChildNode(frame_node, None)
                else:
                    group_layer.addChildNode(frame_node, None)

            # Set frame size
            frame_node.setPixelData(pixel_array, 0, 0, width, height)
            
            # if bg frame or first frame, center it
            if i == 0:
                # Center first frame
                anchorX = (canvas_width // 2) - (width // 2)
                anchorY = (canvas_height // 2) - (height // 2)
                
                first_offsetX = offsetX + anchorX
                first_offsetY = offsetY + anchorY

                # Move first frame directly
                frame_node.move(anchorX, anchorY)
            else:
                # Reset origin frame
                frame_node.move(anchorX, anchorY)
                # Apply relative offset
                frame_node.move(-(offsetX - first_offsetX), -(offsetY - first_offsetY))

            if not self.import_with_alpha_bg:
                # make frame the active node
                doc.setActiveNode(frame_node)

                # Merge down the frame to the background
                frame_node.mergeDown()

                # make background the active node
                doc.setActiveNode(bg_node)

            # Refresh document
            doc.refreshProjection()

        # Initialize bounding box
        self.update_bounds(doc, canvas_width, canvas_height)
        self.import_with_alpha_bg = True
        doc.refreshProjection()

    def update_bounds(self, doc, canvas_width=1024, canvas_height=1024):
        # Initialize bounding box extremes
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')

        # Iterate over all layers to find the extreme positions
        for layer in doc.rootNode().childNodes():
            bounds = layer.bounds()
            x, y = bounds.x(), bounds.y()
            width, height = bounds.width(), bounds.height()

            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + width)
            max_y = max(max_y, y + height)

        # Compute the new bounding box size
        new_width = max_x - min_x
        new_height = max_y - min_y

        # Update bounding box
        self.bounding_box["w"] = int(new_width)
        self.bounding_box["h"] = int(new_height)

        # Update offsets to center
        offsetX = (canvas_width // 2) - (new_width // 2)
        offsetY = (canvas_height // 2) - (new_height // 2)

        doc.resizeImage(offsetX, offsetY, self.bounding_box["w"], self.bounding_box["h"])

    def ape_init(self): 
        """Initialize APE."""
        # Load image from DLL
        self.ape_instance = ape.create_ape_instance()
        if not self.ape_instance:
            self.show_message("Error", "Error: Failed to create ApeCore instance.")
            return 0
        
        # Return success
        return 1

    def load_image_into_krita(self, graphic_path, pal_path, load_bg_frame_only=None, import_alpha=None):
        """Load an RGBA pixel stream from pyape.dll and create a new Krita layer."""
        self.krita = Krita.instance()

        # Initialize APE
        if not self.ape_instance:
            if self.ape_init() < 1:
                return

        # Load image
        if not ape.load_image(self.ape_instance, graphic_path.encode(), 1, pal_path.encode()):
            self.show_message("Error", "Error: Failed to load image.")
            return -1
        
        # Does the image have a background frame?
        self.has_bg_frame = ape.has_background_frame(graphic_path.encode())
        
        # Get frame count
        frame_count = ape.get_frame_count(self.ape_instance)

        # Get frame data
        frame_buffer = ape.get_frame_buffer(self.ape_instance)
        frames = []

        # Load frames
        self.load_frames(frame_buffer, frame_count, frames)

        # Find the largest size
        # max_width = max(frame[0] for frame in frames)
        # max_height = max(frame[1] for frame in frames)
        
        doc = self.krita.createDocument(self.bounding_box["w"], self.bounding_box["h"], "Untitled", "RGBA", "U8", "", 300.0)
        self.krita.activeWindow().addView(doc)

        # # If no document is open, create one
        # if not doc:
        #     doc = krita_instance.createDocument(max_width, max_height, "APE Image", "RGBA", "U8", "", 300.0)
        #     krita_instance.activeWindow().addView(doc)

        self.frames_to_layers(frames, doc)
        app = Krita.instance()
        doc = app.activeDocument()

        # Refresh to apply changes
        doc.refreshProjection()

        # Clean up APE
        # self.ape_cleanup()

    def show_message(self, title, text):
        """ Show a pop-up message box. """
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

    # ------------------------------------- Dialog --------------------------------------------- #
    def open_dialog(self):
        """Open dialog."""
        # static variables
        widget_height = 25
        text_field_width = 460
        button_width = 100
        form_width = text_field_width + button_width + 10
        form_height = 350

        # Create pop-up dialog
        ape_win = QDialog()
        ape_win.setWindowTitle("APE Krita Tools v" + VERSION)
        ape_win.setMinimumSize(form_width, form_height)
        ape_win.setMaximumSize(form_width, form_height)

        # Create layout
        root = QVBoxLayout()
        ape_win.setLayout(root)

        # Open Button Form
        open_form = QVBoxLayout()
        root.addLayout(open_form)
        # ----- Open Label
        open_msg = QLabel("Open APE Graphic")
        open_form.addWidget(open_msg)
        # ----- Textfield + Button
        open_sub_row = QHBoxLayout()
        open_form.addLayout(open_sub_row)
        # ------------- Textfield
        open_text = QLineEdit()
        open_text.setMinimumSize(text_field_width, widget_height)
        open_text.setMaximumSize(text_field_width, widget_height)
        open_sub_row.addWidget(open_text)
        # ------------- Button
        open_button = QPushButton("Open")
        open_button.setMinimumSize(button_width, widget_height)
        open_button.setMaximumSize(button_width, widget_height)
        open_sub_row.addWidget(open_button)
        # ----- Connect button to function
        open_button.clicked.connect(lambda: self.open_file("Open APE Image", "APE Image (*)", open_text))
        open_text.setText(self.file_path)
        # ------------- Error Label
        open_error = QLabel("Not a valid APE file.")
        open_error.setStyleSheet("color: red")
        open_error.setVisible(False)
        open_form.addWidget(open_error)

        # ------------------------------------- #

        # Open Palette Form
        open_pal_form = QVBoxLayout()
        root.addLayout(open_pal_form)
        # ----- Open Label
        open_pal_msg = QLabel("Open APE Palette")
        open_pal_form.addWidget(open_pal_msg)
        # ----- Textfield + Button
        open_pal_sub_row = QHBoxLayout()
        open_pal_form.addLayout(open_pal_sub_row)
        # ------------- Textfield
        open_pal_text = QLineEdit()
        open_pal_text.setMinimumSize(text_field_width, widget_height)
        open_pal_text.setMaximumSize(text_field_width, widget_height)
        open_pal_text.setDisabled(True)
        open_pal_sub_row.addWidget(open_pal_text)
        # ------------- Button
        open_pal_button = QPushButton("Open")
        open_pal_button.setMinimumSize(button_width, widget_height)
        open_pal_button.setMaximumSize(button_width, widget_height) 
        open_pal_button.setDisabled(True)
        open_pal_sub_row.addWidget(open_pal_button)
        # ------------- Enable checkbox
        open_pal_checkbox = QCheckBox("Use Embedded Palette")
        open_pal_checkbox.setChecked(True)
        open_pal_form.addWidget(open_pal_checkbox)
        # ----- Connect checkbox to function
        open_pal_checkbox.stateChanged.connect(lambda: self.enable_forms(open_pal_text, open_pal_button, open_pal_checkbox.checkState()))
        # ----- Connect button to function
        open_pal_button.clicked.connect(lambda: self.open_file("Open APE Palette", "APE Palette (*.pal)", open_pal_text))
        # ------------- Error Label
        open_pal_error = QLabel("Not a valid APE palette. (Or palette not found)")
        open_pal_error.setStyleSheet("color: red")
        open_pal_error.setVisible(False)
        open_pal_form.addWidget(open_pal_error)

        # ------------- State checks
        open_pal_text.textChanged.connect(lambda: self.validate_file(open_pal_text.text(), "palette", open_pal_error, None, import_button))
        open_pal_text.textChanged.connect(lambda: self.update_import_button_state(import_button))
        open_text.textChanged.connect(lambda: self.validate_file(open_text.text(), "graphic", open_error, open_pal_text, import_button))
        open_text.textChanged.connect(lambda: self.update_import_button_state(import_button))

        # ------------------------------------- #

        # Settings Panel
        settings_panel = QWidget()
        settings_panel.setObjectName("settings_panel")
        settings_panel.setStyleSheet("""
            #settings_panel { 
                border: 1px solid rgb(51, 51, 51); 
                padding: 5px;
                border-radius: 5px;
                background-color: rgb(70, 70, 70);
            }
        """)
        # ----- Create settings layout
        settings_form = QVBoxLayout(settings_panel)
        root.addWidget(settings_panel)

        # ----- Settings Label
        settings_msg = QLabel("Settings")
        settings_form.addWidget(settings_msg)
        # ----- Load only background frame checkbox
        load_bg_checkbox = QCheckBox("Load only background frame")
        load_bg_checkbox.setChecked(False)
        settings_form.addWidget(load_bg_checkbox)
        # ----- Import with alpha checkbox
        import_alpha_checkbox = QCheckBox("Import with alpha background")
        import_alpha_checkbox.setChecked(True)
        # ----- Add border to settings panel
        settings_form.addWidget(import_alpha_checkbox)
        # ----- Connect checkboxes to functions
        load_bg_checkbox.stateChanged.connect(lambda: self.bg_frame_only_triggered(load_bg_checkbox.checkState()))
        import_alpha_checkbox.stateChanged.connect(lambda: self.import_alpha_triggered(import_alpha_checkbox.checkState()))
        # ----- Spacer
        settings_form.addStretch()

        # Import/Cancel Form
        import_form = QHBoxLayout()
        root.addLayout(import_form)
        # ----- Spacer
        import_form.addStretch()
        # ----- Import Button
        import_button = QPushButton("Import")
        import_button.setMinimumSize(button_width, widget_height)
        import_button.setMaximumSize(button_width, widget_height)
        import_button.setDisabled(True)
        import_form.addWidget(import_button)
        # ----- Connect button to function
        import_button.clicked.connect(lambda: self.import_triggered(open_text.text(), open_pal_text.text(), load_bg_checkbox.isChecked(), import_alpha_checkbox.isChecked()))
        # ----- Cancel Button
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumSize(button_width, widget_height)
        cancel_button.setMaximumSize(button_width, widget_height)
        import_form.addWidget(cancel_button)
        cancel_button.clicked.connect(ape_win.close)
        # ------------------------------------- #
        # ------------------------------------- #

        # Set margins and spacing
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)
                
        # Show dialog
        ape_win.exec_()
    
    # ------------------------------------- Event Handlers ------------------------------------- #

    def update_import_button_state(self, import_button):
        """Update import button state based on both error flags."""
        if import_button:
            has_any_error = self.graphic_error # or self.pal_error
            import_button.setDisabled(has_any_error)

    def enable_forms(self, textfield, button, state):
        """Enable or disable forms."""
        if state == Qt.Checked:
            textfield.setDisabled(True)
            if self.embedded_pal_path:
                textfield.setText(self.embedded_pal_path)
            button.setDisabled(True)
        else:
            textfield.setDisabled(False)
            button.setDisabled(False)
    
    def open_file(self, title, type_filter, text_field):
        path = QFileDialog.getOpenFileName(None, title, "", type_filter)
        if path[0]:
            text_field.setText(path[0])
        else:
            text_field.setText("")

    def validate_file(self, file_path, file_type, widget, widget2=None, import_button=None):
        """Validate file."""
        if not os.path.isfile(file_path):
            widget.setVisible(True)
            return False
        
        if file_type == "graphic":
            if not ape.validate_graphic_file(file_path.encode()):
                self.graphic_error = True
                widget.setVisible(True)
                self.update_import_button_state(import_button)
                return False
            else:
                self.graphic_error = False
                if widget2:
                    header = ape.get_header(file_path.encode())
                    if header:
                        pal_path = header.palName
                        widget2.setText(self.adjust_pal_directory(pal_path, file_path))
                        self.embedded_pal_path = pal_path.decode()
        elif file_type == "palette":
            if not ape.validate_palette_file(file_path.encode()):
                self.pal_error = True
                widget.setVisible(True)
                self.update_import_button_state(import_button)
                return False
            else:
                self.pal_error = False
        
        widget.setVisible(False)
        return True

    # ------------------------------------- Helpers --------------------------------------------- #

    def adjust_pal_directory(self, pal_path, graphic_path):
        """Adjust palette path by finding common path components and appending the palette file."""
        # Decode bytes if necessary
        if isinstance(pal_path, bytes):
            pal_path = pal_path.decode("utf-8")
        if isinstance(graphic_path, bytes):
            graphic_path = graphic_path.decode("utf-8")
        
        # Normalize slashes and get directory parts
        pal_parts = pal_path.replace("\\", "/").split("/")
        graphic_path = graphic_path.replace("\\", "/")
        graphic_parts = graphic_path.split("/")
        # pal_filename = pal_parts[-1]
        
        # Find the last matching path component
        last_match_index = -1
        for pal_part in pal_parts[:-1]:  # Exclude pal filename
            for i, graphic_part in enumerate(graphic_parts):
                if pal_part.lower() == graphic_part.lower():
                    last_match_index = i
        
        if last_match_index != -1:
            # Take the graphic path up to the last matching component
            base_path = "/".join(graphic_parts[:last_match_index + 1])
            # Get the pal filename
            pal_filename = pal_parts[-1]
            # Join them together
            return f"{base_path}/{pal_filename}"
        else:
            # If no common path components, just return the pal, return graphic path
            # without filename and append pal filename
            new_pal_path = "/".join(graphic_parts[:-1]) + "/" + "/".join(pal_parts)
            return new_pal_path
        
        return pal_path    
    
    def import_triggered(self, graphic_path, pal_path, load_bg_frame_only, import_alpha):
        """Import button triggered."""
        if not graphic_path or not pal_path:
            self.show_message("Error", "Error: Graphic or palette path is empty.")
            return
        
        if not os.path.isfile(graphic_path):
            self.show_message("Error", "Error: Graphic file not found.")
            return
        
        if not os.path.isfile(pal_path):
            self.show_message("Error", "Error: Palette file not found.")
            return
        
        if self.pal_error or self.graphic_error:
            self.show_message("Error", "Error: Invalid graphic or palette file.")
            return
        
        # Load image into Krita
        self.load_image_into_krita(graphic_path, pal_path, load_bg_frame_only, import_alpha)
        

        # Close dialog
        QApplication.activeWindow().close()
        QTimer.singleShot(500, lambda: self.runAfterExit(self.frame_count, graphic_path))


    def bg_frame_only_triggered(self, state):
        """Background frame only checkbox triggered."""
        self.load_bg_frame_only = state

    def import_alpha_triggered(self, state):
        """Import with alpha checkbox triggered."""
        self.import_with_alpha_bg = state

    def runAfterExit(self, frames, file_path):
        """Convert group layer to timeline."""
        doc = Krita.instance().activeDocument()

        if self.has_bg_frame:
            # move bg frame to the back
            bg_frame = doc.nodeByName("Frame 0")
            # Rename bg frame
            bg_frame.setName("Background")

        group_layer = doc.nodeByName("Animation")
        doc.setActiveNode(group_layer)
        Krita.instance().action("convert_group_to_animated").trigger()
        Krita.instance().action("move_layer_up").trigger()

        # Update fps
        header = ape.get_header(file_path.encode())
        if header:
            ms = header.speed
        fps = 1000 / ms # original speed is ms per frame
        doc.setFramesPerSecond(fps)
        doc.setFullClipRangeEndTime(self.frame_count - 1)

        # Hit play
        Krita.instance().action("toggle_playback").trigger()

        
    # ------------------------------------- Krita Extension ------------------------------------- #
        
    def createActions(self, window):
        """ Register Krita menu action """
        action = window.createAction("ape_load_krita", "Load APE Image into Krita", "tools/scripts")
        # action.triggered.connect(self.load_image_into_krita)
        # Open dialog
        action.triggered.connect(self.open_dialog)

# MIT License

# Copyright (c) 2025 Eric Galvan (Goosifer.IO)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.    