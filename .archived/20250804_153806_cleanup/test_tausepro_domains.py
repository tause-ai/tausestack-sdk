#!/usr/bin/env python3
"""
Script para probar que los dominios tause.pro están funcionando correctamente
"""

import requests
import time
import sys
from urllib3.exceptions import InsecureRequestWarning

# Suprimir advertencias SSL para testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def test_domain(domain, path="/health"):
    """Probar un dominio específico"""
    url = f"https://{domain}{path}"
    
    try:
        print(f"🔍 Probando: {url}")
        response = requests.get(url, timeout=10, verify=False)
        
        if response.status_code == 200:
            print(f"✅ {domain} → OK ({response.status_code})")
            return True
        else:
            print(f"⚠️  {domain} → HTTP {response.status_code}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"❌ {domain} → SSL Error: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ {domain} → Connection Error: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ {domain} → Timeout: {e}")
        return False
    except Exception as e:
        print(f"❌ {domain} → Error: {e}")
        return False

def main():
    """Probar todos los dominios de TausePro"""
    
    print("🧪 Probando dominios TausePro...")
    print("=" * 50)
    
    domains = [
        "tause.pro",
        "app.tause.pro",
        "api.tause.pro",
        "www.tause.pro"
    ]
    
    results = {}
    
    for domain in domains:
        results[domain] = test_domain(domain)
        time.sleep(1)  # Pausa entre requests
    
    print("\n📊 Resumen de resultados:")
    print("=" * 50)
    
    working_domains = [d for d, status in results.items() if status]
    failing_domains = [d for d, status in results.items() if not status]
    
    if working_domains:
        print("✅ Dominios funcionando:")
        for domain in working_domains:
            print(f"   - {domain}")
    
    if failing_domains:
        print("\n❌ Dominios con problemas:")
        for domain in failing_domains:
            print(f"   - {domain}")
    
    print(f"\n📈 Estado: {len(working_domains)}/{len(domains)} dominios funcionando")
    
    if len(working_domains) == len(domains):
        print("\n🎉 ¡Configuración completada exitosamente!")
        return 0
    else:
        print("\n⚠️  Necesita configurar certificados SSL")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 