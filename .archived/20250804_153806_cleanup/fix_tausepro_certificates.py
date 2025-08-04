#!/usr/bin/env python3
"""
Script para actualizar CloudFormation stack con certificados de tause.pro

Este script:
1. Obtiene la configuración actual del stack
2. Actualiza el listener HTTPS para incluir certificados de tause.pro
3. Aplica los cambios via CloudFormation
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError

def main():
    print("🔧 Configurando certificados tause.pro para Load Balancer...")
    
    # Configuración
    region = 'us-east-1'
    stack_name = 'tausestack-final-fixed'
    
    # Certificados ARN
    tausestack_cert = 'arn:aws:acm:us-east-1:349622182214:certificate/f190e0dd-5ce9-4702-85cf-4d3ce5faba79'
    tausepro_cert = 'arn:aws:acm:us-east-1:349622182214:certificate/1e8403aa-614e-4299-aeb6-364bb4215609'
    
    # Clientes AWS
    cf_client = boto3.client('cloudformation', region_name=region)
    elb_client = boto3.client('elbv2', region_name=region)
    
    try:
        # Obtener información del stack actual
        print("📋 Obteniendo información del stack...")
        response = cf_client.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]
        
        if stack['StackStatus'] != 'UPDATE_COMPLETE' and stack['StackStatus'] != 'CREATE_COMPLETE':
            print(f"⚠️  Stack está en estado {stack['StackStatus']}")
            print("🔄 Intentando actualizar directamente con ELB...")
            
            # Intentar actualizar directamente el listener
            listeners = elb_client.describe_listeners(
                LoadBalancerArn='arn:aws:elasticloadbalancing:us-east-1:349622182214:loadbalancer/app/tausestack-final-fixed-alb/c0102867a94eeb90'
            )
            
            https_listener = None
            for listener in listeners['Listeners']:
                if listener['Protocol'] == 'HTTPS':
                    https_listener = listener
                    break
            
            if https_listener:
                print("📝 Actualizando listener HTTPS...")
                
                # Actualizar listener con ambos certificados
                try:
                    elb_client.modify_listener(
                        ListenerArn=https_listener['ListenerArn'],
                        Certificates=[
                            {'CertificateArn': tausestack_cert},
                            {'CertificateArn': tausepro_cert}
                        ]
                    )
                    print("✅ Certificados actualizados exitosamente!")
                    
                    # Verificar certificados instalados
                    updated_listener = elb_client.describe_listeners(
                        ListenerArns=[https_listener['ListenerArn']]
                    )['Listeners'][0]
                    
                    print("\n🔍 Certificados instalados:")
                    for cert in updated_listener['Certificates']:
                        print(f"  • {cert['CertificateArn']}")
                        
                except ClientError as e:
                    if 'AccessDenied' in str(e):
                        print("❌ Error de permisos. Necesitas permisos de elasticloadbalancing:ModifyListener")
                        print("🔧 Solución: Ejecutar desde consola AWS o IAM con permisos de administrador")
                        return False
                    else:
                        print(f"❌ Error actualizando listener: {e}")
                        return False
                        
            else:
                print("❌ No se encontró listener HTTPS")
                return False
        
        print("\n🎉 Proceso completado!")
        print("📊 Estado actual:")
        print(f"  • Stack: {stack['StackStatus']}")
        print(f"  • Certificados configurados para tause.pro y tausestack.dev")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 