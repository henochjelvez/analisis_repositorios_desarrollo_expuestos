import requests
import re
import time
import os
from datetime import datetime

# Configuración de las APIs
GITHUB_TOKEN = "xxxxxxxxxxx"
BITBUCKET_USERNAME = "xxxxxxxxxx"
BITBUCKET_APP_PASSWORD = "xxxxxxxxxxxxxxxxxx"
GOOGLE_API_KEY = "xxxxxxxxxxxxxxxxxxxx"
GOOGLE_CX = "xxxxxxxxxxxxxx"
GITLAB_TOKEN = "glpat-xxxxxxxxxxxxxxxxxx"

headers_github = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

headers_gitlab = {
    "Authorization": f"Bearer {GITLAB_TOKEN}"
}

# Palabras clave para analizar información sensible
PALABRAS_CLAVE = [
    "password", "apikey", "secret", "token", "private_key",
    "jwt_secret", "client_secret", "username", "credit_card",
    "sql", "database", "confidential", "rut", "tarjeta"
]

# Función para analizar contenido sensible
def analizar_contenido(contenido, archivo_url):
    lineas_encontradas = []
    for i, linea in enumerate(contenido.splitlines(), 1):
        for palabra in PALABRAS_CLAVE:
            if re.search(rf"\b{palabra}\b", linea, re.IGNORECASE):
                lineas_encontradas.append((i, palabra, linea.strip(), archivo_url))
    return lineas_encontradas

# Buscar información sensible en archivos de GitHub
def buscar_info_sensible_en_archivo(archivo_url):
    try:
        response = requests.get(archivo_url)
        if response.status_code == 200:
            contenido = response.text
            return analizar_contenido(contenido, archivo_url)
    except Exception as e:
        print(f"Error al analizar archivo: {e}")
    return []

# Buscar repositorios en GitHub
def buscar_repositorios_github(empresa):
    print(f"Buscando repositorios públicos en GitHub para '{empresa}'...")
    repositorios = []
    url = f"https://api.github.com/search/repositories?q={empresa}+in:name"
    while url:
        response = requests.get(url, headers=headers_github)
        if response.status_code == 200:
            data = response.json()
            repositorios.extend(data['items'])
            url = response.links.get('next', {}).get('url')
            time.sleep(1)
        else:
            print(f"Error al obtener repositorios de GitHub: {response.status_code}")
            break
    return repositorios

# Buscar repositorios en Bitbucket
def buscar_repositorios_bitbucket(empresa, workspace):
    print(f"Buscando repositorios públicos en Bitbucket para '{empresa}' en workspace '{workspace}'...")
    repositorios = []
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}"
    while url:
        response = requests.get(url, auth=(BITBUCKET_USERNAME, BITBUCKET_APP_PASSWORD))
        if response.status_code == 200:
            data = response.json()
            for repo in data.get('values', []):
                if empresa.lower() in repo['name'].lower():
                    repositorios.append(repo)
            url = data.get('next')
            time.sleep(1)
        else:
            print(f"Error al obtener repositorios de Bitbucket: {response.status_code} - {response.text}")
            break
    return repositorios

# Buscar repositorios en GitLab
def buscar_repositorios_gitlab(empresa):
    print(f"Buscando repositorios públicos en GitLab para '{empresa}'...")
    repositorios = []
    url = f"https://gitlab.com/api/v4/projects?search={empresa}"
    while url:
        response = requests.get(url, headers=headers_gitlab)
        if response.status_code == 200:
            data = response.json()
            repositorios.extend(data)
            url = response.links.get('next', {}).get('url')
            time.sleep(1)
        else:
            print(f"Error al obtener repositorios de GitLab: {response.status_code}")
            break
    return repositorios

# Buscar con Google Custom Search Engine
def buscar_con_google_cse(empresa):
    print(f"Buscando resultados con Google Custom Search Engine para '{empresa}'...")
    resultados = []
    url = f"https://www.googleapis.com/customsearch/v1?q={empresa}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for item in data.get("items", []):
            resultados.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            })
    else:
        print(f"Error al buscar en Google CSE: {response.status_code}")
    return resultados

# Buscar menciones en Pastebin con Google
def buscar_en_pastebin_con_google(empresa):
    print(f"Buscando menciones en Pastebin para '{empresa}'...")
    resultados = []
    query = f"site:pastebin.com {empresa}"
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for item in data.get("items", []):
            resultados.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            })
    else:
        print(f"Error al buscar en Pastebin: {response.status_code}")
    return resultados

# Generar el nombre del archivo de reporte
def generar_nombre_reporte(empresa):
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"reporte_{empresa.replace(' ', '_')}_{fecha}.txt"
    return os.path.join(os.getcwd(), nombre_archivo)

# Generar el informe detallado
def generar_informe(empresa, repositorios_github, repositorios_bitbucket, repositorios_gitlab, resultados_google, resultados_pastebin):
    reporte_path = generar_nombre_reporte(empresa)
    with open(reporte_path, "w") as file:
        file.write(f"--- Informe de Resultados para '{empresa}' ---\n\n")

        # GitHub
        file.write("--- Repositorios en GitHub ---\n")
        for repo in repositorios_github:
            file.write(f"- {repo['full_name']}: {repo['html_url']}\n")
            detalles_sensibles = buscar_info_sensible_en_archivo(repo['html_url'])
            if detalles_sensibles:
                for linea in detalles_sensibles:
                    file.write(f"  [!] Línea {linea[0]}: {linea[1]} -> {linea[2]} (Archivo: {linea[3]})\n")

        # Bitbucket
        file.write("\n--- Repositorios en Bitbucket ---\n")
        for repo in repositorios_bitbucket:
            file.write(f"- {repo['name']}: {repo['links']['html']['href']}\n")

        # GitLab
        file.write("\n--- Repositorios en GitLab ---\n")
        for repo in repositorios_gitlab:
            file.write(f"- {repo['path_with_namespace']}: {repo['web_url']}\n")

        # Google CSE
        file.write("\n--- Resultados de Google Custom Search Engine ---\n")
        for resultado in resultados_google:
            file.write(f"- {resultado['title']}: {resultado['link']}\n")
            file.write(f"  {resultado['snippet']}\n")

        # Pastebin
        file.write("\n--- Resultados en Pastebin ---\n")
        for resultado in resultados_pastebin:
            file.write(f"- {resultado['title']}: {resultado['link']}\n")
            file.write(f"  {resultado['snippet']}\n")

        file.write("\n--- Fin del Informe ---\n")

    print(f"[+] Informe guardado en: {reporte_path}")

# Ejecutar el script
if __name__ == "__main__":
    empresa = input("Ingresa el nombre de la empresa: ")
    bitbucket_workspace = input("Ingresa el workspace de Bitbucket: ")

    repositorios_github = buscar_repositorios_github(empresa)
    repositorios_bitbucket = buscar_repositorios_bitbucket(empresa, bitbucket_workspace)
    repositorios_gitlab = buscar_repositorios_gitlab(empresa)
    resultados_google = buscar_con_google_cse(empresa)
    resultados_pastebin = buscar_en_pastebin_con_google(empresa)
    generar_informe(empresa, repositorios_github, repositorios_bitbucket, repositorios_gitlab, resultados_google, resultados_pastebin)
