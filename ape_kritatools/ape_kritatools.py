from krita import *
import ctypes
import os
import sys

# Get current path
dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(dir_path, "inc"))

from ape_def import lib

VERSION = "0.3.0"

class APEKritaTools(Extension):

    def __init__(self, parent):
        super().__init__(parent)
        self.file_path = None
        self.ape_instance = None
        self.buffers = []

    def setup(self):
        pass

    def load_frames(self, frame_buffer, frame_count, frames):
        """Load frames from frame buffer."""
        for i in range(0, frame_count - 1):
            frame = frame_buffer[i].contents
            width = frame.width
            height = frame.height
            channels = frame.channels
            pixel_stream = frame.pixels

            if not pixel_stream:
                self.show_message("Error", "Error: Failed to get pixel stream.")
                return

            if width <= 0 or height <= 0:
                self.show_message("Error", "Error: Image buffer is empty.")
                return

            # Convert C++ pixel buffer to python bytes
            num_pixels = width * height * channels
            pixel_data_ptr = ctypes.cast(pixel_stream, ctypes.POINTER(ctypes.c_uint8 * num_pixels))

            try:
                pixel_array = bytearray(pixel_data_ptr.contents)
            except ValueError as e:
                self.show_message("Error", f"Error: {str(e)}")
                return
            
            frames.append((width, height, channels, pixel_array))

    def frames_to_layers(self, frames, doc):
        """Convert frames to layers."""
        # Add layers to document
        for i, (width, height, channels, pixel_array) in enumerate(frames):
            node = doc.createNode(f"Frame {i}", "paintlayer")
            doc.rootNode().addChildNode(node, None)

            # Send the raw pixel data directly to Krita
            node.setPixelData(pixel_array, 0, 0, width, height)
            # Refresh to apply changes
            doc.refreshProjection()
            # Set the new layer as the active node

            doc.setActiveNode(node)

    def ape_init(self): 
        """Initialize APE."""
        # Load image from DLL
        self.ape_instance = lib.create_ape_instance()
        if not self.ape_instance:
            self.show_message("Error", "Error: Failed to create ApeCore instance.")
            return 0
        
        # Load file dialog
        ape_path = QFileDialog.getOpenFileName(None, "Open APE Image", "", "APE Image (*)")
        pal_path = QFileDialog.getOpenFileName(None, "Open APE Palette", "", "APE Palette (*.pal)")

        if not lib.load_image(self.ape_instance, ape_path[0].encode(), 1, pal_path[0].encode()):
            self.show_message("Error", "Error: Failed to load image.")
            return -1
        
        # Return success
        return 1

    def load_image_into_krita(self):
        """Load an RGBA pixel stream from pyape.dll and create a new Krita layer."""
        krita_instance = Krita.instance()

        # Initialize APE
        if not self.ape_instance:
            if self.ape_init() < 1:
                return
        
        # Get frame count
        frame_count = lib.get_frame_count(self.ape_instance)

        # Get frame data
        frame_buffer = lib.get_frame_buffer(self.ape_instance)
        frames = []

        # Load frames
        self.load_frames(frame_buffer, frame_count, frames)

        # Find the largest size
        max_width = max(frame[0] for frame in frames)
        max_height = max(frame[1] for frame in frames)
        
        doc = krita_instance.activeDocument()

        # If no document is open, create one
        if not doc:
            doc = krita_instance.createDocument(max_width, max_height, "APE Image", "RGBA", "U8", "", 300.0)
            krita_instance.activeWindow().addView(doc)

        self.frames_to_layers(frames, doc)

        # Refresh to apply changes
        doc.refreshProjection()

    def show_message(self, title, text):
        """ Show a pop-up message box. """
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

    def createActions(self, window):
        """ Register Krita menu action """
        action = window.createAction("ape_load_krita", "Load APE Image into Krita", "tools/scripts")
        action.triggered.connect(self.load_image_into_krita)