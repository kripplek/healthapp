#!/bin/bash

gunicorn 'app:get_app()'  -b 0 --reload --workers 4
