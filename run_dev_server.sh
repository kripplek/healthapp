#!/bin/bash

gunicorn 'server:get_app()'  -b 0 --reload --workers 4
