import os
import getpass
import time
import logging
import keyboard
from tqdm import tqdm
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudFailedLoginException, PyiCloudException

pause = False

def setup_logging(directory_path):
    log_file_path = os.path.join(directory_path, 'download_log.log')
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file_path)
        ]
    )
    return logging.getLogger()

def setup_directories(directory_path):
    photos_path = os.path.join(directory_path, "Fotos")
    videos_path = os.path.join(directory_path, "Videos")
    if not os.path.exists(photos_path):
        os.makedirs(photos_path)
    if not os.path.exists(videos_path):
        os.makedirs(videos_path)
    return photos_path, videos_path

def toggle_pause(e):
    global pause
    pause = not pause
    if pause:
        print("Download wurde pausiert.")
    else:
        print("Download wird fortgesetzt.")

def authenticate_icloud(email, password, logger):
    api = PyiCloudService(email, password)
    if api.requires_2fa:
        logger.warning("Zweifaktor-Authentifizierung erforderlich. Ein Code wurde an deine Geräte gesendet.")
        code = input("Bitte gib den Verifizierungscode ein: ")
        result = api.validate_2fa_code(code)
        if not result:
            logger.error("Ungültiger Verifizierungscode.")
            exit(1)
    return api

def download_assets(api, photos_path, videos_path, file_type, logger):
    assets = api.photos.all
    logger.info(f"{len(assets)} Dateien gefunden.")
    
    for i, asset in enumerate(tqdm(assets, desc="Dateien werden heruntergeladen...")):
        while pause:
            time.sleep(1)
        try:
            filename, file_extension = os.path.splitext(asset.filename)

            if file_extension.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                subfolder = photos_path
                if file_type not in ['f', 'beide']:
                    continue
            else:
                subfolder = videos_path
                if file_type not in ['v', 'beide']:
                    continue

            file_path = os.path.join(subfolder, asset.filename)

            if os.path.exists(file_path):
                logger.info(f"Datei {asset.filename} existiert bereits - Überspringe Download.")
                continue

            chunk_size = 1024 * 1024
            download_url = asset.download(timeout=30)

            with open(file_path, 'wb') as f:
                for chunk in download_url.iter_content(chunk_size=chunk_size):
                    while pause:
                        time.sleep(1)
                    f.write(chunk)

            logger.info(f"Datei {i + 1} von {len(assets)} heruntergeladen und gespeichert als {file_path}")

        except Exception as e:
            logger.error(f"Ein Fehler ist beim Herunterladen der Datei {asset.filename} aufgetreten: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("ICloud-Backup-Service")
    print("Drücke \"P\" um die Anwendung zu pausieren.")
    
    email = input("Bitte gib deine iCloud E-Mail-Adresse ein: ")
    password = getpass.getpass("Bitte gib dein iCloud Passwort ein: ")
    directory_path = input("Bitte gib den Verzeichnispfad an, wo die Dateien gespeichert werden sollen: ")
    
    logger = setup_logging(directory_path)
    photos_path, videos_path = setup_directories(directory_path)
    keyboard.on_press_key("p", toggle_pause)

    try:
        api = authenticate_icloud(email, password, logger)
        file_type = input("Möchtest du Fotos oder Videos herunterladen? (f/v/beide): ").lower()
        download_assets(api, photos_path, videos_path, file_type, logger)
        
    except PyiCloudFailedLoginException:
        print("Fehler bei der Anmeldung - Überprüfe Benutzername und Passwort.")
        logger.error("Fehler bei der Anmeldung - Überprüfe Benutzername und Passwort.")
    except PyiCloudException:
        print("Ein Problem mit der iCloud-Authentifizierung ist aufgetreten.")
        logger.error("Ein Problem mit der iCloud-Authentifizierung ist aufgetreten.")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten - die Anwendung wird beendet...")
        logger.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
