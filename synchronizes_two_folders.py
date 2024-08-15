import argparse
import os
import shutil
import hashlib
import time
import logging
from pathlib import Path

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as file:
        while True:
            # Read a chunk of the file. Choose 1MB but it could depend on file and system 'needs'
            chunk = file.read(1048576)
            if not chunk:
                break
            hash_md5.update(chunk)

    return hash_md5.hexdigest()

def sync_folders(source, replica, logger):
    source_files = {}
    replica_files = {}

    # Source directory
    for dirpath, _, filenames in os.walk(source):
        for filename in filenames:
            src_file = Path(dirpath) / filename
            rel_path = os.path.relpath(src_file, source)
            src_md5 = calculate_md5(src_file)
            source_files[rel_path] = src_md5

    # Replica directory
    for dirpath, _, filenames in os.walk(replica):
        for filename in filenames:
            repl_file = Path(dirpath) / filename
            rel_path = os.path.relpath(repl_file, replica)
            repl_md5 = calculate_md5(repl_file)
            replica_files[rel_path] = repl_md5

    # Copy files
    for rel_path, src_md5 in source_files.items():
        replica_path = Path(replica) / rel_path
        if rel_path not in replica_files:
            logger.info(f"Copying {rel_path} to replica.")
            replica_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(source) / rel_path, replica_path)
        elif replica_files[rel_path] != src_md5:
            logger.info(f"Updating {rel_path} in replica.")
            shutil.copy2(Path(source) / rel_path, replica_path)

    # Clean up files from replica
    for rel_path in replica_files:
        if rel_path not in source_files:
            logger.info(f"Deleting {rel_path} from replica.")
            os.remove(Path(replica) / rel_path)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Synchronize two folders.")
    parser.add_argument('-s', '--source', required=True, help="Path to the source folder.")
    parser.add_argument('-r', '--replica', required=True, help="Path to the replica folder.")
    parser.add_argument('-i', '--interval', type=int, required=True, help="Synchronization interval in seconds.")
    parser.add_argument('-l', '--log', required=True, help="Path to the log file.")
    
    # Parse the command-line arguments
    args = parser.parse_args()

    source_folder = args.source
    replica_folder = args.replica
    interval = args.interval
    log_file = args.log

    # Set up logging
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
    logger = logging.getLogger()
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(console_handler)

    while True:
        logger.info("Starting synchronization.")
        sync_folders(source_folder, replica_folder, logger)
        logger.info("Synchronization complete.")
        time.sleep(interval)

if __name__ == "__main__":
    main()
