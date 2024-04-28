import customtkinter as tk
import subprocess
import threading
import requests
import zipfile
import stat
import time
import sys
import os
import os



tk.set_appearance_mode("System")
tk.set_default_color_theme("blue")  # ["blue", "green", "dark-blue", "sweetkind"]

script_dir = os.getcwd()
createdFilesFolder = "LocalAIChat"
gitFiles = os.path.join(script_dir, createdFilesFolder, "src")
conda_env_path = os.path.join(script_dir, createdFilesFolder, "env")
file_path = os.path.join(script_dir, createdFilesFolder, "ready.txt")


CTkLabel_List = []
cancel = False
ready = False
errorList = []
LlamaCPPVersion = "0.2.62"
bat_thread = None

app = tk.CTk()
app.geometry("900x500")
app.title("Install AI-Chatbot")
app.title("Ai-Chatbot")




class colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'



# https://github.com/oobabooga/text-generation-webui/blob/main/start_windows.bat
def createCondaBat():

    bat_content = r'''

@echo off

cd /D "%~dp0"

set PATH=%PATH%;%SystemRoot%\system32

echo "%CD%"| findstr /C:" " >nul && echo This script relies on Miniconda which can not be silently installed under a path with spaces. && goto end

@rem Check for special characters in installation path
set "SPCHARMESSAGE="WARNING: Special characters were detected in the installation path!" "         This can cause the installation to fail!""
echo "%CD%"| findstr /R /C:"[!#\$%&()\*+,;<=>?@\[\]\^`{|}~]" >nul && (
	call :PrintBigMessage %SPCHARMESSAGE%
)
set SPCHARMESSAGE=

@rem fix failed install when installing to a separate drive
set TMP=%cd%
set TEMP=%cd%

@rem deactivate existing conda envs as needed to avoid conflicts
(call conda deactivate && call conda deactivate && call conda deactivate) 2>nul

@rem config
set INSTALL_DIR=%cd%
set CONDA_ROOT_PREFIX=%cd%\conda
set INSTALL_ENV_DIR=%cd%\env
set MINICONDA_DOWNLOAD_URL=https://repo.anaconda.com/miniconda/Miniconda3-py310_23.3.1-0-Windows-x86_64.exe
set conda_exists=F

@rem figure out whether git and conda needs to be installed
call "%CONDA_ROOT_PREFIX%\_conda.exe" --version >nul 2>&1
if "%ERRORLEVEL%" EQU "0" set conda_exists=T

@rem (if necessary) install git and conda into a contained environment
@rem download conda
if "%conda_exists%" == "F" (
	echo Downloading Miniconda from %MINICONDA_DOWNLOAD_URL% to %INSTALL_DIR%\miniconda_installer.exe

	mkdir "%INSTALL_DIR%"
	call curl -Lk "%MINICONDA_DOWNLOAD_URL%" > "%INSTALL_DIR%\miniconda_installer.exe" || ( echo. && echo Miniconda failed to download. && goto end )

	echo Installing Miniconda to %CONDA_ROOT_PREFIX%
	start /wait "" "%INSTALL_DIR%\miniconda_installer.exe" /InstallationType=JustMe /NoShortcuts=1 /AddToPath=0 /RegisterPython=0 /NoRegistry=1 /S /D=%CONDA_ROOT_PREFIX%

	@rem test the conda binary
	echo Miniconda version:
	call "%CONDA_ROOT_PREFIX%\_conda.exe" --version || ( echo. && echo Miniconda not found. && goto end )

    @rem delete the Miniconda installer
    del "%INSTALL_DIR%\miniconda_installer.exe"
)

@rem create the installer env
if not exist "%INSTALL_ENV_DIR%" (
	echo Packages to install: %PACKAGES_TO_INSTALL%
	call "%CONDA_ROOT_PREFIX%\_conda.exe" create --no-shortcuts -y -k --prefix "%INSTALL_ENV_DIR%" python=3.12 || ( echo. && echo Conda environment creation failed. && goto end )
)

@rem check if conda environment was actually created
if not exist "%INSTALL_ENV_DIR%\python.exe" ( echo. && echo Conda environment is empty. && goto end )

@rem environment isolation
set PYTHONNOUSERSITE=1
set PYTHONPATH=
set PYTHONHOME=
set "CUDA_PATH=%INSTALL_ENV_DIR%"
set "CUDA_HOME=%CUDA_PATH%"

@rem activate installer env
call "%CONDA_ROOT_PREFIX%\condabin\conda.bat" activate "%INSTALL_ENV_DIR%" || ( echo. && echo Miniconda hook not found. && goto end )

@rem setup installer env
@rem call python one_click.py %*

@rem below are functions for the script   next line skips these during normal execution
goto end

:PrintBigMessage
echo. && echo.
echo *******************************************************************
for %%M in (%*) do echo * %%~M
echo *******************************************************************
echo. && echo.
exit /b

:end
pause
'''

    bat_file_path = os.path.join(createdFilesFolder, "installConda.bat")

    if not os.path.exists(bat_file_path):
        with open(bat_file_path, 'w') as bat_file:
            bat_file.write(bat_content)
        setTaskText(text=f"The file '{bat_file_path}' was successfully created.")  
    else:
        pass




