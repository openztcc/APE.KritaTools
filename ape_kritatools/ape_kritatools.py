from krita import *
import ctypes
import os

VERSION = "0.1.0"

# Get current path
current_path = os.path.dirname(os.path.abspath(__file__))
dll_path = os.path.join(current_path, "inc", "pyape.dll")

# Load the DLL
lib = ctypes.CDLL(os.path.join(dll_path))

# --------------------------- Define the function signatures ---------------------------

# Define create function
lib.create_ape_instance.argtypes = []
lib.create_ape_instance.restype = ctypes.c_void_p  # ptr to ApeCore

# Define the destroy function
lib.destroy_ape_instance.argtypes = [ctypes.c_void_p]
lib.destroy_ape_instance.restype = None

# Define load_image function (char* argument needs proper conversion)
lib.load_image.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p]
lib.load_image.restype = ctypes.c_int

# Define get_frame_buffer_size function
lib.get_frame_count.argtypes = [ctypes.c_void_p]
lib.get_frame_count.restype = ctypes.c_int

# Define OutputBuffer struct
class OutputBuffer(ctypes.Structure):
    _fields_ = [
        ("pixels", ctypes.POINTER(ctypes.c_uint8)),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("channels", ctypes.c_int)
    ]

# Define get_frame_buffer function (array of structs)
lib.get_frame_buffer.argtypes = [ctypes.c_void_p]
lib.get_frame_buffer.restype = ctypes.POINTER(ctypes.POINTER(OutputBuffer))

# Define frame width function
lib.get_frame_buffer_width.argtypes = [ctypes.POINTER(OutputBuffer)]
lib.get_frame_buffer_width.restype = ctypes.c_int

# Define frame height function
lib.get_frame_buffer_height.argtypes = [ctypes.POINTER(OutputBuffer)]
lib.get_frame_buffer_height.restype = ctypes.c_int

# Get frame
lib.get_frame.argtypes = [ctypes.c_void_p, ctypes.c_int]
lib.get_frame.restype = ctypes.POINTER(OutputBuffer)

# Get pixel stream
lib.get_frame_stream.argtypes = [ctypes.POINTER(OutputBuffer)]
lib.get_frame_stream.restype = ctypes.POINTER(ctypes.c_uint8)

class APEKritaTools(Extension):

    def __init__(self, parent):
        super().__init__(parent)
        self.file_path = None
        self.ape_instance = None
        self.buffers = []

    def setup(self):
        pass

    def load_image_into_krita(self):
        """Load an RGBA pixel stream from pyape.dll and create a new Krita layer."""
        krita_instance = Krita.instance()
        doc = krita_instance.activeDocument()

        # If no document is open, create one
        if not doc:
            doc = krita_instance.createDocument(512, 512, "APE Image", "RGBA", "U8", "", 300.0)
            krita_instance.activeWindow().addView(doc)

        node = doc.createNode("APE Layer", "paintlayer")
        doc.rootNode().addChildNode(node, None)
        doc.setActiveNode(node)

        # Load image from DLL
        self.ape_instance = lib.create_ape_instance()
        if not self.ape_instance:
            self.show_message("Error", "Error: Failed to create ApeCore instance.")
            return
        
        # Load file dialog
        ape_path = QFileDialog.getOpenFileName(None, "Open APE Image", "", "APE Image (*)")
        pal_path = QFileDialog.getOpenFileName(None, "Open APE Palette", "", "APE Palette (*.pal)")

        if not lib.load_image(self.ape_instance, ape_path[0].encode(), 0, pal_path[0].encode()):
            self.show_message("Error", "Error: Failed to load image.")
            return

        # Get buffers
        frame_buffer = lib.get_frame_buffer(self.ape_instance)
        frame = frame_buffer[0].contents
        width = frame.width
        height = frame.height
        channels = frame.channels
        pixel_stream = frame.pixels

        if not pixel_stream:
            self.show_message("Error", "Error: Failed to get pixel stream.")
            return

        self.show_message("Frame Size", "Frame size: {}x{}".format(width, height) + 
                                                "\nChannels: {}".format(channels))

        if width == 0 or height == 0:
            self.show_message("Error", "Error: Image buffer is empty.")
            return
        
        num_pixels = width * height * channels
        pixel_data = ctypes.cast(pixel_stream, ctypes.POINTER(ctypes.c_uint8 * num_pixels)).contents

        # Convert pixel data to a bytearray
        try:
            pixel_array = bytearray(pixel_data)
        except ValueError as e:
            self.show_message("Error", f"Error: {str(e)}")
            return

        # Convert to QImage (RGBA format)
        qimage = QImage(pixel_array, width, height, QImage.Format_RGBA8888)

        if qimage.isNull():
            self.show_message("Error", "Error: Failed to convert pixel data to QImage.")
            return
        
        # convert QImage to bytes
        qimage_bytes = qimage.bits().asarray(width * height * channels)

        if not qimage_bytes:
            self.show_message("Error", "Error: Failed to convert QImage to bytes.")
            return
        
        # convert to bytearray
        qimage_bytearray = bytearray(qimage_bytes)

        # Set pixel data into Krita
        node.setPixelData(qimage_bytearray, 0, 0, width, height)

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