
---

# Google Classroom Course Materials Downloader

This script downloads and organizes course materials from Google Classroom, saving them to your local machine by topic.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Google Cloud Console Setup](#google-cloud-console-setup)
4. [Running the Script](#running-the-script)
5. [Changing Account](#changing-account)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.6 or higher
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
- If it is the very first time at `Google Cloud Console`, choose `Country` and tick at `Terms of Service`> `AGREE AND CONTINUE`  
  ![Welcome Page](Screenshots/1.png)
- Click on `Select a project` and click `New Project`.  
  ![Select a Project](Screenshots/2.png)
  ![New Project](Screenshots/3.png)
- Enter a project name, choose `No organization` for location and click `Create`.
  ![Create Project](Screenshots/4.png)
### 2. Enable APIs
- Select your project.
  ![Select a Project](Screenshots/5.png)
  ![Select Project](Screenshots/6.png)
- Go to the API & Services Dashboard.
  ![API & Services](Screenshots/7.png) 
  ![Enable APIs](Screenshots/8.png)
- Search and Enable the following APIs:
  - Google Classroom API
  - Google Drive API  
  ![Enable APIs Step1](Screenshots/9.png)
  ![Enable APIs Step2](Screenshots/10.png)
  ![Enable APIs Step3](Screenshots/11.png)
  ![Enable APIs Step4](Screenshots/12.png)
  ![Enable APIs Step5](Screenshots/13.png)

### 3. Create OAuth 2.0 Credentials
- Go to `OAuth consent screen` and select `External` as `User Type` then click `CREATE` button. 
  And follow the steps as shown in the pictures below.
  ![OAuth consent screen Step1](Screenshots/14.png)
  ![OAuth consent screen Step2](Screenshots/15.png)
  ![OAuth consent screen Step3](Screenshots/16.png)
  ![OAuth consent screen Step4](Screenshots/17.png)
  ![OAuth consent screen Step5](Screenshots/18.png)
  ![OAuth consent screen Step6](Screenshots/19.png)
  ![OAuth consent screen Step7](Screenshots/20.png)
  ![OAuth consent screen Step8](Screenshots/21.png)
- After published, go to `Credentials` and click `CREATE CREDENTIALS`, from drop down list select `OAuth Client ID`. 
  ![Create Credentials Step1](Screenshots/22.png)
- Select `Desktop app` as the application type and click `Create`.
  ![Create Credentials Step2](Screenshots/23.png)
- Download the `json` file.
  ![Create Credentials Step3](Screenshots/24.png)

### 4. Save the Credentials File
- Rename the downloaded json file to `credentials.json` and place the file in the project directory `google-classroom-downloader`.

## Running the Script

1. **Navigate to the project directory:**

   ```sh
   cd google-classroom-downloader
   ```
   
   (or)Type `cmd` in the address bar of folder and hit ENTER
   ![cmd on address ](Screenshots/25.png)

2. **Run the script:**

   ```sh
   python3 download.py
   ```
   ![Running](Screenshots/27.png)

3. **Follow the prompts:**
   - The script will open a browser window for authentication. And follow the steps as shown in pictures below.
     ![Authentication1](Screenshots/28.png)
     ![Authentication2](Screenshots/29.png)
     ![Authentication3](Screenshots/30.png)
     ![Authentication4](Screenshots/31.png)
     ![Authentication5](Screenshots/32.png)


   - Choose the course you want to download by entering the corresponding number.
     ![Choose the Course](Screenshots/34.png)

   - The script will download the materials and save them in the `Downloads` folder.

## Changing Account

- If you want to use the script for other Google account, you do not need to set up Google Cloud Console again, just delete `token.pickle` file and run the script, when a browser opens, authenticate with your desired Google account as shown in the above steps.

## Troubleshooting

- **Authentication Issues:**
  - If you encounter issues during authentication, delete the `token.pickle` file and try again.
  - Make sure your `credentials.json` file is correctly placed in the specified directory.

- **File Download Issues:**
  - Ensure you have a stable internet connection.
  - Check for any permission issues on the download directory.

---
