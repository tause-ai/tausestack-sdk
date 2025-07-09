#!/bin/bash

echo "🔧 ACTUALIZANDO TASK DEFINITION CON VARIABLES DE SUPABASE"

# Variables de Supabase
SUPABASE_JWT_SECRET="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqb3htcHJtY2JrbWh3bWJuaWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTU3Mzg3NCwiZXhwIjoyMDY3MTQ5ODc0fQ.PfU_xe38vl3wW1DQZaOp10p1HaM89Og-O0hYfJcgFBk"

# Extraer la task definition sin metadatos
jq '.taskDefinition | {
  family: .family,
  taskRoleArn: .taskRoleArn,
  executionRoleArn: .executionRoleArn,
  networkMode: .networkMode,
  requiresCompatibilities: .requiresCompatibilities,
  cpu: .cpu,
  memory: .memory,
  containerDefinitions: [
    .containerDefinitions[0] | . + {
      environment: (.environment + [
        {name: "SUPABASE_JWT_SECRET", value: "'"$SUPABASE_JWT_SECRET"'"},
        {name: "TAUSESTACK_AUTH_BACKEND", value: "supabase"}
      ])
    }
  ]
}' current-task-def.json > new-task-def.json

echo "✅ Nueva task definition creada en new-task-def.json"

# Registrar la nueva task definition
echo "🚀 Registrando nueva task definition..."
aws ecs register-task-definition --region us-east-1 --cli-input-json file://new-task-def.json

# Obtener la nueva revisión
NEW_REVISION=$(aws ecs describe-task-definition --task-definition tausestack-final-fixed-task --region us-east-1 --query 'taskDefinition.revision')

echo "📦 Nueva revisión: $NEW_REVISION"

# Actualizar el servicio para usar la nueva task definition
echo "🔄 Actualizando servicio para usar nueva task definition..."
aws ecs update-service \
  --cluster tausestack-final-fixed-cluster \
  --service tausestack-final-fixed-service \
  --task-definition tausestack-final-fixed-task:$NEW_REVISION \
  --region us-east-1

echo "✅ Servicio actualizado. Las variables de Supabase ya están configuradas."
echo ""
echo "Variables agregadas:"
echo "- SUPABASE_JWT_SECRET: (configurado)"
echo "- TAUSESTACK_AUTH_BACKEND: supabase" 