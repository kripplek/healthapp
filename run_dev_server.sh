#!/bin/bash

gunicorn 'app:get_app()'  --reload --workers 4
