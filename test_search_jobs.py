from playwright.sync_api import sync_playwright, Playwright
from rich import print
import csv
import json
import re
from datetime import datetime

# Selectores CSS
date_post_job = "div.opacity-half.size0"
date_post_job_utility = "h3 + div time"
pinned_title_jobs = "strong.pr-3 i.fa.fa-thumb-tack.purple.tooltipster-basic"
href_jobs = "a.gb-results-list__item[href]"
title_jobs = "h1[class='gb-landing-cover__title size5 mb1']"
qualifications_jobs = "span[itemprop='qualifications']"
quantity_applicants = (
    "#right-col > div:nth-of-type(2) > div > div > div > div:nth-of-type(5)"
)


# urls de los trabajos
url_junior_jobs = "https://www.getonbrd.com/jobs-junior"
url_santiago_general_jobs = "https://www.getonbrd.com/jobs/city/santiago"


def run(playwright: Playwright):
    start_url = url_junior_jobs  # URL a scrapear
    chrome = playwright.chromium  # Usando Chromium
    browser = chrome.launch(headless=True)  # headless = False para ver el navegador
    page = browser.new_page()  # Crear una nueva página

    page.goto(start_url)  # Ir a la URL
    print(page.title())  # Imprimir el título de la página

    # Esperar a que se cargue la página 5 segundos
    # page.wait_for_timeout(5000)

    test = True
    # contar los jobs
    while test:
        # Esperar a que se cargue la página 5 segundos
        # page.wait_for_timeout(5000)

        job_items_date = page.query_selector_all(date_post_job)
        print(len(job_items_date))
        # acabar el loop
        if job_items_date is not None:
            test = False

    jobs_data = []  # Lista para almacenar los datos de los trabajos

    # Segundo bucle: procesar los enlaces de los jobs
    a = True
    max_tabs = len(job_items_date)  # Límite de pestañas a abrir
    max_tabs_alternative = 2
    tab_count = 0  # Contador de pestañas abiertas

    while a and tab_count < max_tabs_alternative:
        for link in page.locator(href_jobs).all():
            if tab_count >= max_tabs_alternative:
                a = False  # Salir del bucle while
                break  # Salir del bucle for

            p = browser.new_page(base_url="https://www.getonbrd.com/")
            url = link.get_attribute("href")
            if url is not None:
                p.goto(url)
                p.wait_for_timeout(1000)  # Esperar a que se cargue la página

                # Seleccionar el enlace de ubicación con href='/jobs/city/santiago'
                location_link = p.locator("a[href='/jobs/city/santiago']")

                # Verificar si el enlace existe
                if location_link.count() > 0:
                    location_text = "Santiago"  # Asignar directamente "Santiago" si el enlace existe
                    print(f"Ubicación: {location_text}")
                else:
                    print("No se encontró la ubicación de Santiago")
                    location_text = ""

                # Extraer el título, la fecha de publicación, la cantidad de postulantes y la categoría
                title = p.query_selector(title_jobs)
                title_text = title.inner_text() if title else "No se encontró el título"

                date_posted = p.query_selector(date_post_job_utility)
                date_text = (
                    date_posted.inner_text()
                    if date_posted
                    else "No se encontró la fecha"
                )

                qualifity_job = p.query_selector(qualifications_jobs)
                qualifity_job_text = (
                    qualifity_job.inner_text()
                    if qualifity_job
                    else "No se encontró la categoria"
                )

                quantity_applicants_job = p.query_selector(quantity_applicants)
                quantity_applicants_text = (
                    quantity_applicants_job.inner_text()
                    if quantity_applicants_job
                    else "No se encontró la cantidad de postulantes"
                )

                match = re.search(r"\d+", quantity_applicants_text)
                # Extraer la cantidad de postulantes
                quantity_applicants_text = (
                    int(match.group(0))
                    if match
                    else "No se encontró la cantidad de postulantes"
                )

                # Convertir la fecha a un objeto datetime y extraer el año
                try:
                    date_obj = datetime.strptime(date_text, "%B %d, %Y")  # Formato: "February 24, 2025"
                    year = date_obj.year  # Extraer el año
                except ValueError:
                    year = None  # Si no se puede convertir, ignorar

                # Filtrar solo los trabajos con categoría "Junior", menos de 50 postulantes, año 2025 y ubicación "Santiago"
                if (
                    "Junior" in qualifity_job_text
                    and quantity_applicants_text <= 100
                    and year == 2025
                    and location_text == "Santiago"
                ):
                    # Almacenar datos en un diccionario
                    job_data = {
                        "title": title_text,
                        "date_posted": date_text,
                        "url": url,
                        "category_professional": qualifity_job_text,
                        "quantity_applicants": quantity_applicants_text,
                        "country": location_text,
                    }
                    jobs_data.append(job_data)

                tab_count += 1  # Incrementar el contador de pestañas
                print(f"Pestañas abiertas: {tab_count}")

            p.close()  # Cerrar la pestaña después de procesarla

        # Preguntar hasta que responda bien, colocar 0 para salir

        #Dar al usuario elegir si quiere exportar los datos a un archivo JSON o CSV
        print("¿Deseas exportar los datos a un archivo JSON o CSV?")
        print("1. JSON")
        print("2. CSV")
        option = input("Selecciona una opción: ")
        answer_option_selected(option, jobs_data)

    # Cerrar el navegador al finalizar
    browser.close()


def import_JSON(jobs_data):
    # Importar los datos de un archivo JSON
    with open("jobs_data.json", mode="w", encoding="utf-8") as file:
        json.dump(jobs_data, file, ensure_ascii=False, indent=4)
    print("Datos exportados a 'jobs_data.json'")


def import_CSV(jobs_data):
    # Exportar los datos a un archivo CSV
    if jobs_data:
        with open("jobs_data.csv", mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["title", "url", "date_posted"])
            writer.writeheader()  # Escribir la cabecera del CSV
            writer.writerows(jobs_data)  # Escribir los datos
        print("Datos exportados a 'jobs_data.csv'")
    else:
        print("No se encontraron datos para exportar.")

def answer_option_selected(option, jobs_data):
    # Preguntar al usuario qué formato de archivo desea exportar
    while True:
        if option == "1":
            import_JSON(jobs_data)
            break
        elif option == "2":
            import_CSV(jobs_data)
            break
        elif option == "0":
            print("Saliendo...")
            break
        else:
            print("Opción inválida. Inténtalo de nuevo.")
            break


with sync_playwright() as playwright:
    run(playwright)
