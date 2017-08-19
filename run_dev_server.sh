#!/bin/bash

gunicorn 'app:get_app()'  --reload
