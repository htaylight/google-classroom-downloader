
---

# Google Classroom and Google Drive Downloader

This script allows you to download and organize materials from Google Classroom and Google Drive directly to your local machine. It provides both an interactive mode and command-line options for ease of use.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Google Cloud Console Setup](#google-cloud-console-setup)
4. [Running the Script](#running-the-script)
5. [Changing Account](#changing-account)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.8 or higher
- Google account with access to Google Classroom and Google Drive

## Installation

### Python Installation

1. **Download Python:**
   - Go to the [Python download page](https://www.python.org/downloads/).
   - Download the latest version of Python for your operating system.

2. **Install Python:**
   - Run the installer and follow the on-screen instructions.
   - Make sure to check the box that says "Add Python to PATH" during installation.

### Cloning the Repository

1. **Clone the repository:**

   Clone this repository or download the zip file and extract it. Navigate to the project directory.

   ```sh
   git clone https://github.com/htaylight/google-classroom-downloader.git
   cd google-classroom-downloader
   ```

2. **Install the required Python packages:**

   ```sh
   pip install -r requirements.txt
   ```

   ![Install Python packages](Screenshots/26.png)

## Google Cloud Console Setup

### 1. Create a Project

- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- If this is your first time using the `Google Cloud Console`, select your `Country`, accept the `Terms of Service`, and click `AGREE AND CONTINUE`.  
  ![Welcome Page](Screenshots/1.png)
- Click on `Select a project` and then `New Project`.  
  ![Select a Project](Screenshots/2.png)
  ![New Project](Screenshots/3.png)
- Enter a project name, select `No organization` for location, and click `Create`.
  ![Create Project](Screenshots/4.png)

### 2. Enable APIs

- Select your project.
  ![Select a Project](Screenshots/5.png)
  ![Select Project](Screenshots/6.png)
- Go to the API & Services Dashboard.
  ![API & Services](Screenshots/7.png)
  ![Enable APIs](Screenshots/8.png)
- Search and enable the following APIs:
  - Google Classroom API
  - Google Drive API  
  ![Enable APIs Step1](Screenshots/9.png)
  ![Enable APIs Step2](Screenshots/10.png)
  ![Enable APIs Step3](Screenshots/11.png)
  ![Enable APIs Step4](Screenshots/12.png)
  ![Enable APIs Step5](Screenshots/13.png)

### 3. Create OAuth 2.0 Credentials

- Go to `OAuth consent screen`, select `External` as the `User Type`, and click `CREATE`. Follow the steps shown in the images below.
  ![OAuth consent screen Step1](Screenshots/14.png)
  ![OAuth consent screen Step2](Screenshots/15.png)
  ![OAuth consent screen Step3](Screenshots/16.png)
  ![OAuth consent screen Step4](Screenshots/17.png)
  ![OAuth consent screen Step5](Screenshots/18.png)
  ![OAuth consent screen Step6](Screenshots/19.png)
  ![OAuth consent screen Step7](Screenshots/20.png)
  ![OAuth consent screen Step8](Screenshots/21.png)

- Once published, go to `Credentials`, click `CREATE CREDENTIALS`, and select `OAuth Client ID` from the dropdown list.
  ![Create Credentials Step1](Screenshots/22.png)
- Choose `Desktop app` as the application type and click `Create`.
  ![Create Credentials Step2](Screenshots/23.png)
- Download the `json` file.
  ![Create Credentials Step3](Screenshots/24.png)

### 4. Save the Credentials File

- Rename the downloaded JSON file to `credentials.json` and place it in the project directory `google-classroom-downloader`.

## Running the Script

### Option 1: Interactive Mode

1. **Navigate to the project directory:**

   ```sh
   cd google-classroom-downloader
   ```

   (or) Type `cmd` in the address bar of the folder and press ENTER.
   ![cmd on address ](Screenshots/25.png)

2. **Run the script:**

   ```sh
   python3 download.py
   ```

   ![Running](Screenshots/27.png)

3. **Follow the on-screen prompts:**

   - The script will guide you through selecting the source (Google Classroom or Google Drive).
   - It will open a browser window for authentication if needed.
     ![Authentication1](Screenshots/28.png)
     ![Authentication2](Screenshots/29.png)
     ![Authentication3](Screenshots/30.png)
     ![Authentication4](Screenshots/31.png)
     ![Authentication5](Screenshots/32.png)
   - Choose the course or enter the Google Drive link/ID when prompted. You can enter comma-separated course numbers or drive links for multiple downloads.
     ![Choose the Course](Screenshots/34.png)
   
   - The script will download the materials and save them in the `Downloads` folder.


### Option 2: Command-Line Mode

**Use Command-Line Arguments:**

   - **Download All Courses from Google Classroom:**

     ```sh
     python3 download.py -c all
     ```

   - **Download Specific Courses by Index:**

     ```sh
     python3 download.py -c 1,3,5
     ```

   - **Download Specific Files/Folders from Google Drive:**

     ```sh
     python3 download.py -d "https://drive.google.com/drive/folders/your-folder-id"
     ```

   - **Download Multiple Files/Folders from Google Drive(add comma-separated-links):**

     ```sh
     python3 download.py -d "https://drive.google.com/drive/folders/your-folder-id,https://drive.google.com/drive/folders/your-folder-id"
     ```

## Changing Account

- To use the script with a different Google account, simply delete the `token.pickle` file and run the script again. When a browser window opens, authenticate with the desired Google account.

## Troubleshooting

- **Authentication Issues:**
  - If you encounter issues during authentication, delete the `token.pickle` file and try again.
  - Ensure your `credentials.json` file is correctly placed in the specified directory.

- **File Download Issues:**
  - Ensure you have a stable internet connection.
  - Check for any permission issues in the download directory.

---
