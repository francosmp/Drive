from tkinter.filedialog import askdirectory
import pickle
import os.path
from apiclient import errors
import io
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload, MediaIoBaseDownload
import urllib.error
from Autenticacion import Auth


class Drive:

    def __init__(self):

        self.service = build(
            'drive', 'v3', credentials=Auth().obtener_credenciales())

    def crear_carpeta(self, nombre, carpeta=None, id=None):

        file_metadata = None

        if id is not None:
            file_metadata = {
                'name': nombre,
                'parents': [id],
                'mimeType': 'application/vnd.google-apps.folder'
            }
        else:
            if carpeta is not None:
                busqueda = self.buscar(carpeta)
                if busqueda == 'Nulo o hay mas de uno':
                    return 'No se puede crear carpeta porque hay mas de una con el mismo nombre'
                else:
                    file_metadata = {
                        'name': nombre,
                        'parents': [busqueda],
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
            else:
                file_metadata = {
                    'name': nombre,
                    'mimeType': 'application/vnd.google-apps.folder'
                }

        file = self.service.files().create(body=file_metadata, fields='id').execute()

        return 'Carpeta Creada: %s' % file.get('id')

    def buscar(self, nombre, id=None):

        if id is not None:
            results = self.service.files().list(pageSize=10, fields="nextPageToken, files(id, name)",
                                                q="'"+id+"' in parents and trashed = false").execute()
        else:
            results = self.service.files().list(pageSize=10, fields="nextPageToken, files(id, name)",
                                                q="name = '"+nombre+"'  and trashed = false").execute()

        items = results.get('files', [])

        if not items or len(items) > 1:
            return 'Nulo o hay mas de uno'
        else:
            return items[0]['id']

    def listar(self, cantidad, nombre, id=None):

        if id is not None:
            results = self.service.files().list(pageSize=cantidad, fields="nextPageToken, files(id, name)",
                                                q="'"+id+"' in parents and trashed = false").execute()
        else:
            results = self.service.files().list(pageSize=cantidad, fields="nextPageToken, files(id, name)",
                                                q="name contains '"+nombre+"' and trashed = false").execute()

        items = results.get('files', [])

        if not items:
            return 'No se encontro nada'
        else:
            return items

    def ruta(self):

        directory_path = askdirectory()

        return directory_path

    def subir(self, carpeta, id=None):

        ruta = self.ruta()
        id_carpeta = self.buscar(carpeta)

        if id is not None:  # Sin id
            if id == id_carpeta and id_carpeta != 'Nulo o hay mas de uno':  # Misma carpeta y solo hay una
                self.pre_subida(id_carpeta, ruta)
                return 'Archivos Subidos'
            else:
                return 'No se puede subir porque hay mas de una carpeta con el mismo nombre y el id de la carpeta ingresada no coincide con el id ingresado'
        else:  # Con id
            if id_carpeta != 'Nulo o hay mas de uno':  # Solo hay una carpeta
                self.pre_subida(id_carpeta, ruta)
                return 'Archivos Subidos'
            else:
                return 'No se puede subir porque hay mas de una carpeta con el mismo nombre'

    def pre_subida(self, carpeta, ruta):

        archivos_ruta = os.listdir(ruta)
        archivos_drive = self.listar(len(archivos_ruta), 'Musica', carpeta)
        
        if archivos_drive != 'No se encontro nada':  # Encontro datos
            for i in range(0, len(archivos_drive)):
                archivos_drive[i] = archivos_drive[i]['name']

            for i in range(0, len(archivos_ruta)):
                if '.mp3' in archivos_ruta[i]:
                    if archivos_ruta[i] not in archivos_drive:
                        print('No esta en Lista: ' + archivos_ruta[i])
                        self.magia_subida(carpeta, ruta, archivos_ruta[i])
                    else:
                        print(
                            'En drive: [' + str(archivos_drive.index(archivos_ruta[i])) + '] : ' + archivos_ruta[i])
        else:  # No encontro nada, o sea, sube defrente
            for i in range(0, len(archivos_ruta)):
                if '.mp3' in archivos_ruta[i]:
                    print('Subiendo: ' + archivos_ruta[i])
                    self.magia_subida(carpeta, ruta, archivos_ruta[i])

    def magia_subida(self, carpeta, ruta, nombre):
        file_metadata = {
            'name': nombre,
            'parents': [carpeta]
        }

        media = MediaFileUpload(ruta + '\\' + nombre, mimetype='audio/mpeg')
        file = self.service.files().create(body=file_metadata,
                                           media_body=media, fields='id').execute()

    def bajar(self, carpeta, id=None):

        id_carpeta = self.buscar(carpeta)

        if id is not None:  # Sin id
            if id == id_carpeta and id_carpeta != 'Nulo o hay mas de uno':  # Misma carpeta y solo hay una
                self.pre_bajada(id_carpeta)
                return 'Archivos Subidos'
            else:
                return 'No se puede bajar porque hay mas de una carpeta con el mismo nombre y el id de la carpeta ingresada no coincide con el id ingresado'
        else:  # Con id
            if id_carpeta != 'Nulo o hay mas de uno':  # Solo hay una carpeta
                self.pre_bajada(id_carpeta)
                return 'Archivos Subidos'
            else:
                return 'No se puede bajar porque hay mas de una carpeta con el mismo nombre'

    def pre_bajada(self, carpeta):

        ruta = self.ruta()

        archivos_drive = self.listar(1000, 'Musica', carpeta)

        if archivos_drive != 'No se encontro nada':  # Encontro datos
            for i in range(0, len(archivos_drive)):
                self.magia_bajada(
                    archivos_drive[i]['id'], archivos_drive[i]['name'], ruta)

        else:  # No encontro nada, o sea, nada que bajar
            print('Nada que bajar')

    def magia_bajada(self, id, nombre, ruta):
        request = self.service.files().get_media(fileId=id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(nombre)
            print("Download %d%%." % int(status.progress() * 100))

        with io.open(ruta + '\\' + nombre, 'wb') as f:
            fh.seek(0)
            f.write(fh.read())
