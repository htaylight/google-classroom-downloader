import os
import pickle
import re
import logging
from tqdm import tqdm
import time
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

# Constants for paths and scopes
TOKEN_PATH = os.getenv('TOKEN_PATH', 'token.pickle')
CREDS_PATH = os.getenv('CREDS_PATH', 'credentials.json')
DOWNLOAD_PATH = os.path.join(os.path.expanduser('~'), 'Downloads')

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly',
    'https://www.googleapis.com/auth/classroom.topics.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Set up logging to both file and console
logging.basicConfig(
    level=logging.INFO,  # Set the logging level
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download.log', encoding='utf-8', mode='w'),  # Log to file with UTF-8 encoding
        logging.StreamHandler()  # Log to console
    ]
)


# # Suppress specific logging messages
# logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


def get_credentials():
    """
    Obtain OAuth2 credentials for accessing Google APIs.

    Returns:
        creds (google.auth.credentials.Credentials): The authenticated credentials.
    """
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    return creds


def extract_file_id_from_input(input_str):
    """
    Extract file or folder ID from a Google Drive URL or direct input.

    Args:
        input_str (str): The Google Drive URL or ID.

    Returns:
        str: The extracted file ID or None if not found.
    """
    patterns = [r'/d/([a-zA-Z0-9_-]+)', r'/folders/([a-zA-Z0-9_-]+)', r'^([a-zA-Z0-9_-]{25,})$']
    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)
    return None


def download_file(drive_service, file_id, file_path, failed_downloads):
    """
    Download a single file from Google Drive.

    Args:
        drive_service (googleapiclient.discovery.Resource): The Drive API service instance.
        file_id (str): The ID of the file to download.
        file_path (str): The local file path where the file will be saved.
        failed_downloads (list): List to track failed downloads.

    Returns:
        bool: True if the download is successful, False otherwise.
    """
    try:
        # Check if the file already exists
        if os.path.exists(file_path):
            logging.info(f"File {file_path} already exists. Skipping download.\n")
            return True

        request = drive_service.files().get(fileId=file_id, fields='name, mimeType').execute()
        mime_type = request['mimeType']

        # Handle Google Docs files by exporting them in appropriate formats
        if mime_type.startswith('application/vnd.google-apps.'):
            export_formats = {
                'application/vnd.google-apps.document': 'application/pdf',
                'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument'
                                                           '.spreadsheetml.sheet',
                'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument'
                                                            '.presentationml.presentation'
            }

            export_mime_type = export_formats.get(mime_type)
            if export_mime_type:
                export_request = drive_service.files().export_media(fileId=file_id, mimeType=export_mime_type)
                file_extension = export_mime_type.split('/')[-1].replace('vnd.', '')
                file_path = f"{file_path}.{file_extension}"
            else:
                logging.warning(f"Cannot download this Google Docs file: {file_path}\n")
                failed_downloads.append((file_path, f"Cannot download this file type: {mime_type}"))
                return False
        else:
            export_request = drive_service.files().get_media(fileId=file_id)

        # Download the file with a progress bar
        logging.info(f"Downloading: {request['name']}")
        with open(file_path, 'wb') as file:
            downloader = MediaIoBaseDownload(file, export_request)
            done = False
            with tqdm(total=100, desc=f"{request['name']}", unit='%') as pbar:
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        pbar.update(progress - pbar.n)
        logging.info(f'File downloaded to {file_path}\n')
        return True

    except Exception as e:
        logging.error(f'An error occurred while downloading the file: {e}\n')
        failed_downloads.append((file_path, str(e)))
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Deleted the failed download: {file_path}\n")
        return False