# Dont used
def addToScrollbar(text, text_color = "#FFFFFF", bgcolor="#2b2b2b", alignment="w", wraplength= 450, fontAndsize=('Arial', 11)):
    elm = tk.CTkLabel(scroll_frame, text=text, bg_color=bgcolor, anchor=alignment, wraplength = wraplength, text_color=text_color, font=fontAndsize)
    CTkLabel_List.append(elm)
    elm.pack(anchor="w", padx=20)




def setTaskText(text, text_color = "#FFFFFF", bgcolor="#2b2b2b", alignment="w", add = True, fontAndsize=('Arial', 11), success = False, error = False, info = False):
    if success:
        task.configure(text=text, text_color="green", bg_color=bgcolor, anchor=alignment, font=('Arial', 13))
    elif error:
        task.configure(text=text, text_color="#ff4200", bg_color=bgcolor, anchor=alignment, font=('Arial', 13))
    elif info:
        task.configure(text=text, text_color="#C0C0FF", bg_color=bgcolor, anchor=alignment, font=('Arial', 13))
    else:
        task.configure(text=text, text_color=text_color, bg_color = bgcolor, anchor=alignment, font=fontAndsize)
    if add:
        addToScrollbar(text, text_color, bgcolor, alignment="w", fontAndsize=fontAndsize)




def showSuccess(text, color="#2b2b2b", bgcolor="green", alignment="w", fontAndsize=('Arial', 13), add = True):
    setTaskText(text, text_color = bgcolor, bgcolor=color, alignment=alignment, fontAndsize=fontAndsize, add = add)


def showError(text, color="#2b2b2b", bgcolor="#ff4200", alignment="w", fontAndsize=('Arial', 13), add = True):
    setTaskText(text, text_color = bgcolor, bgcolor=color, alignment=alignment, fontAndsize=fontAndsize, add = add)


def showinfo(text, color="#2b2b2b", bgcolor="#C0C0FF", alignment="w", fontAndsize=('Arial', 13), add = True):
    setTaskText(text, text_color = bgcolor, bgcolor=color, alignment=alignment, fontAndsize=fontAndsize, add = add)




def deleteElements():
    for label in CTkLabel_List:
        label.destroy()




def remove_non_utf8(text):
    return ''.join(char for char in text if char.encode('utf-8', 'ignore'))


def remove_by_percent(text):
    index = text.find('%')
    if index != -1:
        return text[:index+1]
    else:
        return text
    


def streamInstallOutput(lineText, taskText):
    if cancel:
        return
    
    line = lineText.strip()
    if line:
        line = remove_non_utf8(line.strip())
        progressbar.step()
        text = remove_by_percent(line)
        setTaskText(f"{taskText}\n{text}")
        print(text) 



