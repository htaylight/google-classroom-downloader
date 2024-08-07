import os
import pickle
import re
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly',
    'https://www.googleapis.com/auth/classroom.topics.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]


def get_credentials():
    creds = None
    token_path = 'token.pickle'
    creds_path = 'credentials.json'

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    return creds


def list_courses(classroom_service):
    results = classroom_service.courses().list(pageSize=10).execute()
    courses = results.get('courses', [])
    return courses


def get_course_materials(service, course_id):
    try:
        materials_response = service.courses().courseWorkMaterials().list(courseId=course_id).execute()
        materials = materials_response.get('courseWorkMaterial', [])
        return materials
    except Exception as e:
        print(f'An error occurred while fetching materials: {e}')
        return []


def download_file(drive_service, file_id, file_path, failed_downloads):
    if os.path.exists(file_path):
        print(f"File {file_path} already exists. Skipping download.\n")
        return True
    try:
        request = drive_service.files().get_media(fileId=file_id)
        with open(file_path, 'wb') as file:
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Downloaded {int(status.progress() * 100)}%.")
        print(f'File downloaded to {file_path}\n')
        return True
    except Exception as e:
        print(f'An error occurred while downloading the file: {e}\n')
        failed_downloads.append((file_path, str(e)))
        return False


def main():
    creds = get_credentials()
    classroom_service = build('classroom', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

    courses = list_courses(classroom_service)

    if not courses:
        print('No courses found.')
        return

    print("Choose the course to download:")
    for idx, course in enumerate(courses, start=1):
        print(f"{idx}: {course['name']}")

    while True:
        try:
            choice = int(input("Enter the number of the course to download: "))
            if 1 <= choice <= len(courses):
                break
            else:
                print("Invalid choice. Please enter a number corresponding to the course.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    chosen_course = courses[choice - 1]
    course_name = chosen_course['name']
    course_id = chosen_course['id']
    print(f"Course ID found: {course_id}")

    try:
        course_folder = os.path.join(download_path, course_name)
        os.makedirs(course_folder, exist_ok=True)

        topics_response = classroom_service.courses().topics().list(courseId=course_id).execute()
        topics = topics_response.get('topic', [])
        topic_dict = {topic['topicId']: topic['name'] for topic in topics}

        if not topics:
            print('No topics found.')
        else:
            print('Downloading materials:')
            materials = get_course_materials(classroom_service, course_id)
            if not materials:
                print('No materials found.')
            else:
                materials.reverse()

                total_downloaded_topics = []
                total_downloaded_files = 0
                failed_downloads = []

                for material in materials:
                    topic_id = material.get('topicId')
                    topic_name = topic_dict.get(topic_id, 'No Topic')
                    topic_folder = os.path.join(course_folder, topic_name)
                    os.makedirs(topic_folder, exist_ok=True)

                    print(f"Downloading materials for topic: {topic_name}")
                    if topic_id not in total_downloaded_topics:
                        total_downloaded_topics.append(topic_id)

                    if 'materials' in material:
                        for mat in material['materials']:
                            if 'driveFile' in mat:
                                drive_file = mat['driveFile']['driveFile']
                                file_name = drive_file.get('title')
                                file_id = drive_file.get('id')
                                print(f"Found file: {file_name}")
                                if file_name and file_id:
                                    file_path = os.path.join(topic_folder, file_name)
                                    if download_file(drive_service, file_id, file_path, failed_downloads):
                                        total_downloaded_files += 1
                                else:
                                    print(f"Missing file name or ID for material: {mat}")
                                    failed_downloads.append((file_name, 'Missing file name or ID'))
                            else:
                                print(f"No drive file found in material: {mat}")
                                failed_downloads.append((str(mat), 'No drive file found'))
                    elif 'description' in material:
                        description = material.get('description')
                        file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', description)
                        if file_id_match:
                            file_id = file_id_match.group(1)
                            drive_file = drive_service.files().get(fileId=file_id).execute()
                            file_name = drive_file.get('name')
                            print(f"Found file: {file_name}")
                            if file_name and file_id:
                                file_path = os.path.join(topic_folder, file_name)
                                if download_file(drive_service, file_id, file_path, failed_downloads):
                                    total_downloaded_files += 1
                            else:
                                print(f"Could not extract file ID from description: {description}")
                                failed_downloads.append((description, 'Could not extract file ID'))
                        else:
                            print(f"Could not extract file ID from description: {description}")
                            failed_downloads.append((description, 'Could not extract file ID'))
                    else:
                        print(f"No materials or description found in material: {material}")
                        failed_downloads.append((str(material), 'No materials or description found'))

                print("\nDownload Summary:")
                print(f"Total downloaded topics: {len(total_downloaded_topics)}")
                print(f"Total downloaded files: {total_downloaded_files}")
                print(f"Total failed downloads: {len(failed_downloads)}")
                if failed_downloads:
                    print("\nFailed Downloads Details:")
                    for fail in failed_downloads:
                        print(f"File: {fail[0]}, Reason: {fail[1]}")

    except Exception as e:
        print(f'An error occurred: {e}')


if __name__ == '__main__':
    main()