def download_recursive(drive_service, current_file_id, current_folder, summary_dict=None):
    """
    Recursively download files and folders from Google Drive.

    Args:
        drive_service (googleapiclient.discovery.Resource): The Drive API service instance.
        current_file_id (str): The ID of the current file or folder to download.
        current_folder (str): The local folder path where the files will be saved.
        summary_dict (dict): A dictionary to track download summary.

    Returns:
        dict: Updated summary dictionary with counts of folders, files, and failed downloads.
    """

    if summary_dict is None:
        summary_dict = {
            'total_folders': 0,
            'total_files': 0,
            'failed_downloads': [],
        }

    file_name = None  # Initialize file_name variable

    try:
        # Fetch file metadata to determine if it's a file or a folder
        request = drive_service.files().get(fileId=current_file_id, fields='id, name, mimeType').execute()
        file_name = request['name']
        mime_type = request['mimeType']

        # Check if it's a folder
        if mime_type == 'application/vnd.google-apps.folder':
            # If it's a folder, create a local folder and list all its contents
            folder_path = os.path.join(current_folder.strip(), file_name.strip())
            os.makedirs(folder_path, exist_ok=True)
            logging.info(f"Folder path: {folder_path}\n")

            # Count this folder
            summary_dict['total_folders'] += 1

            # Initialize page token for pagination
            page_token = None

            while True:
                # List contents of the folder
                query = f"'{current_file_id}' in parents"
                results = drive_service.files().list(
                    q=query,
                    fields='nextPageToken, files(id, name, mimeType)',
                    pageToken=page_token
                ).execute()
                items = results.get('files', [])

                # Recursively download each item in the folder
                for item in items:
                    download_recursive(drive_service, item['id'], folder_path, summary_dict)

                # Check if there is another page of results
                page_token = results.get('nextPageToken', None)
                if not page_token:
                    break
        else:
            # If it's a file, download it
            file_path = os.path.join(current_folder.strip(), file_name.strip())
            if download_file(drive_service, current_file_id, file_path, summary_dict['failed_downloads']):
                summary_dict['total_files'] += 1

    except HttpError as error:
        logging.error(f'An error occurred: {error}\n')
        if file_name:
            summary_dict['failed_downloads'].append((file_name, str(error)))
        else:
            summary_dict['failed_downloads'].append((f'File ID: {current_file_id}', str(error)))

    return summary_dict


def download_google_drive_files(drive_service, root_file_id, root_folder):
    """
    Download files and folders from Google Drive.

    Args:
        drive_service (googleapiclient.discovery.Resource): The Drive API service instance.
        root_file_id (str): The ID of the root folder or file to download.
        root_folder (str): The local root folder path where the files will be saved.
    """
    try:
        # Create the root folder
        os.makedirs(root_folder, exist_ok=True)

        # Start the download process
        drive_summary = download_recursive(drive_service, root_file_id, root_folder)

        # Exclude the root folder from the count
        if drive_summary['total_folders'] >= 1:
            drive_summary['total_folders'] -= 1

        # Print download summary for Google Drive
        name = drive_service.files().get(fileId=root_file_id, fields='name').execute().get('name', '')
        logging.info(f"Google Drive Download Summary: {name}")
        logging.info(f"Total downloaded folders: {drive_summary['total_folders']}")
        logging.info(f"Total downloaded files: {drive_summary['total_files']}")
        logging.info(f"Total failed downloads: {len(drive_summary['failed_downloads'])}\n")
        if drive_summary['failed_downloads']:
            logging.error("Failed Downloads Details:")
            for fail in drive_summary['failed_downloads']:
                logging.error(f"File: {fail[0]}, Reason: {fail[1]}\n")

    except Exception as e:
        logging.error(f'An error occurred: {e}\n')


def list_courses(classroom_service):
    """
    Fetch and list all Google Classroom courses.

    Args:
        classroom_service (googleapiclient.discovery.Resource): The Classroom API service instance.

    Returns:
        list: A list of dictionaries containing course names and IDs.
    """
    try:
        courses = []
        page_token = None

        while True:
            results = classroom_service.courses().list(pageSize=100, pageToken=page_token).execute()
            courses.extend(results.get('courses', []))
            page_token = results.get('nextPageToken', None)

            if not page_token:
                break

        return [{'name': course['name'], 'id': course['id']} for course in courses]

    except HttpError as error:
        logging.error(f'An error occurred: {error}\n')
        return []


def get_course_materials(service, course_id):
    """
    Retrieves materials for a specific course using the Google Classroom API.

    Args:
        service (Resource): The Classroom API service instance.
        course_id (str): The ID of the course.

    Returns:
        list: A list of course materials. Returns an empty list if none are found or on error.
    """
    try:
        materials_response = service.courses().courseWorkMaterials().list(courseId=course_id).execute()
        materials = materials_response.get('courseWorkMaterial', [])
        return materials
    except Exception as e:
        logging.error(f'An error occurred while fetching materials: {e}\n')
        return []


