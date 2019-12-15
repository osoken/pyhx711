# -*- coding: utf-8 -*-

import os
import time
import json
from logging.config import dictConfig


from flask import Flask, jsonify, request

from . sensor import HX711


def gen_app(config_object=None, logsetting_file=None, parameter_file=None):
    if logsetting_file is not None:
        with open(logsetting_file, 'r') as fin:
            dictConfig(json.load(fin))
    elif os.getenv('HX711SENSOR_LOGGER') is not None:
        with open(os.getenv('HX711SENSOR_LOGGER'), 'r') as fin:
            dictConfig(json.load(fin))
    app = Flask(__name__)
    app.config.from_object('hx711.config')
    if os.getenv('HX711SENSOR') is not None:
        app.config.from_envvar('HX711SENSOR')
    if config_object is not None:
        app.config.update(**config_object)

    sensor = HX711(
        dout=app.config['DOUT'],
        pd_sck=app.config['PD_SCK'],
        reference_unit=app.config['REFERENCE_UNIT'],
        gain=app.config['GAIN'],
        hook=lambda v: app.logger.info('sensor value.', extra=v)
    )
    if os.getenv('HX711SENSOR_PARAMETER') is not None:
        sensor.import_parameters(os.getenv('HX711SENSOR_PARAMETER'))
    if parameter_file is not None:
        sensor.import_parameters(parameter_file)

    sensor.start()

    @app.route('/api/weight')
    def api_weight():
        return jsonify({
            'weight': sensor.weight,
            'raw_value': sensor.raw_value,
            'timestamp': time.time()
        })

    @app.route('/api/reference-unit', methods=['GET', 'POST'])
    def api_referenceunit():
        if request.method == 'POST':
            sensor.reference_unit = request.get_json()['reference_unit']
            if os.getenv('HX711SENSOR_PARAMETER') is not None:
                sensor.export_parameters(os.getenv('HX711SENSOR_PARAMETER'))
            if parameter_file is not None:
                sensor.export_parameters(parameter_file)
        return jsonify({
            'reference_unit': sensor.reference_unit
        })

    @app.route('/api/offset', methods=['GET', 'POST'])
    def api_offset():
        if request.method == 'POST':
            sensor.offset = request.get_json()['offset']
            if os.getenv('HX711SENSOR_PARAMETER') is not None:
                sensor.export_parameters(os.getenv('HX711SENSOR_PARAMETER'))
            if parameter_file is not None:
                sensor.export_parameters(parameter_file)
        return jsonify({
            'offset': sensor.offset
        })

    return app
