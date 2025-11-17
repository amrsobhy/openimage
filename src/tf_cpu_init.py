"""
Force TensorFlow to use CPU-only mode.

This module MUST be imported before any TensorFlow imports.
It sets environment variables to prevent CUDA initialization.

IMPORTANT: This module does NOT import TensorFlow itself to avoid
crashes during initialization. It only sets environment variables.
"""

import os

# Set comprehensive environment variables to force CPU-only mode
# These MUST be set before TensorFlow is imported anywhere in the application

# Disable GPU visibility completely
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# Suppress TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Disable GPU memory growth
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'false'

# Disable oneDNN optimizations that might try to use GPU
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Disable XLA entirely (XLA tries to initialize CUDA)
os.environ['TF_XLA_FLAGS'] = '--tf_xla_enable_xla_devices=false'

# Force TensorFlow to use CPU-only kernels
os.environ['TF_DISABLE_SEGMENT_REDUCTION_OP_DETERMINISM_EXCEPTIONS'] = '1'

# Prevent any CUDA initialization attempts
os.environ['NVIDIA_VISIBLE_DEVICES'] = ''
os.environ['NVIDIA_DRIVER_CAPABILITIES'] = ''

print("✓ CPU-only mode enforced (environment variables set)")

def configure_tensorflow_cpu():
    """
    Dummy function for backwards compatibility.
    The actual configuration is done via environment variables above.
    """
    pass
