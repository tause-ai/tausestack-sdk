// Test final de autenticación con diferentes enfoques
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://vjoxmprmcbkmhwmbniaz.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqb3htcHJtY2JrbWh3bWJuaWF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE1NzM4NzQsImV4cCI6MjA2NzE0OTg3NH0.bY4FrlKtDK2TnMt7hOC5_KpIuoHwqJLOYkB-bWs_Wd8';

const supabase = createClient(supabaseUrl, supabaseKey);

async function testAuth() {
  console.log('🔐 Test completo de autenticación\n');

  const credentials = [
    { email: 'felipe@tause.co', password: 'test123456' },
    { email: 'felipe@tause.co', password: 'test123' },
    { email: 'felipe@tause.co', password: '123456' },
    { email: 'felipe@tause.co', password: 'password' }
  ];

  for (const cred of credentials) {
    console.log(`🔑 Probando: ${cred.email} / ${cred.password}`);
    
    const { data, error } = await supabase.auth.signInWithPassword(cred);
    
    if (error) {
      console.log(`   ❌ Error: ${error.message}`);
    } else {
      console.log(`   ✅ ¡Login exitoso!`);
      console.log(`   👤 Usuario: ${data.user.email}`);
      console.log(`   🆔 ID: ${data.user.id}`);
      console.log(`   ✅ Confirmado: ${data.user.email_confirmed_at ? 'Sí' : 'No'}`);
      return; // Salir si encuentra credenciales válidas
    }
  }

  console.log('\n🚨 Ninguna combinación funcionó.');
  console.log('\n💡 Soluciones:');
  console.log('1. Ve a Supabase > Authentication > Users');
  console.log('2. Busca felipe@tause.co');
  console.log('3. Haz clic en el usuario');
  console.log('4. Confirma el email (si no está confirmado)');
  console.log('5. Cambia la contraseña a "test123456"');
  console.log('6. Guarda los cambios');

  // Intentar registrar nuevo usuario con email diferente
  console.log('\n🆕 Intentando crear usuario alternativo...');
  const { data: newUser, error: newError } = await supabase.auth.signUp({
    email: 'admin@tausestack.dev',
    password: 'admin123456',
    options: {
      data: {
        name: 'Admin TauseStack'
      }
    }
  });

  if (newError) {
    console.log(`❌ Error creando usuario alternativo: ${newError.message}`);
  } else {
    console.log(`✅ Usuario alternativo creado: admin@tausestack.dev`);
    console.log(`📧 Revisa si necesita confirmación de email`);
    
    // Intentar login inmediato
    console.log('\n🔐 Probando login con usuario alternativo...');
    const { data: loginData, error: loginError } = await supabase.auth.signInWithPassword({
      email: 'admin@tausestack.dev',
      password: 'admin123456'
    });

    if (loginError) {
      console.log(`❌ Login alternativo falló: ${loginError.message}`);
    } else {
      console.log(`✅ ¡Login alternativo exitoso!`);
      console.log(`\n🎉 Usa estas credenciales:`);
      console.log(`   Email: admin@tausestack.dev`);
      console.log(`   Password: admin123456`);
    }
  }
}

testAuth(); 