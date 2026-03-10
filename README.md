# 🏥 ReportLens: Medical Intelligence Hub

ReportLens is an automated clinical dashboard designed to extract, process, and securely store patient lab results from PDF reports using OCR and AI.

This guide provides the exact steps to install and run ReportLens locally on a Windows machine.

---

## ⚙️ Step 1: Install External Windows Software
Because this app processes PDFs and images, you must install two external system tools on the Windows laptop before running any Python code.

### A. Install Tesseract OCR
1. Download the official Windows installer: [Tesseract Installer (64-bit)](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer and leave the default installation path exactly as: `C:\Program Files\Tesseract-OCR`
*(Note: The Python code is hardcoded to look for Tesseract at this specific location).*

### B. Install Poppler (Required for PDF-to-Image)
1. Download the latest Poppler for Windows zip file from here: [Poppler Windows Releases](https://github.com/oschwartz10612/poppler-windows/releases/)
2. Extract the downloaded `.zip` folder.
3. Move the extracted folder to `C:\Program Files\` and rename it simply to `poppler`.
4. **CRITICAL - Add Poppler to the Windows System PATH:**
   * Press the Windows key, type "Environment Variables", and hit Enter.
   * Click the **"Environment Variables..."** button at the bottom.
   * Under the **"System variables"** section (the bottom half), find the variable named `Path`, select it, and click **"Edit"**.
   * Click **"New"** and paste this exact path: `C:\Program Files\poppler\Library\bin`
   * Click OK on all windows to save and close.

---

## 📥 Step 2: Download & Setup Python Packages
1. Ensure **Python 3.9 or newer** is installed on the laptop. 
   * *⚠️ Crucial: During Python installation, make sure to check the box at the bottom that says **"Add Python to PATH"**.*
2. Download the ReportLens project folder to the laptop.
3. Open the Command Prompt (Terminal) inside the ReportLens folder.
4. Install all required Python packages by running this command:
   ```cmd
   pip install -r requirements.txt
   ```

---

## 🔑 Step 3: Configure the AI API Key
ReportLens requires an API key to process the medical text using AI.
1. Inside the main ReportLens folder, create a brand new text file and name it exactly `.env`
2. Open the file in Notepad and paste the following line, replacing the placeholder text with your actual API key:
   ```text
   GROQ_API_KEY=your_actual_api_key_goes_here
   ```
3. Save and close the file.

---

## 🚀 Step 4: Create the Desktop Launcher
To make this easy for the doctor to use without ever opening a terminal:
1. Locate the `Run_ReportLens.bat` file in the main folder.
2. Right-click it -> **Show more options** -> **Send to** -> **Desktop (create shortcut)**.
3. You can rename the desktop shortcut to "ReportLens Dashboard".
4. **To use the app:** The doctor simply double-clicks the desktop shortcut. The system will boot up in the background and the dashboard will automatically open in their web browser!

---
**Note on Data Storage:** *The database (`reportlens_lab.db`) and all temporary PDF storage folders will be generated automatically the very first time a report is uploaded through the dashboard.*