"""
Force TensorFlow to use CPU-only mode.

This module MUST be imported before any TensorFlow imports.
It sets environment variables and configures TensorFlow to prevent CUDA initialization.
"""

import os

# Set environment variables BEFORE any TensorFlow imports
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'false'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Additional flag to prevent XLA from trying to use CUDA
os.environ['TF_XLA_FLAGS'] = '--tf_xla_enable_xla_devices=false'

def configure_tensorflow_cpu():
    """
    Explicitly configure TensorFlow to use CPU only.
    This function should be called before any DeepFace operations.
    """
    try:
        import tensorflow as tf

        # Disable all GPUs
        tf.config.set_visible_devices([], 'GPU')

        # Set memory growth to False (already disabled by env var but being explicit)
        physical_devices = tf.config.list_physical_devices('CPU')
        print(f"✓ TensorFlow configured for CPU-only mode ({len(physical_devices)} CPU devices)")

    except ImportError:
        # TensorFlow not installed, which is fine
        pass
    except Exception as e:
        print(f"⚠ Warning: Could not configure TensorFlow: {e}")


# Configure immediately on import
configure_tensorflow_cpu()
