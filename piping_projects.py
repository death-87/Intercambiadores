"""Proyectos privados en Drive mediante un Web App configurado por el propietario."""
import os
import requests


def settings(secrets):
    return {key:os.environ.get(key) or secrets.get(key,'') for key in ('PIPING_PROJECTS_URL','PIPING_PROJECTS_TOKEN','PIPING_PROJECTS_PASSWORD')}


def configured(config):return all(config.get(key) for key in ('PIPING_PROJECTS_URL','PIPING_PROJECTS_TOKEN','PIPING_PROJECTS_PASSWORD'))


def call(config,action,**fields):
    if not configured(config):raise ValueError('Falta configurar el guardado entre computadores.')
    if not config['PIPING_PROJECTS_URL'].startswith('https://script.google.com/macros/s/') or not config['PIPING_PROJECTS_URL'].endswith('/exec'):raise ValueError('La dirección del servicio de proyectos no es válida.')
    try:
        response=requests.post(config['PIPING_PROJECTS_URL'],json={'action':action,'token':config['PIPING_PROJECTS_TOKEN'],**fields},timeout=60)
        response.raise_for_status();result=response.json()
    except (requests.RequestException,ValueError) as error:raise ValueError('No se pudo contactar al almacenamiento. Tu proyecto sigue abierto; vuelve a intentar.') from error
    if not result.get('ok'):raise ValueError(result.get('error','No se pudo guardar el proyecto.'))
    return result