# https://github.com/oobabooga/text-generation-webui/blob/main/one_click.py
def run_cmd(cmd, environment=False, task ="Status: ", stream=False):

    i = 0
    stdin = subprocess.DEVNULL

    if environment:
        conda_bat_path = os.path.join(script_dir, createdFilesFolder, "conda", "condabin", "conda.bat")
        cmd = f'"{conda_bat_path}" activate "{conda_env_path}">nul && {cmd}'

    if stream:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="latin1", stdin=stdin)
    else: 
        process = subprocess.run(cmd, shell=True, stdin=stdin)

    if stream:
        for line in process.stdout:
            streamInstallOutput(line, task)

        for line in process.stderr:
            streamInstallOutput(line, task)
            errorList.append(str(line))
    
        process.wait()


    if process.returncode is not None:
        if process.returncode == 0:
            print(colors.GREEN + 'No Error' + colors.RESET)

        else:
            result = " ".join(errorList)
            print("Error: ", result)
            print(colors.RED + f'Error:  {result}' + colors.RESET)
            cancel_process(text=f"ERROR: {result}")
    else:
        print(colors.RED + f'Process ERROR' + colors.RESET)







def downloadGit(github_url):

    try:

        script_dir = os.getcwd()
        createdFilesFolder = "LocalAIChat"
        gitFiles = os.path.join(script_dir, createdFilesFolder)

        zip_file_path = os.path.join(gitFiles, 'ai-chatbot.zip')

        extracted_folder = os.path.join(gitFiles)

        if not os.path.exists(gitFiles):
            os.makedirs(gitFiles)

        response = requests.get(github_url)
        if response.status_code == 200:
            with open(zip_file_path, 'wb') as f:
                f.write(response.content)
            showSuccess(text=f"LocalAIChat Succesful downloded!")
        
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(extracted_folder)
                showSuccess(text=f"ZIP file successfully unpacked.")
            
            os.rename(os.path.join(extracted_folder, 'ai-chatbot-main'), os.path.join(extracted_folder, 'src'))
            os.remove(zip_file_path)
        else:
            cancel_process(text=f"ERROR: Failed to download files")
            global cancel
            cancel = True
    except Exception as e:
        cancel_process(text=f"ERROR: {e}")








def startCondaBatch():

    batch_file_path = "installConda.bat"
    dir = os.path.join(script_dir, createdFilesFolder)

    global cancel
    if not cancel:
        setTaskText(text=f"Download conda and configure...")
        run_cmd(f"cd {dir} && {batch_file_path}", environment=False,  stream=True, task="Install Conda: ")
        if not cancel:
            showSuccess(text=f"Conda installation complete!")
        time.sleep(1)






def installRequerements():

    global cancel
    if not cancel:
        setTaskText(text=f"Download and Install all Requerement Modules")
        run_cmd(f"cd {gitFiles} && pip install -r requirements.txt", environment=True, stream=True, task="Install requerements: ")
        if not cancel:
            showSuccess(text=f"Requerements Succesful installed!")
        time.sleep(1)





def installCudaRuntime():

    global cancel
    if not cancel:
        setTaskText(text=f"Download cuda-runtime 12.1.1 ...")
        cmd = 'conda install -y -c "nvidia/label/cuda-12.1.1" cuda-runtime'
        run_cmd(cmd, environment=True, stream=True, task="install Cuda-runtime: ")
        if not cancel:
            showSuccess(text=f"Cuda-Runtime installed!")
        time.sleep(1)




def installTorch():
    global cancel
    if not cancel:
        setTaskText(text=f"Download Torch with cu121 ...")
        #cmd = 'pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121'
        cmd = 'conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia'

        run_cmd(cmd, environment=True, stream=True, task="Install torch")
        if not cancel:
            showSuccess(text=f"Torch with cu121 installed!")
        time.sleep(1)




def install_llamCPP():
    
    global cancel
    if not cancel:
        llamacpp = f"pip install llama-cpp-python=={LlamaCPPVersion} --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 --no-cache"
        #cmd = f"set CMAKE_ARGS=-DLLAMA_CUBLAS=on && set FORCE_CMAKE=1 && {llamacpp}"
        cmd = f"{llamacpp}"

        setTaskText(text=f"Download and Install LlamCPP")
        run_cmd(cmd, environment=True, stream=True, task="Install LlamaCPP: ")

        if not cancel:
            setTaskText("Llamacpp Installed!")
        time.sleep(1)








def startInstallation():

    global cancel
    downloadGit(github_url = 'https://github.com/Snens98/ai-chatbot/archive/main.zip')
    startCondaBatch()
    installRequerements() 
    installTorch()
    installCudaRuntime()
    install_llamCPP()

    if not cancel:
        setGUIStartApp()
        if not cancel:
            setReady()
            pass
    else:
        pass






