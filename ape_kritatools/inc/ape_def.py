import os
import ctypes

# This module is used to interface with the C++ APECore library.
# version: 0.1.0

# Get current path
current_path = os.path.dirname(os.path.abspath(__file__))
dll_path = os.path.join(current_path, "pyape.dll")

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
