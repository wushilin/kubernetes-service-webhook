#!/bin/sh


kubectl create secret tls webhook-tls --cert=./certs/tls.crt --key=./certs/tls.key 