def setGUIStartApp():

    if len(errorList) != 0:

        title_.configure(text=f"Installing complete. But with warnings. ")
        print(colors.GREEN + f'\n\nInstalling complete. But with warnings. ' + colors.RESET)


        result = " ".join(errorList)
        print(colors.YELLOW + f'Warnings: ", {result}' + colors.RESET)

        info_.configure(text=f"{result}", font=("Arial", 9))

    else:
        title_.configure(text="Installation complete!")

    info_.configure(text="All requerements downloaded and installed.")

    progressbar.pack_forget()
    showSuccess("You can now start the APP!", fontAndsize=('Calibri', 20))

    # Disable installation-Button / Enable Start-Button
    SuccessInstallation_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20, padx=50) 
    installation_frame.pack_forget()





# After successful installation, the application is ready for use
def setReady():

    ready = True
    with open(file_path, "w") as file:
        file.write(str(ready))
    





def isAlreadyInstalled(): 
    try:
        installer_dir = os.path.join(script_dir, createdFilesFolder)
        if not os.path.exists(installer_dir):
            os.makedirs(installer_dir)

        with open(file_path, "r") as file:
            content = file.read().strip()
            return content.lower() == "true"
        
    except FileNotFoundError:
        with open(file_path, "w") as file:
            file.write("False")
        return False
    except FileExistsError:
        pass







def cancel_process(text="Install process canceld"):
    showError("Install process canceld")

    close = False

    global cancel
    if cancel:
        close = True
    
    cancel = True

    if cancel and close:

        bat_thread

        sys.exit(0)    

    showError(text)
    progressbar.pack_forget()
    close_BTN.configure(text="Close", fg_color ="grey")




  






# All Text in the GUI
frame = tk.CTkFrame(app, 500, 40)
frame.pack(pady=0, fill="x")

title = tk.CTkLabel(frame, text="Local AI-Chatbot", font=("Arial", 22))
title.pack(padx=25, side="top", anchor="w", pady=(30, 0))


info = tk.CTkLabel(frame, text="This application only works under Windows and is optimized for RTX Nvidea graphics cards.", font=("Arial", 12),  wraplength=350, anchor="w", justify="left")
info.pack(side="top", anchor="w", padx=(25, 50), pady=(10, 40))


version = tk.CTkLabel(frame, text=f"Version: 0.8  |  Llama-cpp-python {LlamaCPPVersion}", font=("Arial", 10), height=10)
version.pack(padx=25, pady=(5, 2), side="top", anchor="w")

git_text = tk.CTkLabel(frame, text=r"", font=("Arial", 10), text_color="#9cdcf1", cursor="hand2", height=10)
git_text.pack(padx=25, pady=(2, 20), side="top", anchor="w")







frame_ = tk.CTkFrame(app, 500, 40)

title_ = tk.CTkLabel(frame_, text="Installing Local-AI-Chatbot ... ", font=("Arial", 22))
title_.pack(padx=25, side="top", anchor="w", pady=(30, 0))

info_ = tk.CTkLabel(frame_, text="All dependencies are now downloaded and installed.\nThis may take a few minutes.", font=("Arial", 12),  wraplength=350, anchor="w", justify="left")
info_.pack(side="top", anchor="w", padx=(25, 50), pady=(10, 15))






# If Install-Button pressed, inszallation starts in another thread
def startInstall():

    global bat_thread
    frame_.pack(pady=0, fill="x")

    if  isAlreadyInstalled(): 
        setGUIStartApp()
    else:
        initScreen()
        install_BTN.configure(fg_color ="grey", corner_radius=5, text_color="white")
        bat_thread = threading.Thread(target=startInstallation)
        bat_thread.daemon = True
        bat_thread.start()










# Prozssbar
progressbar = tk.CTkProgressBar(master=app, determinate_speed=0.5, indeterminate_speed=0.75)
progressbar.pack_forget()
progressbar.set(0)






# Task test
task = tk.CTkLabel(app, text=f"", bg_color="#2b2b2b", width = 700, anchor="w", padx=40, pady=40, wraplength=800, justify="left")
task.pack_forget()