def download_classroom_materials(classroom_service, drive_service, download_path, course_index=None):
    """
    Downloads materials from Google Classroom for one or more courses, organizing them by topics.

    Args:
        classroom_service (Resource): The Classroom API service instance.
        drive_service (Resource): The Google Drive API service instance.
        download_path (str): The local directory path where materials will be downloaded.
        course_index (Union[int, str, None]): The index of the course(s) to download. If 'all', downloads all courses.
                                              If None, prompts user for input.

    Returns:
        None
    """

    courses = list_courses(classroom_service)

    if not courses:
        logging.info('No courses found.')
        return

    def download_single_course(the_course_name, the_course_id):
        try:
            course_folder = os.path.join(download_path, the_course_name)
            os.makedirs(course_folder, exist_ok=True)

            topics_response = classroom_service.courses().topics().list(courseId=the_course_id).execute()
            topics = topics_response.get('topic', [])
            topic_dict = {topic['topicId']: topic['name'] for topic in topics}

            if not topics:
                logging.info('No topics found.')
            else:
                materials = get_course_materials(classroom_service, the_course_id)
                if not materials:
                    logging.info('No materials found.')
                else:
                    materials.reverse()
                    summary_dict = {
                        'total_folders': 0,
                        'total_files': 0,
                        'failed_downloads': [],
                    }
                    total_downloaded_topics = []

                    for material in materials:
                        topic_id = material.get('topicId')
                        topic_name = topic_dict.get(topic_id, 'No Topic')
                        topic_folder = os.path.join(course_folder, topic_name)
                        os.makedirs(topic_folder, exist_ok=True)

                        logging.info(f"Downloading materials for topic: {topic_name}")
                        if topic_id not in total_downloaded_topics:
                            total_downloaded_topics.append(topic_id)

                        if 'materials' in material:
                            for mat in material['materials']:
                                if 'driveFile' in mat:
                                    drive_file_id = mat['driveFile']['driveFile']['id']
                                    recursive_dict = download_recursive(drive_service, drive_file_id, topic_folder)
                                    for i in summary_dict:
                                        summary_dict[i] += recursive_dict[i]
                                else:
                                    logging.warning(f"No drive file found in material: {mat}\n")
                                    summary_dict['failed_downloads'].append((str(mat), 'No drive file found'))

                        elif 'description' in material:
                            description = material.get('description')
                            drive_file_id = extract_file_id_from_input(description)
                            if drive_file_id:
                                recursive_dict = download_recursive(drive_service, drive_file_id, topic_folder)
                                for i in summary_dict:
                                    summary_dict[i] += recursive_dict[i]

                            else:
                                logging.warning(f"Could not extract file ID from description: {description}\n")
                                summary_dict['failed_downloads'].append((description, 'Could not extract file ID'))

                        elif material.get('title') is not None:
                            mat_title = material.get('title')
                            drive_file_id = extract_file_id_from_input(mat_title)
                            if drive_file_id:
                                recursive_dict = download_recursive(drive_service, drive_file_id, topic_folder)
                                for i in summary_dict:
                                    summary_dict[i] += recursive_dict[i]
                            else:
                                logging.warning(f"Could not extract file ID from material: {mat_title}\n")
                                summary_dict['failed_downloads'].append((mat_title, 'Could not extract file ID'))

                        else:
                            logging.warning(f"No materials or description or Drive file found: {material}\n")
                            summary_dict['failed_downloads'].append((str(material), "No materials or description or "
                                                                                    "Drive file found"))

                    logging.info(f"Download Summary: {the_course_name}")
                    logging.info(f"Total downloaded topics: {len(total_downloaded_topics)}")
                    logging.info(f"Total downloaded folders: {summary_dict['total_folders']}")
                    logging.info(f"Total downloaded files: {summary_dict['total_files']}")
                    logging.info(f"Total failed downloads: {len(summary_dict['failed_downloads'])}\n")
                    if summary_dict['failed_downloads']:
                        logging.error("Failed Downloads Details:")
                        for fail in summary_dict['failed_downloads']:
                            logging.error(f"File: {fail[0]}, Reason: {fail[1]}\n")

        except Exception as e:
            logging.error(f'An error occurred: {e}\n')

    def download_all_courses():
        for i in courses:
            name_of_course = i['name']
            id_of_course = i['id']
            logging.info(f"Course Name: {name_of_course}\n")
            download_single_course(name_of_course, id_of_course)

    if course_index is None:
        print("\nChoose the course to download:")
        print("0: All Courses")
        for idx, course in enumerate(courses, start=1):
            print(f"{idx}: {course['name']}")

        choice = input("\nEnter a number or comma-separated numbers corresponding to the course: ")
        try:
            choice = [int(i) for i in choice.split(',')]
            for index in choice:
                if index == 0:
                    download_all_courses()
                    break
                else:
                    chosen_course = courses[index - 1]
                    course_name = chosen_course['name']
                    course_id = chosen_course['id']
                    logging.info(f"Course Name: {course_name}\n")
                    download_single_course(course_name, course_id)
        except TypeError:
            print(f"Invalid input: Please provide comma-separated integers.\n")
        except IndexError:
            print(f"Invalid input: Please choose the numbers from the above course list.\n")

    elif course_index == 'all':
        download_all_courses()

    else:
        try:
            course_index = [int(i) for i in course_index.split(',')]
            for index in course_index:
                chosen_course = courses[index-1]
                course_name = chosen_course['name']
                course_id = chosen_course['id']
                logging.info(f"Course Name: {course_name}\n")
                download_single_course(course_name, course_id)
        except TypeError:
            logging.error(f"Invalid input: Please provide an integer or comma-separated integers.\n")
            return
        except IndexError:
            print(f"Invalid input: Please provide the comma-separated numbers within the range of course list.\n")
            return


