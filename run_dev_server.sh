#!/bin/bash

gunicorn 'healthapp.server:get_app()'  -b 0 --reload --workers 4