def createStartBat():
    bat_content = r'''
    @echo off

    cd /D "%~dp0"

    set PATH=%PATH%;%SystemRoot%\system32

    set SPCHARMESSAGE=

    set TMP=%cd%
    set TEMP=%cd%

    @rem config
    set SRC_DIR=%cd%\src
    set INSTALL_ENV_DIR=%cd%\env


    cd %SRC_DIR%
    call conda activate %INSTALL_ENV_DIR%
    call streamlit run main.py
    '''

    bat_file_path = os.path.join(createdFilesFolder, "start.bat")

    if not os.path.exists(bat_file_path):
        with open(bat_file_path, 'w') as bat_file:
            bat_file.write(bat_content)
        setTaskText(text=f"Die Datei '{bat_file_path}' wurde erfolgreich erstellt.")  
    else:
        pass




def startAPPWithExternalConsole():

    conda_bat_path = os.path.join(script_dir, createdFilesFolder, "conda", "condabin", "conda.bat")
    setTaskText(text=f"Start APP...")    
    batch_file_path = os.path.join(script_dir, createdFilesFolder, "start.bat")
    print(f'\n\nRun:\n"start cmd /k "{conda_bat_path} activate {conda_env_path}"\nand\n"{batch_file_path}"\nto start App')
    os.system(f'start cmd /k "{conda_bat_path} activate {conda_env_path} && {batch_file_path}' )
    sys.exit()






scroll_frame = tk.CTkScrollableFrame(app, label_fg_color="transparent", height=100)
scroll_frame.pack_forget()
scroll_frame._scrollbar.configure(height=0)


tk.CTkLabel(scroll_frame, text="Install ...", wraplength = 800).pack(anchor="w", padx=20)




def startThread():
        
    bat_thread = threading.Thread(target=reinstallBTN)
    bat_thread.start()



def reinstallBTN():
    try:

        filesDir = os.path.join(script_dir, createdFilesFolder)
        gitFiles = os.path.join(script_dir, createdFilesFolder, "src")

        print(f"Try to delete {filesDir}")
              
        if os.path.exists(filesDir):

            #os.chmod(gitFiles, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR) # Enable permission to delete these files
            os.chmod(filesDir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR) # Enable permission to delete these files
            #git.rmtree(filesDir) # Delete
        
        sys.exit(0)    

    except Exception as e:
        showError(text= f"Delete was not successful. Try it manually.")






# Buttons
SuccessInstallation_frame = tk.CTkFrame(app, fg_color="transparent")
SuccessInstallation_frame.pack_forget()

start_BTN = tk.CTkButton(SuccessInstallation_frame, text="Start App", width=350,height=35, command=startAPPWithExternalConsole)
reinstall = tk.CTkButton(SuccessInstallation_frame, text="Reinstall", width=50, fg_color="grey", command=startThread)
update = tk.CTkButton(SuccessInstallation_frame, text="Update", width=50, fg_color="grey", command=downloadGit)

# downloadGit
# installRequerements
start_BTN.pack(side=tk.LEFT, fill=tk.X, padx=(10, 50), expand=True)
reinstall.pack(side=tk.RIGHT, fill=tk.X, padx=2, expand=True)
update.pack(side=tk.RIGHT, fill=tk.X, padx=2, expand=True)






installation_frame = tk.CTkFrame(app, fg_color="transparent")
installation_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20) 

install_BTN = tk.CTkButton(installation_frame, text="Install", command=startInstall, width=300)
install_BTN.pack(side=tk.LEFT, padx=(30, 20))

close_BTN = tk.CTkButton(installation_frame, text="cancel", command=cancel_process)
close_BTN.pack(side=tk.RIGHT, padx=30)






if isAlreadyInstalled():    # to check whether the app has already been installed (successfully or unsuccessfully)
    setGUIStartApp()
    version.configure(text="The app is ready to use 👍", font=("Arial", 20), text_color="green")
    version.pack(padx=25, pady=(5, 20), side="top", anchor="w")

    git_text.pack_forget()
    installation_frame.pack_forget()
    pass




# Create start Screen of non installed App
def initScreen():

    task.pack(padx=0, pady=20, fill= tk.BOTH)
    progressbar.pack(padx=20, pady=10, fill= tk.BOTH)

    frame.pack_forget()
    install_BTN._state = tk.DISABLED
    install_BTN.configure(fg_color ="grey")




createCondaBat()
createStartBat()



app.mainloop()
