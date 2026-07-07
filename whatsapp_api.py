import requests
import os
import logging

WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN')
PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
API_VERSION = 'v18.0'
BASE_URL = f'https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages'


def enviar_recordatorio(telefono, nombre_cliente, fecha, hora, servicio):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logging.warning('WhatsApp API no configurada')
        return False, 'WhatsApp no configurado (faltan WHATSAPP_TOKEN o WHATSAPP_PHONE_NUMBER_ID)'

    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json',
    }

    data = {
        'messaging_product': 'whatsapp',
        'to': telefono,
        'type': 'template',
        'template': {
            'name': 'recordatorio_turno',
            'language': {'code': 'es'},
            'components': [{
                'type': 'body',
                'parameters': [
                    {'type': 'text', 'text': nombre_cliente},
                    {'type': 'text', 'text': fecha},
                    {'type': 'text', 'text': hora},
                    {'type': 'text', 'text': servicio},
                ],
            }],
        },
    }

    try:
        r = requests.post(BASE_URL, headers=headers, json=data, timeout=15)
        result = r.json()
        if r.status_code == 200 and result.get('messages'):
            return True, 'Recordatorio enviado con éxito'
        error_msg = result.get('error', {}).get('message', 'Error desconocido')
        logging.error(f'WhatsApp API error: {error_msg}')
        return False, f'WhatsApp error: {error_msg[:150]}'
    except requests.exceptions.RequestException as e:
        logging.error(f'WhatsApp API connection error: {e}')
        return False, 'Error de conexión con WhatsApp API'
