# Archivos Archivados - TauseStack SDK

Este directorio contiene scripts y archivos que fueron utilizados durante el desarrollo y deployment inicial del proyecto, pero que ya no son necesarios para el funcionamiento actual del sistema.

## Scripts Archivados

### Scripts de Deployment Obsoletos
- `deploy-mvp.sh` - Script inicial de deployment MVP
- `deploy-complete.sh` - Script de deployment completo obsoleto
- `start-production-simple.sh` - Script simplificado de producción
- `cleanup_for_aws.py` - Script de limpieza inicial
- `real_cleanup_for_aws.py` - Script de limpieza mejorado

## Por qué se archivaron

Estos scripts fueron reemplazados por:
- `scripts/deploy-production.sh` - Script de deployment optimizado y actual
- Documentación completa en `DEPLOYMENT_AWS_GUIDE.md`
- Organización mejorada de scripts en subdirectorios

## Restauración

Si necesitas restaurar algún archivo:
```bash
mv .archived/[archivo] scripts/
```

**Fecha de archivado**: 7 de Julio, 2025
**Versión del proyecto**: 1.0.0
