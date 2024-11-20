import os
import time
import logging
import signal
import sys
from datetime import datetime
from PIL import Image, ImageWin  # Ensure Pillow is installed and compatible

# Path to the directory to monitor (e.g., network drive)
directory_path = r"\\VBoxSvr\uploads"

# Polling interval in seconds
poll_interval = 1

# Initial set of files in the directory
initial_files = set(os.listdir(directory_path))

# Add configuration
MAX_RETRIES = 3
RETRY_DELAY = 5

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define the destination directory
OUTPUT_DIRECTORY = r"\\VBoxSvr\uploads\out"

def get_file_info(filepath):
    try:
        stats = os.stat(os.path.join(directory_path, filepath))
        return {
            'mtime': stats.st_mtime,
            'size': stats.st_size
        }
    except OSError as e:
        logging.error("Error getting file info for {0}: {1}".format(filepath, e))
        return None

def print_image(image):
    try:
        # Save the image to a temporary file
        temp_file = os.path.join(directory_path, "temp_print_image.bmp")
        image.save(temp_file, "BMP")

        # Use the Windows command line to print the image
        os.system('rundll32.exe C:\\WINDOWS\\system32\\shimgvw.dll,ImageView_PrintTo /pt "{0}" "Printer"'.format(temp_file))

        # Remove the temporary file
        os.remove(temp_file)
        logging.info("Printed image successfully")
    except Exception as e:
        logging.error("Error printing image: {0}".format(e))

def check_new_files():
    global initial_files

    try:
        current_files = set(os.listdir(directory_path))
    except OSError as e:
        logging.error("Error accessing directory {0}: {1}".format(directory_path, e))
        return

    new_files = current_files - initial_files

    if new_files:
        for file in new_files:
            # Wait for file to be completely written
            file_info = None
            for _ in range(MAX_RETRIES):
                file_info = get_file_info(file)
                if file_info:
                    time.sleep(1)  # Brief pause
                    new_info = get_file_info(file)
                    if new_info and new_info['size'] == file_info['size']:
                        break
                time.sleep(RETRY_DELAY)

            if file_info:
                source_path = os.path.join(directory_path, file)
                try:
                    # Check if the file is an image
                    if file.lower().endswith(('.jpg')):
                        img = Image.open(source_path)
                        print_image(img)
                        # Close the image
                        img.close()
                    else:
                        logging.warning("File {0} is not an image, skipping processing.".format(file))
                except Exception as e:
                    logging.error("Error processing image {0}: {1}".format(file, e))
                dest_path = os.path.join(OUTPUT_DIRECTORY, file)
                if os.path.exists(dest_path):
                    logging.warning("File {0} already exists in the destination directory, discarding.".format(file))
                    os.remove(source_path)
                else:
                    try:
                        os.rename(source_path, dest_path)
                        logging.info("Moved file: {0} to {1}".format(file, OUTPUT_DIRECTORY))
                    except OSError as e:
                        logging.error("Error moving file {0}: {1}".format(file, e))
                    finally:
                        # Update initial_files regardless of move success
                        if file in initial_files:
                            initial_files.remove(file)
            else:
                logging.warning("Could not process file: {0}".format(file))

    # Update initial_files to only include files that still exist
    initial_files = set(f for f in initial_files if os.path.exists(os.path.join(directory_path, f)))

def signal_handler(signum, frame):
    logging.info("Stopping file monitoring...")
    sys.exit(0)

# Main loop with signal handling
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logging.info("Starting file monitoring in {0}".format(directory_path))

    while True:
        try:
            check_new_files()
            time.sleep(poll_interval)
        except Exception as e:
            logging.error("Unexpected error: {0}".format(e))
            time.sleep(RETRY_DELAY)