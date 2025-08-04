#!/usr/bin/env python3
"""
Script para verificar que la configuración de tause.pro esté funcionando correctamente

Este script verifica:
1. Resolución DNS de los dominios
2. Certificados SSL configurados
3. Conectividad HTTPS
4. Respuesta del servidor TauseStack
"""

import boto3
import requests
import socket
import ssl
import sys
from urllib.parse import urlparse
from botocore.exceptions import ClientError

def check_dns_resolution(domain):
    """Verificar que el dominio resuelva correctamente"""
    try:
        ip = socket.gethostbyname(domain)
        print(f"✅ DNS {domain} → {ip}")
        return True, ip
    except socket.gaierror as e:
        print(f"❌ DNS {domain} → Error: {e}")
        return False, None

def check_ssl_certificate(domain):
    """Verificar certificado SSL"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                print(f"✅ SSL {domain} → Válido hasta {cert['notAfter']}")
                return True, cert
    except Exception as e:
        print(f"❌ SSL {domain} → Error: {e}")
        return False, None

def check_https_response(url):
    """Verificar respuesta HTTPS"""
    try:
        response = requests.get(url, timeout=10, allow_redirects=False)
        print(f"✅ HTTPS {url} → {response.status_code}")
        return True, response.status_code
    except requests.RequestException as e:
        print(f"❌ HTTPS {url} → Error: {e}")
        return False, None

def check_load_balancer_certificates():
    """Verificar certificados en Load Balancer"""
    try:
        client = boto3.client('elbv2', region_name='us-east-1')
        
        # Obtener listeners
        response = client.describe_listeners(
            LoadBalancerArn='arn:aws:elasticloadbalancing:us-east-1:349622182214:loadbalancer/app/tausestack-final-fixed-alb/c0102867a94eeb90'
        )
        
        https_listener = None
        for listener in response['Listeners']:
            if listener['Protocol'] == 'HTTPS':
                https_listener = listener
                break
        
        if https_listener:
            print("🔍 Certificados en Load Balancer:")
            for cert in https_listener['Certificates']:
                arn = cert['CertificateArn']
                if 'tause.pro' in arn or 'f190e0dd' in arn:
                    print(f"  ✅ TauseStack: {arn}")
                elif 'tause.pro' in arn or '1e8403aa' in arn:
                    print(f"  ✅ TausePro: {arn}")
                else:
                    print(f"  ❓ Desconocido: {arn}")
            return True
        else:
            print("❌ No se encontró listener HTTPS")
            return False
            
    except ClientError as e:
        print(f"❌ Error verificando Load Balancer: {e}")
        return False

def main():
    print("🔍 Verificando configuración de TausePro...")
    print("=" * 50)
    
    # Dominios a verificar
    domains = [
        'tause.pro',
        'app.tause.pro',
        'api.tause.pro',
        'www.tause.pro'
    ]
    
    urls = [
        'https://tause.pro',
        'https://app.tause.pro',
        'https://api.tause.pro',
        'https://www.tause.pro'
    ]
    
    print("\n📋 1. Verificando resolución DNS...")
    dns_results = []
    for domain in domains:
        success, ip = check_dns_resolution(domain)
        dns_results.append((domain, success, ip))
    
    print("\n🔐 2. Verificando certificados SSL...")
    ssl_results = []
    for domain in domains:
        success, cert = check_ssl_certificate(domain)
        ssl_results.append((domain, success, cert))
    
    print("\n🌐 3. Verificando respuestas HTTPS...")
    https_results = []
    for url in urls:
        success, status = check_https_response(url)
        https_results.append((url, success, status))
    
    print("\n⚙️ 4. Verificando configuración Load Balancer...")
    lb_success = check_load_balancer_certificates()
    
    print("\n📊 RESUMEN:")
    print("=" * 50)
    
    # Resumen DNS
    dns_ok = all(result[1] for result in dns_results)
    print(f"DNS: {'✅ Todos OK' if dns_ok else '❌ Algunos fallan'}")
    
    # Resumen SSL
    ssl_ok = all(result[1] for result in ssl_results)
    print(f"SSL: {'✅ Todos OK' if ssl_ok else '❌ Algunos fallan'}")
    
    # Resumen HTTPS
    https_ok = all(result[1] for result in https_results)
    print(f"HTTPS: {'✅ Todos OK' if https_ok else '❌ Algunos fallan'}")
    
    # Resumen Load Balancer
    print(f"Load Balancer: {'✅ Certificados OK' if lb_success else '❌ Revisar configuración'}")
    
    # Estado general
    all_ok = dns_ok and ssl_ok and https_ok and lb_success
    print(f"\n🎯 ESTADO GENERAL: {'✅ TODO FUNCIONANDO' if all_ok else '❌ REVISAR CONFIGURACIÓN'}")
    
    if not all_ok:
        print("\n🔧 PRÓXIMOS PASOS:")
        if not dns_ok:
            print("   • Verificar registros DNS en Route 53")
        if not ssl_ok:
            print("   • Revisar certificados en ACM")
        if not https_ok:
            print("   • Verificar conectividad y configuración del servidor")
        if not lb_success:
            print("   • Configurar certificados en Load Balancer (usar manual_certificate_setup.md)")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 