// Script automático para configurar Supabase
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://vjoxmprmcbkmhwmbniaz.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqb3htcHJtY2JrbWh3bWJuaWF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE1NzM4NzQsImV4cCI6MjA2NzE0OTg3NH0.bY4FrlKtDK2TnMt7hOC5_KpIuoHwqJLOYkB-bWs_Wd8';

// Usar service_role key para operaciones administrativas
const serviceRoleKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqb3htcHJtY2JrbWh3bWJuaWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTU3Mzg3NCwiZXhwIjoyMDY3MTQ5ODc0fQ.mJJSoZ3_T-2iVwfCcJzpxpKPFLMxJhAFkMl_8EB6T1E'; // Necesitas obtener esta key

const supabase = createClient(supabaseUrl, supabaseKey);

async function setupSupabase() {
  console.log('🚀 Configurando Supabase automáticamente...\n');

  try {
    // 1. Insertar tenant por defecto
    console.log('📝 Creando tenant por defecto...');
    const { data: tenantData, error: tenantError } = await supabase
      .from('tenants')
      .insert([
        {
          name: 'Default Tenant',
          plan: 'pro',
          status: 'active',
          config: { features: ['all'] }
        }
      ])
      .select();

    if (tenantError) {
      console.log('⚠️  El tenant ya existe o hay un error:', tenantError.message);
    } else {
      console.log('✅ Tenant creado:', tenantData);
    }

    // 2. Registrar usuario de prueba
    console.log('\n👤 Registrando usuario de prueba...');
    const { data: authData, error: authError } = await supabase.auth.signUp({
      email: 'felipe@tause.co',
      password: 'test123456',
      options: {
        data: {
          name: 'Felipe Admin'
        }
      }
    });

    if (authError) {
      if (authError.message.includes('already registered')) {
        console.log('⚠️  El usuario ya existe');
        
        // Intentar login
        console.log('\n🔐 Probando login...');
        const { data: loginData, error: loginError } = await supabase.auth.signInWithPassword({
          email: 'felipe@tause.co',
          password: 'test123456'
        });

        if (loginError) {
          console.error('❌ Error en login:', loginError.message);
          console.log('\n💡 Solución: Ve a Supabase Auth > Users y cambia la contraseña a "test123456"');
        } else {
          console.log('✅ Login exitoso:', loginData.user.email);
        }
      } else {
        console.error('❌ Error registrando usuario:', authError.message);
      }
    } else {
      console.log('✅ Usuario registrado:', authData.user.email);
    }

    // 3. Verificar configuración
    console.log('\n🔍 Verificando configuración...');
    const { data: tenantsCheck } = await supabase.from('tenants').select('*');
    const { data: usersCheck } = await supabase.from('users').select('*');

    console.log('📊 Tenants en DB:', tenantsCheck?.length || 0);
    console.log('👥 Users en DB:', usersCheck?.length || 0);

    if (tenantsCheck?.length > 0 && usersCheck?.length > 0) {
      console.log('\n🎉 ¡Configuración completada exitosamente!');
      console.log('\n📋 Credenciales para login:');
      console.log('   Email: felipe@tause.co');
      console.log('   Password: test123456');
      console.log('\n🌐 Ve a: http://localhost:8000');
    } else {
      console.log('\n⚠️  Configuración incompleta. Revisa los errores arriba.');
    }

  } catch (error) {
    console.error('❌ Error general:', error.message);
  }
}

setupSupabase(); 