def seconds_to_hms(seconds_to_convert):
    """
    Converts seconds into hours, minutes, and seconds.

    Args:
        seconds_to_convert (int or float): The number of seconds.

    Returns:
        tuple: (hours, minutes, seconds).

    If an error occurs, logs the error and returns (0, 0, 0).

    """
    try:
        total_hours = int(seconds_to_convert // 3600)
        total_minutes = int((seconds_to_convert % 3600) // 60)
        total_seconds = seconds_to_convert % 60
    except Exception as error:
        logging.error(f"An error occurs when converting {seconds_to_convert} to hms: {error}\n")
        return 0, 0, 0
    return total_hours, total_minutes, total_seconds


def main():
    """
    Main function to execute the Google Classroom and Drive download script.

    Parses command-line arguments for course and drive folder selection,
    initializes services, and handles user interaction for downloading materials.

    Supports:
    - Downloading all or specific courses from Google Classroom.
    - Downloading specific files/folders from Google Drive using URLs or IDs.
    - Interactive mode for user-driven source selection.

    Logs errors and progress throughout execution.
    """
    try:
        parser = argparse.ArgumentParser(description="Google Classroom and Drive Downloader")
        parser.add_argument('-c', '--course-index', type=str, help="all(to download all courses) | 1,4,"
                                                                   "5(comma-separated integers within the range of "
                                                                   "course list.)")

        parser.add_argument('-d', '--drive-folder-id', type=str, help='Google Drive file/folder URL or ID (Provide '
                                                                      'comma-separated links or IDs for multiple '
                                                                      'download')
        args = parser.parse_args()

        creds = get_credentials()
        classroom_service = build('classroom', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        if args.course_index is not None:
            logging.info("Downloading from Google Classroom")
            download_classroom_materials(classroom_service, drive_service, DOWNLOAD_PATH, args.course_index)

        elif args.drive_folder_id:
            try:
                drive_id_list = args.drive_folder_id.split(',')
                for i in drive_id_list:
                    drive_file_id = extract_file_id_from_input(i.strip())
                    if not drive_file_id:
                        logging.error(f"Invalid URL or ID in {i.strip()}.\n")
                        continue
                    logging.info("Downloading from Google Drive")
                    download_google_drive_files(drive_service, drive_file_id, DOWNLOAD_PATH)
            except Exception as e:
                logging.error(f"An error occur: {e}\n")

        else:
            running = True
            while running:
                print("Choose the download source or exit:")
                print("1: Google Classroom")
                print("2: Google Drive")
                print("3: Exit")
                try:
                    choice = int(input("Enter your choice (1 or 2 or 3): "))
                    if choice == 1:
                        download_classroom_materials(classroom_service, drive_service, DOWNLOAD_PATH)
                        time.sleep(3)

                    elif choice == 2:
                        drive_input = input("Enter the Google Drive file/folder URL or ID (Provide comma-separated "
                                            "links or IDs for multiple download: ")
                        try:
                            drive_id_list = drive_input.split(',')
                            for i in drive_id_list:
                                drive_file_id = extract_file_id_from_input(i.strip())
                                if not drive_file_id:
                                    print(f"Invalid URL or ID in {i.strip()}.\n")
                                    continue
                                logging.info("Downloading from Google Drive")
                                download_google_drive_files(drive_service, drive_file_id, DOWNLOAD_PATH)
                                time.sleep(3)
                        except Exception as e:
                            logging.error(f"An error occur: {e}\n")

                    elif choice == 3:
                        running = False

                    else:
                        print("Invalid choice. Please enter 1 or 2 or 3.")

                except ValueError:
                    print("Invalid input. Please enter a number.")

    except Exception as e:
        logging.error(f'An error occurred: {e}\n')


if __name__ == '__main__':
    start_time = time.time()
    try:
        main()
    except Exception as e:
        logging.error(f'An unexpected error occurred: {e}\n')
    end_time = time.time()
    elapsed_time = end_time - start_time
    hours, minutes, seconds = seconds_to_hms(elapsed_time)
    logging.info(f"Total execution time: {hours} hours, {minutes} minutes, {seconds:.2f} seconds\n")
